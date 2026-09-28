variable "project_name" { type = string }
variable "vpc_cidr" { type = string }
variable "availability_zones" { type = list(string) }
resource "aws_vpc" "main" { cidr_block = var.vpc_cidr enable_dns_hostnames = true enable_dns_support = true tags = { Name = var.project_name } }
resource "aws_subnet" "public" { count = length(var.availability_zones) vpc_id = aws_vpc.main.id cidr_block = cidrsubnet(var.vpc_cidr, 4, count.index) availability_zone = var.availability_zones[count.index] map_public_ip_on_launch = true tags = { Name = "${var.project_name}-public-${count.index}" } }
resource "aws_subnet" "private" { count = length(var.availability_zones) vpc_id = aws_vpc.main.id cidr_block = cidrsubnet(var.vpc_cidr, 4, count.index + 8) availability_zone = var.availability_zones[count.index] tags = { Name = "${var.project_name}-private-${count.index}" } }
resource "aws_internet_gateway" "main" { vpc_id = aws_vpc.main.id }
output "vpc_id" { value = aws_vpc.main.id }
output "private_subnet_ids" { value = aws_subnet.private[*].id }
output "public_subnet_ids" { value = aws_subnet.public[*].id }
