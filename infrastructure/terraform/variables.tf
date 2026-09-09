variable "aws_region" {
  description = "AWS region for Reservoir resources."
  type        = string
  default     = "us-west-2"
}

variable "project_name" {
  description = "Short project name used in AWS resource names."
  type        = string
  default     = "reservoir"
}

variable "environment" {
  description = "Deployment environment name."
  type        = string
  default     = "production"
}

variable "domain_name" {
  description = "Fully qualified domain name served by the load balancer."
  type        = string
}

variable "hosted_zone_id" {
  description = "Route 53 hosted zone ID containing domain_name."
  type        = string
}

variable "jwt_secret_arn" {
  description = "ARN of a Secrets Manager secret containing the raw JWT signing key."
  type        = string
  sensitive   = true
}

variable "vpc_cidr" {
  description = "CIDR block for the application VPC."
  type        = string
  default     = "10.42.0.0/16"
}

variable "database_instance_class" {
  description = "RDS instance class."
  type        = string
  default     = "db.t4g.micro"
}

variable "database_allocated_storage" {
  description = "Initial PostgreSQL storage in GiB."
  type        = number
  default     = 20
}

variable "database_deletion_protection" {
  description = "Protect the production database from accidental deletion."
  type        = bool
  default     = true
}

variable "enable_alarms" {
  description = "Create operational CloudWatch alarms after the service is deployed."
  type        = bool
  default     = false
}

variable "alert_email" {
  description = "Optional email address for CloudWatch alarm notifications."
  type        = string
  default     = null
  nullable    = true
}

variable "github_repository" {
  description = "GitHub owner/repository permitted to assume the deployment role."
  type        = string
  default     = "mattthewyeh/Reservoir"
}

variable "github_environment" {
  description = "Protected GitHub environment used by the deployment workflow."
  type        = string
  default     = "production"
}

variable "create_github_oidc_provider" {
  description = "Create the account-wide GitHub OIDC provider. Disable when one already exists."
  type        = bool
  default     = true
}

variable "github_oidc_provider_arn" {
  description = "Existing GitHub OIDC provider ARN when creation is disabled."
  type        = string
  default     = null
  nullable    = true
}

variable "github_oidc_subject" {
  description = "Optional exact GitHub OIDC subject override."
  type        = string
  default     = null
  nullable    = true
}
