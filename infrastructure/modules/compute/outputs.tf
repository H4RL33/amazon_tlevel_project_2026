output "ecs_cluster_name" {
  value = aws_ecs_cluster.main.name
}

output "backend_task_definition_family" {
  value = aws_ecs_task_definition.backend.family
}
