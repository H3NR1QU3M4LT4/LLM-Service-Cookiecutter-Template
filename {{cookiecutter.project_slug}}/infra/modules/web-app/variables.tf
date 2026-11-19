variable "resource_group_name" {
  type = string
}

variable "location" {
  type = string
}

variable "name" {
  type        = string
  description = "Web app name (globally unique)."
}

variable "service_plan_id" {
  type = string
}

variable "port" {
  type        = number
  description = "Port the container listens on (WEBSITES_PORT)."
}

variable "health_check_path" {
  type    = string
  default = "/"
}

variable "image_repository" {
  type = string
}

variable "image_tag" {
  type = string
}

variable "acr_id" {
  type = string
}

variable "acr_login_server" {
  type = string
}

variable "app_settings" {
  type      = map(string)
  default   = {}
  sensitive = true
}

variable "role_assignments" {
  type = map(object({
    scope = string
    role  = string
  }))
  default = {}
}

variable "tags" {
  type = map(string)
}

variable "subscription_id" {
  type        = string
  description = "Azure subscription ID (consumed by the provider generated in root.hcl)"
}
