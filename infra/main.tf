locals {
  project_root = abspath("${path.root}/..")

  # Content-based image tag: rebuilds only when source files change.
  image_tag = substr(sha256(join("", [
    filesha256("${local.project_root}/Dockerfile"),
    filesha256("${local.project_root}/src/math_mcp/server.py"),
    filesha256("${local.project_root}/pyproject.toml"),
  ])), 0, 12)
}

module "iam" {
  source      = "./modules/iam"
  project     = var.project
  environment = var.environment
  region      = var.region
}

module "ecr" {
  source       = "./modules/ecr"
  project      = var.project
  environment  = var.environment
  region       = var.region
  project_root = local.project_root
  image_tag    = local.image_tag
}

module "agentcore" {
  source             = "./modules/agentcore"
  project            = var.project
  environment        = var.environment
  region             = var.region
  ecr_image_uri      = "${module.ecr.repository_url}:${local.image_tag}"
  execution_role_arn = module.iam.execution_role_arn
  project_root       = local.project_root

  depends_on = [module.ecr, module.iam]
}
