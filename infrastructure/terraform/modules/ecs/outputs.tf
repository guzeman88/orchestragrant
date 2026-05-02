output "cluster_id"        { value = aws_ecs_cluster.main.id }
output "cluster_name"      { value = aws_ecs_cluster.main.name }
output "task_sg_id"        { value = aws_security_group.tasks.id }
output "api_service_name"  { value = aws_ecs_service.api.name }
output "web_service_name"  { value = aws_ecs_service.web.name }
