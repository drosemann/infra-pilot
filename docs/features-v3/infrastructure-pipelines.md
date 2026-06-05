# Feature 73: Infrastructure Pipelines

## Overview
CI/CD pipelines for infrastructure as code with lint, plan, apply workflow supporting Terraform, Pulumi, CloudFormation, and OpenTofu.

## Components
- `pipeline_engine.py` - Core pipeline execution
- `terraform_runner.py` - Terraform/OpenTofu execution
- `pulumi_runner.py` - Pulumi execution
- `pipeline_routes.py` - API endpoints
- `PipelineManager` - Manager class

## Pipeline Stages
1. **Validate** - Syntax and configuration validation
2. **Lint** - Code style and best practice checks (tflint, checkov)
3. **Plan** - Preview changes
4. **Approve** - Manual or auto-approval gate
5. **Apply** - Execute changes
6. **Verify** - Post-deployment validation

## Pipeline Configuration
```yaml
pipeline:
  name: deploy-aws-infra
  triggers:
    - branch: main
      path: terraform/*
  stages:
    - name: validate
      commands: ["terraform validate"]
    - name: lint
      commands: ["tflint", "checkov -d ."]
    - name: plan
      commands: ["terraform plan -out=tfplan"]
    - name: approve
      type: manual
      approvers: ["team-leads"]
    - name: apply
      commands: ["terraform apply tfplan"]
  notifications:
    on_success: ["discord", "email"]
    on_failure: ["discord", "pagerduty"]
```

## API Endpoints
- `GET /api/v1/pipelines` - List pipelines
- `POST /api/v1/pipelines` - Create pipeline
- `GET /api/v1/pipelines/{id}` - Get pipeline
- `PUT /api/v1/pipelines/{id}` - Update pipeline
- `DELETE /api/v1/pipelines/{id}` - Delete pipeline
- `POST /api/v1/pipelines/{id}/run` - Trigger pipeline run
- `GET /api/v1/pipelines/{id}/runs` - Run history
- `GET /api/v1/pipelines/{id}/runs/{run_id}` - Run details
- `POST /api/v1/pipelines/{id}/runs/{run_id}/cancel` - Cancel run
- `GET /api/v1/pipelines/{id}/runs/{run_id}/logs` - Run logs

## Supported IaC Tools
- Terraform (OpenTofu)
- Pulumi (TypeScript, Python, Go, .NET)
- AWS CloudFormation
- Azure Resource Manager
- Google Deployment Manager
