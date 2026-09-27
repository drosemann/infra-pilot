# Dev environment Terraform
terraform {
  backend "s3" {
    bucket         = "infra-passenger-terraform-state"
    key            = "environments/dev/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "infra-passenger-terraform-locks"
  }
}

provider "aws" {
  region = "us-east-1"
}

module "infra_passenger" {
  source = "../../"
  environment = "dev"
  region = "us-east-1"
  vpc_cidr = "10.0.0.0/16"
  db_instance_class = "db.t3.small"
  redis_node_type = "cache.t3.micro"
}

output "vpc_id" { value = module.infra_passenger.vpc_id }
output "rds_endpoint" { value = module.infra_passenger.rds_endpoint }
output "redis_endpoint" { value = module.infra_passenger.redis_endpoint }
output "alb_dns_name" { value = module.infra_passenger.alb_dns_name }
output "ecr_repository_urls" { value = module.infra_passenger.ecr_repository_urls }
output "ecs_cluster_name" { value = module.infra_passenger.ecs_cluster_name }