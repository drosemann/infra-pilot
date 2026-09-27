# Production environment Terraform
terraform {
  backend "s3" {
    bucket         = "infra-passenger-terraform-state"
    key            = "environments/prod/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "infra-passenger-terraform-locks"
  }
  required_version = ">= 1.5"
}

provider "aws" {
  region = "us-east-1"
}

module "infra_passenger" {
  source = "../../"
  environment = "prod"
  region = "us-east-1"
  vpc_cidr = "10.0.0.0/16"
  db_instance_class = "db.r6g.large"
  redis_node_type = "cache.r6g.large"
  ecr_repository_names = ["infra-passenger/orchestrator-agent", "infra-passenger/management-panel", "infra-passenger/discord-service"]
}

output "vpc_id" { value = module.infra_passenger.vpc_id }
output "rds_endpoint" { value = module.infra_passenger.rds_endpoint }
output "redis_endpoint" { value = module.infra_passenger.redis_endpoint }
output "alb_dns_name" { value = module.infra_passenger.alb_dns_name }
output "ecr_repository_urls" { value = module.infra_passenger.ecr_repository_urls }
output "ecs_cluster_name" { value = module.infra_passenger.ecs_cluster_name }