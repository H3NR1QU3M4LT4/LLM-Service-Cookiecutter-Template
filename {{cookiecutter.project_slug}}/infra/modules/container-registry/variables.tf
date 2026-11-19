variable "resource_group_name" {
  type = string
}

variable "location" {
  type = string
}

variable "name" {
  type        = string
  description = "Alphanumeric, globally unique."
}

variable "sku" {
  type    = string
  default = "Basic"
}

variable "tags" {
  type = map(string)
}

variable "subscription_id" {
  type        = string
  description = "Azure subscription ID (consumed by the provider generated in root.hcl)"
}
