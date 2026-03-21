# Uncomment and configure after creating the S3 bucket and DynamoDB table.
# terraform {
#   backend "s3" {
#     bucket         = "<your-state-bucket>"
#     key            = "math-mcp/terraform.tfstate"
#     region         = "us-west-2"
#     dynamodb_table = "<your-lock-table>"
#     encrypt        = true
#   }
# }
