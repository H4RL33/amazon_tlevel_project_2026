output "vpc_id" {
  value = aws_vpc.main.id
}

output "public_subnet_ids" {
  value = [aws_subnet.public_a.id, aws_subnet.public_b.id]
}

output "private_subnet_ids" {
  value = [aws_subnet.private_a.id, aws_subnet.private_b.id]
}

output "sg_ecs_id" {
  value = aws_security_group.ecs.id
}

output "sg_rds_id" {
  value = aws_security_group.rds.id
}

output "alb_dns_name" {
  value = aws_lb.main.dns_name
}

output "frontend_target_group_arn" {
  value = aws_lb_target_group.frontend.arn
}

output "backend_target_group_arn" {
  value = aws_lb_target_group.backend.arn
}
