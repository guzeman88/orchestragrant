terraform {
  required_version = ">= 1.8"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.70"
    }
  }
  backend "s3" {
    bucket         = "orchestragrant-terraform-state"
    key            = "staging/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "orchestragrant-terraform-locks"
  }
}

provider "aws" {
  region = var.aws_region
}

variable "aws_region"      { type = string; default = "us-east-1" }
variable "aws_account_id"  { type = string }
variable "db_password"     { type = string; sensitive = true }
variable "certificate_arn" { type = string }
variable "ses_domain"      { type = string; default = "staging.orchestragrant.com" }

locals {
  project = "orchestragrant"
  env     = "staging"
}

module "vpc" {
  source             = "../../modules/vpc"
  project            = local.project
  env                = local.env
  vpc_cidr           = "10.1.0.0/16"
  availability_zones = ["${var.aws_region}a", "${var.aws_region}b"]
}

module "s3" {
  source     = "../../modules/s3"
  project    = local.project
  env        = local.env
  aws_region = var.aws_region
}

module "ses" {
  source     = "../../modules/ses"
  project    = local.project
  env        = local.env
  aws_region = var.aws_region
  ses_domain = var.ses_domain
}

module "alb" {
  source            = "../../modules/alb"
  project           = local.project
  env               = local.env
  vpc_id            = module.vpc.vpc_id
  public_subnet_ids = module.vpc.public_subnet_ids
  certificate_arn   = var.certificate_arn
}

module "rds" {
  source             = "../../modules/rds"
  project            = local.project
  env                = local.env
  vpc_id             = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
  allowed_sg_ids     = [module.ecs.task_sg_id]
  instance_class     = "db.t4g.medium"
  allocated_storage  = 50
  multi_az           = false
  db_password        = var.db_password
}

module "elasticache" {
  source             = "../../modules/elasticache"
  project            = local.project
  env                = local.env
  vpc_id             = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
  allowed_sg_ids     = [module.ecs.task_sg_id]
  node_type          = "cache.t4g.small"
  num_cache_nodes    = 1
}

module "ecs" {
  source             = "../../modules/ecs"
  project            = local.project
  env                = local.env
  vpc_id             = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
  alb_sg_id          = module.alb.alb_sg_id
  aws_region         = var.aws_region
  aws_account_id     = var.aws_account_id
  ecr_repo_prefix    = local.project
  target_group_arns  = module.alb.target_group_arns

  api_desired_count       = 1
  web_desired_count       = 1
  ai_desired_count        = 1
  discovery_desired_count = 1

  env_secrets = {
    DATABASE_URL      = "arn:aws:ssm:${var.aws_region}:${var.aws_account_id}:parameter/${local.project}/${local.env}/DATABASE_URL"
    REDIS_URL         = "arn:aws:ssm:${var.aws_region}:${var.aws_account_id}:parameter/${local.project}/${local.env}/REDIS_URL"
    JWT_PRIVATE_KEY   = "arn:aws:ssm:${var.aws_region}:${var.aws_account_id}:parameter/${local.project}/${local.env}/JWT_PRIVATE_KEY"
    JWT_PUBLIC_KEY    = "arn:aws:ssm:${var.aws_region}:${var.aws_account_id}:parameter/${local.project}/${local.env}/JWT_PUBLIC_KEY"
    OPENAI_API_KEY    = "arn:aws:ssm:${var.aws_region}:${var.aws_account_id}:parameter/${local.project}/${local.env}/OPENAI_API_KEY"
    STRIPE_SECRET_KEY = "arn:aws:ssm:${var.aws_region}:${var.aws_account_id}:parameter/${local.project}/${local.env}/STRIPE_SECRET_KEY"
    AWS_ACCESS_KEY_ID     = "arn:aws:ssm:${var.aws_region}:${var.aws_account_id}:parameter/${local.project}/${local.env}/AWS_ACCESS_KEY_ID"
    AWS_SECRET_ACCESS_KEY = "arn:aws:ssm:${var.aws_region}:${var.aws_account_id}:parameter/${local.project}/${local.env}/AWS_SECRET_ACCESS_KEY"
  }
}

output "alb_dns_name"  { value = module.alb.alb_dns_name }
output "rds_endpoint"  { value = module.rds.endpoint }
