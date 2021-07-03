variable "docker_host" {
  type = string
}

variable "registry_host" {
  type = string
}


terraform {
  required_providers {
    docker = {
      source = "kreuzwerker/docker"
      version = "2.13.0"
    }
  }
}


provider "docker" {
  host = "tcp://${var.docker_host}/"
}


data "docker_registry_image" "target" {
  name = "${var.registry_host}/mock:1.0.0"
  insecure_skip_verify = true
}

resource "docker_image" "target" {
  name          = data.docker_registry_image.target.name
  pull_triggers = [data.docker_registry_image.target.sha256_digest]
}

resource "docker_container" "target" {
  name  = "target"
  image = docker_image.target.latest
  ports {
    internal = 8000
    external = 8000
  }
}


