variable "kubeconfig_path" {
  type    = string
  default = "~/.kube/config"
}

variable "namespace" {
  type    = string
  default = "amma"
}

variable "docker_registry" {
  type    = string
  default = "localhost:5000"
}
