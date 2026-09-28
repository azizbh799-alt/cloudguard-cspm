variable "aws_region" { type = string default = "us-east-1" }
variable "project_name" { type = string default = "cloudguard" }
variable "environment" { type = string default = "production" }
variable "vpc_cidr" { type = string default = "10.42.0.0/16" }
variable "availability_zones" { type = list(string) default = ["us-east-1a", "us-east-1b"] }
variable "db_name" { type = string default = "cloudguard" }
variable "db_username" { type = string default = "cloudguard" }
variable "db_password" { type = string sensitive = true }
