output "ecr_repository_url" {
  description = "ECR repository URL"
  value       = module.ecr.repository_url
}

output "execution_role_arn" {
  description = "AgentCore execution IAM role ARN"
  value       = module.iam.execution_role_arn
}

output "agent_name" {
  description = "AgentCore runtime name"
  value       = module.agentcore.agent_name
}

output "agent_arn_ssm_param" {
  description = "SSM parameter name storing the agent ARN. Read with: aws ssm get-parameter --name <value> --query Parameter.Value --output text"
  value       = module.agentcore.ssm_param_name
}
