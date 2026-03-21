output "ssm_param_name" {
  description = "SSM parameter name where the agent ARN is stored after apply"
  value       = local.ssm_param_name
}

output "agent_name" {
  value = local.agent_name
}
