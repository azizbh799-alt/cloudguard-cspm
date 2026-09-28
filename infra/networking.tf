module "networking" { source = "./modules/networking" project_name = var.project_name vpc_cidr = var.vpc_cidr availability_zones = var.availability_zones }
