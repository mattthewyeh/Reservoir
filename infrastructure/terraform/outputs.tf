output "application_url" {
  description = "Public HTTPS URL for Reservoir."
  value       = "https://${var.domain_name}"
}

output "api_repository_url" {
  description = "ECR repository used by the API image."
  value       = aws_ecr_repository.api.repository_url
}

output "frontend_repository_url" {
  description = "ECR repository used by the frontend image."
  value       = aws_ecr_repository.frontend.repository_url
}

output "github_deploy_role_arn" {
  description = "OIDC role ARN for the protected GitHub deployment environment."
  value       = aws_iam_role.github_deploy.arn
}

output "ecs_cluster_name" {
  value = aws_ecs_cluster.app.name
}

output "ecs_service_name" {
  value = aws_ecs_service.app.name
}

output "ecs_task_family" {
  value = aws_ecs_task_definition.app.family
}

output "database_endpoint" {
  value = aws_db_instance.database.endpoint
}
