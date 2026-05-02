variable "project"            { type = string }
variable "env"                { type = string }
variable "vpc_id"             { type = string }
variable "private_subnet_ids" { type = list(string) }
variable "alb_sg_id"          { type = string }

variable "aws_region"         { type = string; default = "us-east-1" }
variable "aws_account_id"     { type = string }
variable "ecr_repo_prefix"    { type = string }

variable "api_image_tag"       { type = string; default = "latest" }
variable "ai_image_tag"        { type = string; default = "latest" }
variable "discovery_image_tag" { type = string; default = "latest" }
variable "web_image_tag"       { type = string; default = "latest" }

variable "api_cpu"    { type = number; default = 512 }
variable "api_memory" { type = number; default = 1024 }
variable "web_cpu"    { type = number; default = 256 }
variable "web_memory" { type = number; default = 512 }

variable "env_secrets" {
  description = "Map of environment variable names to SSM parameter ARNs"
  type        = map(string)
  default     = {}
}

variable "api_desired_count"       { type = number; default = 2 }
variable "web_desired_count"       { type = number; default = 2 }
variable "ai_desired_count"        { type = number; default = 1 }
variable "discovery_desired_count" { type = number; default = 1 }

variable "target_group_arns" {
  type = object({
    api       = string
    web       = string
    ai        = string
    discovery = string
  })
}

variable "log_retention_days" { type = number; default = 30 }
