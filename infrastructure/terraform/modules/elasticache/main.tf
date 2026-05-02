resource "aws_elasticache_subnet_group" "main" {
  name       = "${var.project}-${var.env}-redis-subnet"
  subnet_ids = var.private_subnet_ids
}

resource "aws_security_group" "redis" {
  name        = "${var.project}-${var.env}-redis-sg"
  description = "Redis access"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = var.allowed_sg_ids
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.project}-${var.env}-redis-sg" }
}

resource "aws_elasticache_replication_group" "redis" {
  replication_group_id       = "${var.project}-${var.env}-redis"
  description                = "OrchestraGrant Redis cluster"
  node_type                  = var.node_type
  num_cache_clusters         = var.num_cache_nodes
  automatic_failover_enabled = var.num_cache_nodes > 1
  engine_version             = "7.2"
  port                       = 6379
  subnet_group_name          = aws_elasticache_subnet_group.main.name
  security_group_ids         = [aws_security_group.redis.id]
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true

  tags = {
    Name    = "${var.project}-${var.env}-redis"
    Project = var.project
    Env     = var.env
  }
}
