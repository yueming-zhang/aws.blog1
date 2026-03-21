resource "aws_ecr_repository" "this" {
  name                 = "${var.project}-${var.environment}"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_lifecycle_policy" "this" {
  repository = aws_ecr_repository.this.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep last 5 images"
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 5
      }
      action = { type = "expire" }
    }]
  })
}

resource "null_resource" "docker_build_push" {
  triggers = {
    image_tag = var.image_tag
  }

  provisioner "local-exec" {
    command = <<-EOT
      aws ecr get-login-password --region ${var.region} | \
        docker login --username AWS --password-stdin ${aws_ecr_repository.this.repository_url}

      docker build --platform linux/arm64 \
        -t ${aws_ecr_repository.this.repository_url}:latest \
        -t ${aws_ecr_repository.this.repository_url}:${var.image_tag} \
        -f ${var.project_root}/Dockerfile \
        ${var.project_root}

      docker push ${aws_ecr_repository.this.repository_url}:latest
      docker push ${aws_ecr_repository.this.repository_url}:${var.image_tag}
    EOT
  }

  depends_on = [aws_ecr_repository.this]
}
