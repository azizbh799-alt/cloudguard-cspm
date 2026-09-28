resource "aws_ecr_repository" "backend" { name = "${var.project_name}-backend" image_scanning_configuration { scan_on_push = true } image_tag_mutability = "IMMUTABLE" }
resource "aws_ecr_repository" "frontend" { name = "${var.project_name}-frontend" image_scanning_configuration { scan_on_push = true } image_tag_mutability = "IMMUTABLE" }
