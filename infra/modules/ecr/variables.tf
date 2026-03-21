variable "project" {
  type = string
}

variable "environment" {
  type = string
}

variable "region" {
  type = string
}

variable "project_root" {
  description = "Absolute path to the project root directory"
  type        = string
}

variable "image_tag" {
  description = "Docker image tag (content-based hash)"
  type        = string
}
