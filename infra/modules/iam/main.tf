variable "project_name" { type = string }
variable "github_repository" { type = string }
data "aws_caller_identity" "current" {}
data "aws_iam_policy_document" "github_trust" { statement { actions = ["sts:AssumeRoleWithWebIdentity"] effect = "Allow" principals { type = "Federated" identifiers = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:oidc-provider/token.actions.githubusercontent.com"] } condition { test = "StringLike" variable = "token.actions.githubusercontent.com:sub" values = ["repo:${var.github_repository}:ref:refs/heads/main"] } condition { test = "StringEquals" variable = "token.actions.githubusercontent.com:aud" values = ["sts.amazonaws.com"] } } }
resource "aws_iam_role" "github_actions" { name = "${var.project_name}-github-actions" assume_role_policy = data.aws_iam_policy_document.github_trust.json }
resource "aws_iam_role_policy" "github_actions" { role = aws_iam_role.github_actions.id policy = jsonencode({ Version = "2012-10-17", Statement = [{ Effect = "Allow", Action = ["ecr:GetAuthorizationToken", "ecr:BatchCheckLayerAvailability", "ecr:PutImage", "ecr:InitiateLayerUpload", "ecr:UploadLayerPart", "ecr:CompleteLayerUpload", "eks:DescribeCluster"], Resource = "*" }] }) }
output "github_actions_role_arn" { value = aws_iam_role.github_actions.arn }
