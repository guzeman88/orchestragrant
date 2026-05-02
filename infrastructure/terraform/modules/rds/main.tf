resource "aws_db_subnet_group" "main" {
  name       = "${var.project}-${var.env}-rds-subnet"
  subnet_ids = var.private_subnet_ids
  tags       = { Name = "${var.project}-${var.env}-rds-subnet-group" }
}

resource "aws_security_group" "rds" {
  name        = "${var.project}-${var.env}-rds-sg"
  description = "RDS PostgreSQL access"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = var.allowed_sg_ids
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.project}-${var.env}-rds-sg" }
}

resource "aws_db_parameter_group" "postgres16" {
  name   = "${var.project}-${var.env}-pg16"
  family = "postgres16"

  parameter {
    name  = "shared_preload_libraries"
    value = "pg_stat_statements,vector"
  }

  parameter {
    name  = "log_min_duration_statement"
    value = "1000"
  }

  tags = { Name = "${var.project}-${var.env}-pg16-params" }
}

resource "aws_db_instance" "main" {
  identifier        = "${var.project}-${var.env}-postgres"
  engine            = "postgres"
  engine_version    = "16.3"
  instance_class    = var.instance_class
  allocated_storage = var.allocated_storage
  storage_type      = "gp3"
  storage_encrypted = true

  db_name  = var.db_name
  username = var.db_username
  password = var.db_password

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  parameter_group_name   = aws_db_parameter_group.postgres16.name

  multi_az               = var.multi_az
  publicly_accessible    = false
  deletion_protection    = var.env == "prod"
  skip_final_snapshot    = var.env != "prod"
  final_snapshot_identifier = var.env == "prod" ? "${var.project}-${var.env}-final" : null

  backup_retention_period = var.env == "prod" ? 7 : 1
  backup_window           = "03:00-04:00"
  maintenance_window      = "sun:04:00-sun:05:00"

  performance_insights_enabled = var.env == "prod"
  monitoring_interval          = var.env == "prod" ? 60 : 0

  tags = {
    Name    = "${var.project}-${var.env}-rds"
    Project = var.project
    Env     = var.env
  }
}
