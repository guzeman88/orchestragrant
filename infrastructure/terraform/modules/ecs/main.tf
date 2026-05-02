locals {
  prefix = "${var.project}-${var.env}"
  ecr    = "${var.aws_account_id}.dkr.ecr.${var.aws_region}.amazonaws.com/${var.ecr_repo_prefix}"
}

# ── IAM ───────────────────────────────────────────────────────────────────────

resource "aws_iam_role" "execution" {
  name = "${local.prefix}-ecs-execution"
  assume_role_policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "execution_basic" {
  role       = aws_iam_role.execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role" "task" {
  name = "${local.prefix}-ecs-task"
  assume_role_policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "task_s3_ses" {
  role = aws_iam_role.task.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:ListBucket"]
        Resource = ["arn:aws:s3:::${var.project}-${var.env}-documents", "arn:aws:s3:::${var.project}-${var.env}-documents/*"]
      },
      {
        Effect   = "Allow"
        Action   = ["ses:SendEmail", "ses:SendRawEmail"]
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = ["ssm:GetParameter", "ssm:GetParameters"]
        Resource = "arn:aws:ssm:${var.aws_region}:${var.aws_account_id}:parameter/${var.project}/${var.env}/*"
      }
    ]
  })
}

# ── Cluster ───────────────────────────────────────────────────────────────────

resource "aws_ecs_cluster" "main" {
  name = "${local.prefix}-cluster"
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
  tags = { Project = var.project, Env = var.env }
}

# ── Security Group (all ECS tasks) ────────────────────────────────────────────

resource "aws_security_group" "tasks" {
  name        = "${local.prefix}-ecs-tasks-sg"
  description = "ECS task inbound from ALB"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 0
    to_port         = 65535
    protocol        = "tcp"
    security_groups = [var.alb_sg_id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${local.prefix}-ecs-tasks-sg" }
}

# ── CloudWatch log groups ─────────────────────────────────────────────────────

resource "aws_cloudwatch_log_group" "api"       { name = "/ecs/${local.prefix}/api";       retention_in_days = var.log_retention_days }
resource "aws_cloudwatch_log_group" "ai"        { name = "/ecs/${local.prefix}/ai";        retention_in_days = var.log_retention_days }
resource "aws_cloudwatch_log_group" "discovery" { name = "/ecs/${local.prefix}/discovery"; retention_in_days = var.log_retention_days }
resource "aws_cloudwatch_log_group" "web"       { name = "/ecs/${local.prefix}/web";       retention_in_days = var.log_retention_days }
resource "aws_cloudwatch_log_group" "celery"    { name = "/ecs/${local.prefix}/celery";    retention_in_days = var.log_retention_days }

# ── Task definitions ──────────────────────────────────────────────────────────

resource "aws_ecs_task_definition" "api" {
  family                   = "${local.prefix}-api"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.api_cpu
  memory                   = var.api_memory
  execution_role_arn       = aws_iam_role.execution.arn
  task_role_arn            = aws_iam_role.task.arn

  container_definitions = jsonencode([{
    name      = "api"
    image     = "${local.ecr}/api:${var.api_image_tag}"
    essential = true
    portMappings = [{ containerPort = 8000, protocol = "tcp" }]
    secrets = [for k, v in var.env_secrets : { name = k, valueFrom = v }]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"  = aws_cloudwatch_log_group.api.name
        "awslogs-region" = var.aws_region
        "awslogs-stream-prefix" = "api"
      }
    }
    healthCheck = {
      command     = ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]
      interval    = 30
      timeout     = 5
      retries     = 3
      startPeriod = 60
    }
  }])
}

resource "aws_ecs_task_definition" "web" {
  family                   = "${local.prefix}-web"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.web_cpu
  memory                   = var.web_memory
  execution_role_arn       = aws_iam_role.execution.arn
  task_role_arn            = aws_iam_role.task.arn

  container_definitions = jsonencode([{
    name      = "web"
    image     = "${local.ecr}/web:${var.web_image_tag}"
    essential = true
    portMappings = [{ containerPort = 3000, protocol = "tcp" }]
    secrets = [for k, v in var.env_secrets : { name = k, valueFrom = v }]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.web.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "web"
      }
    }
    healthCheck = {
      command     = ["CMD-SHELL", "curl -f http://localhost:3000/ || exit 1"]
      interval    = 30
      timeout     = 5
      retries     = 3
      startPeriod = 60
    }
  }])
}

resource "aws_ecs_task_definition" "ai" {
  family                   = "${local.prefix}-ai"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 1024
  memory                   = 2048
  execution_role_arn       = aws_iam_role.execution.arn
  task_role_arn            = aws_iam_role.task.arn

  container_definitions = jsonencode([{
    name      = "ai"
    image     = "${local.ecr}/ai-service:${var.ai_image_tag}"
    essential = true
    portMappings = [{ containerPort = 8001, protocol = "tcp" }]
    secrets = [for k, v in var.env_secrets : { name = k, valueFrom = v }]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.ai.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "ai"
      }
    }
  }])
}

resource "aws_ecs_task_definition" "discovery" {
  family                   = "${local.prefix}-discovery"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 512
  memory                   = 1024
  execution_role_arn       = aws_iam_role.execution.arn
  task_role_arn            = aws_iam_role.task.arn

  container_definitions = jsonencode([{
    name      = "discovery"
    image     = "${local.ecr}/discovery:${var.discovery_image_tag}"
    essential = true
    portMappings = [{ containerPort = 8002, protocol = "tcp" }]
    secrets = [for k, v in var.env_secrets : { name = k, valueFrom = v }]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.discovery.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "discovery"
      }
    }
  }])
}

resource "aws_ecs_task_definition" "celery" {
  family                   = "${local.prefix}-celery"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 512
  memory                   = 1024
  execution_role_arn       = aws_iam_role.execution.arn
  task_role_arn            = aws_iam_role.task.arn

  container_definitions = jsonencode([{
    name      = "celery"
    image     = "${local.ecr}/api:${var.api_image_tag}"
    essential = true
    command   = ["celery", "-A", "celery_app", "worker", "-B", "--loglevel=info"]
    secrets   = [for k, v in var.env_secrets : { name = k, valueFrom = v }]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.celery.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "celery"
      }
    }
  }])
}

# ── Services ──────────────────────────────────────────────────────────────────

resource "aws_ecs_service" "api" {
  name            = "${local.prefix}-api"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = var.api_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [aws_security_group.tasks.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = var.target_group_arns.api
    container_name   = "api"
    container_port   = 8000
  }

  deployment_minimum_healthy_percent = 100
  deployment_maximum_percent         = 200
  wait_for_steady_state              = false

  lifecycle { ignore_changes = [task_definition] }
}

resource "aws_ecs_service" "web" {
  name            = "${local.prefix}-web"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.web.arn
  desired_count   = var.web_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [aws_security_group.tasks.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = var.target_group_arns.web
    container_name   = "web"
    container_port   = 3000
  }

  deployment_minimum_healthy_percent = 100
  deployment_maximum_percent         = 200
  wait_for_steady_state              = false

  lifecycle { ignore_changes = [task_definition] }
}

resource "aws_ecs_service" "ai" {
  name            = "${local.prefix}-ai"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.ai.arn
  desired_count   = var.ai_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [aws_security_group.tasks.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = var.target_group_arns.ai
    container_name   = "ai"
    container_port   = 8001
  }

  lifecycle { ignore_changes = [task_definition] }
}

resource "aws_ecs_service" "discovery" {
  name            = "${local.prefix}-discovery"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.discovery.arn
  desired_count   = var.discovery_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [aws_security_group.tasks.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = var.target_group_arns.discovery
    container_name   = "discovery"
    container_port   = 8002
  }

  lifecycle { ignore_changes = [task_definition] }
}

resource "aws_ecs_service" "celery" {
  name            = "${local.prefix}-celery"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.celery.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [aws_security_group.tasks.id]
    assign_public_ip = false
  }

  lifecycle { ignore_changes = [task_definition] }
}
