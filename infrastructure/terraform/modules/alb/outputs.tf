output "alb_dns_name"      { value = aws_lb.main.dns_name }
output "alb_zone_id"       { value = aws_lb.main.zone_id }
output "alb_sg_id"         { value = aws_security_group.alb.id }
output "target_group_arns" {
  value = {
    api       = aws_lb_target_group.api.arn
    web       = aws_lb_target_group.web.arn
    ai        = aws_lb_target_group.ai.arn
    discovery = aws_lb_target_group.discovery.arn
  }
}
