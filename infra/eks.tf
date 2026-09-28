module "eks" { source = "./modules/eks" project_name = var.project_name kubernetes_version = "1.31" subnet_ids = module.networking.private_subnet_ids vpc_id = module.networking.vpc_id }
