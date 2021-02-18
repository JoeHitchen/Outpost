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
      version = "2.11.0"
    }
  }
}


provider "docker" {
  host = "tcp://${var.docker_host}/"
}


data "docker_registry_image" "target" {
  name = "${var.registry_host}/mock:1.0.0"
}


