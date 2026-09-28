output "vpc_id" { value = module.networking.vpc_id }
output "backend_repository" { value = aws_ecr_repository.backend.repository_url }
output "frontend_repository" { value = aws_ecr_repository.frontend.repository_url }
output "eks_cluster_name" { value = module.eks.cluster_name }
output "database_endpoint" { value = aws_db_instance.main.address }
