variable "project"            { type = string }
variable "env"                { type = string }
variable "vpc_id"             { type = string }
variable "private_subnet_ids" { type = list(string) }
variable "allowed_sg_ids"     { type = list(string); default = [] }

variable "node_type" {
  type    = string
  default = "cache.t4g.small"
}

variable "num_cache_nodes" {
  type    = number
  default = 2
}
