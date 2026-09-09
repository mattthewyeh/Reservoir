# Reservoir AWS Deployment

Terraform in `infrastructure/terraform` defines Reservoir's production AWS architecture. Running Terraform or the deployment workflow creates billable resources; nothing is provisioned merely by committing these files.

## Architecture

```text
Route 53 + ACM
  -> Application Load Balancer
      -> ECS Fargate task in two public subnets
          -> Nginx frontend on port 8080
          -> FastAPI on localhost:8000
              -> encrypted RDS PostgreSQL in private subnets
```

The Fargate task receives a public IP so it can pull images and secrets without a NAT gateway. Its security group accepts only port `8080` from the load balancer; neither the public internet nor the load balancer can connect directly to FastAPI. RDS has no public address and accepts PostgreSQL connections only from the task security group.

## Prerequisites

- An AWS account and a Route 53 hosted zone.
- Terraform `1.16.x`, AWS CLI v2, and Docker.
- AWS credentials authorized to create the resources in this stack.
- A long random JWT signing key stored as a plain-string AWS Secrets Manager secret.
- A secure S3 Terraform state bucket with versioning enabled.

Create the JWT secret without placing its value in Terraform state:

```bash
aws secretsmanager create-secret \
  --name reservoir/production/jwt \
  --generate-secret-string '{"PasswordLength":64,"ExcludePunctuation":true}' \
  --region us-west-2
```

## Bootstrap

From `infrastructure/terraform`:

```bash
cp backend.tf.example backend.tf
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform fmt -check
terraform validate
terraform plan
terraform apply
```

Edit both copied files before planning. `terraform.tfvars` must contain the real domain, hosted-zone ID, region, and JWT secret ARN. Both copied files are ignored by Git.

The initial ECS service intentionally has desired count zero because the immutable ECR repositories do not contain application images yet. Terraform still creates the task definition and service, allowing the first deployment workflow to upload images, run migrations, and start one service task.

If the AWS account already has the GitHub Actions OIDC provider, set `create_github_oidc_provider = false` and provide `github_oidc_provider_arn`. Confirm the `github_oidc_subject` value against the repository's current GitHub OIDC subject format before applying.

## GitHub Environment

Create a protected GitHub environment named `production`, restrict it to the `main` branch, and add these environment variables from the Terraform outputs and AWS account:

| Variable | Value |
| --- | --- |
| `AWS_ACCOUNT_ID` | Twelve-digit AWS account ID |
| `AWS_REGION` | Terraform `aws_region` value |
| `AWS_ROLE_ARN` | `terraform output -raw github_deploy_role_arn` |

No long-lived AWS access key is stored in GitHub. The manual `Deploy to AWS` workflow requests a short-lived OIDC session, builds commit-SHA-tagged images, runs `alembic upgrade head` as a one-off Fargate task, and updates the ECS service only after migration succeeds.

After the first successful deployment, set `enable_alarms = true` in the private `terraform.tfvars` and apply again. If `alert_email` is set, confirm the AWS SNS subscription email.

## Operations

- Application: the `application_url` Terraform output.
- API and frontend logs: CloudWatch log groups under `/ecs/reservoir-production/`.
- Infrastructure dashboard: CloudWatch dashboard `reservoir-production`.
- Application metrics locally: `docker compose --profile monitoring up --build -d --wait`, then open `http://localhost:9090`.
- Rollback: deploy a previous commit, whose SHA identifies its immutable ECR image pair.

## Cost and Destruction

The Application Load Balancer, Fargate task, RDS instance and storage, Route 53, Secrets Manager, ECR storage, and CloudWatch usage can all incur charges. The public-task design avoids a continuously billed NAT gateway, trading that saving for public task IPs protected by security groups.

RDS uses seven-day automated backups, storage encryption, managed master credentials, a final snapshot, and deletion protection by default. Intentional teardown requires first setting `database_deletion_protection = false`, applying that change, and then running `terraform destroy`. Review AWS Billing and remove retained snapshots, secrets, images, DNS records, and state infrastructure only when they are no longer needed.
