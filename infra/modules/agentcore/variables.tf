variable "project" {
  type = string
}

variable "environment" {
  type = string
}

variable "region" {
  type = string
}

variable "ecr_image_uri" {
  description = "Full ECR image URI including tag"
  type        = string
}

variable "execution_role_arn" {
  description = "IAM role ARN for AgentCore runtime execution"
  type        = string
}

variable "project_root" {
  description = "Absolute path to the project root (for uv run)"
  type        = string
}
