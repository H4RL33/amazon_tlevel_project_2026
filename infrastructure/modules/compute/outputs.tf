output "ecs_cluster_name" {
  value = aws_ecs_cluster.main.name
}

output "backend_task_definition_family" {
  value = aws_ecs_task_definition.backend.family
}

output "ecs_cluster_arn" {
  value = aws_ecs_cluster.main.arn
}

output "backend_service_arn" {
  value = aws_ecs_service.backend.id
}

output "frontend_service_arn" {
  value = aws_ecs_service.frontend.id
}
