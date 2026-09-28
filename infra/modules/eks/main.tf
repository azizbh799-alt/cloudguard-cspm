variable "project_name" { type = string }
variable "kubernetes_version" { type = string }
variable "subnet_ids" { type = list(string) }
variable "vpc_id" { type = string }
resource "aws_eks_cluster" "main" { name = var.project_name version = var.kubernetes_version role_arn = aws_iam_role.cluster.arn vpc_config { subnet_ids = var.subnet_ids endpoint_private_access = true endpoint_public_access = true } depends_on = [aws_iam_role_policy_attachment.cluster] }
resource "aws_iam_role" "cluster" { name = "${var.project_name}-eks-cluster" assume_role_policy = jsonencode({ Version = "2012-10-17", Statement = [{ Effect = "Allow", Principal = { Service = "eks.amazonaws.com" }, Action = "sts:AssumeRole" }] }) }
resource "aws_iam_role_policy_attachment" "cluster" { role = aws_iam_role.cluster.name policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy" }
resource "aws_eks_node_group" "main" { cluster_name = aws_eks_cluster.main.name node_group_name = "${var.project_name}-nodes" node_role_arn = aws_iam_role.nodes.arn subnet_ids = var.subnet_ids instance_types = ["t3.medium"] scaling_config { desired_size = 2 min_size = 1 max_size = 4 } depends_on = [aws_iam_role_policy_attachment.nodes] }
resource "aws_iam_role" "nodes" { name = "${var.project_name}-eks-nodes" assume_role_policy = jsonencode({ Version = "2012-10-17", Statement = [{ Effect = "Allow", Principal = { Service = "ec2.amazonaws.com" }, Action = "sts:AssumeRole" }] }) }
resource "aws_iam_role_policy_attachment" "nodes" { for_each = toset(["arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy", "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly", "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"]) role = aws_iam_role.nodes.name policy_arn = each.value }
output "cluster_name" { value = aws_eks_cluster.main.name }
output "cluster_security_group_id" { value = aws_eks_cluster.main.vpc_config[0].cluster_security_group_id }
