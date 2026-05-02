variable "project"            { type = string }
variable "env"                { type = string }
variable "vpc_id"             { type = string }
variable "private_subnet_ids" { type = list(string) }
variable "allowed_sg_ids"     { type = list(string); default = [] }

variable "instance_class" {
  type    = string
  default = "db.t4g.medium"
}

variable "allocated_storage" {
  type    = number
  default = 100
}

variable "db_name"     { type = string; default = "orchestragrant" }
variable "db_username" { type = string; default = "pgadmin" }
variable "db_password" { type = string; sensitive = true }

variable "multi_az" {
  type    = bool
  default = true
}
