variable "project"           { type = string }
variable "env"               { type = string }
variable "vpc_id"            { type = string }
variable "public_subnet_ids" { type = list(string) }
variable "certificate_arn"   { type = string }

variable "api_target_port"       { type = number; default = 8000 }
variable "web_target_port"       { type = number; default = 3000 }
variable "ai_target_port"        { type = number; default = 8001 }
variable "discovery_target_port" { type = number; default = 8002 }
