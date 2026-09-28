resource "aws_cloudwatch_log_group" "app" { name = "/cloudguard/${var.environment}" retention_in_days = 30 }
resource "aws_cloudwatch_log_metric_filter" "errors" { name = "cloudguard-errors" pattern = "ERROR" log_group_name = aws_cloudwatch_log_group.app.name metric_transformation { name = "CloudGuardErrors" namespace = "CloudGuard" value = "1" } }
