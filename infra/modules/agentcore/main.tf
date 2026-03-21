locals {
  agent_name     = replace("${var.project}_${var.environment}", "-", "_")
  ssm_param_name = "/${var.project}/${var.environment}/agent_arn"
  script_path    = abspath("${path.root}/scripts/agentcore_runtime.py")
}

resource "null_resource" "runtime" {
  triggers = {
    ecr_image_uri      = var.ecr_image_uri
    execution_role_arn = var.execution_role_arn
  }

  provisioner "local-exec" {
    command = <<-EOT
      uv run python ${local.script_path} \
        --agent-name ${local.agent_name} \
        --ecr-uri ${var.ecr_image_uri} \
        --role-arn ${var.execution_role_arn} \
        --region ${var.region} \
        --ssm-param ${local.ssm_param_name}
    EOT
    working_dir = var.project_root
  }
}
