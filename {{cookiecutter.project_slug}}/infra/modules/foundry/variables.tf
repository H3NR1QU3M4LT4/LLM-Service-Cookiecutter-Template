variable "resource_group_name" {
  type = string
}

variable "location" {
  type = string
}

variable "name" {
  type        = string
  description = "Foundry account name; also its custom subdomain (globally unique)."
}

variable "project_name" {
  type = string
}

variable "deployment_name" {
  type        = string
  description = "Deployment name; the backend receives it as AZURE_OPENAI_DEPLOYMENT."
}

variable "model_name" {
  type        = string
  description = "Model name as in the Azure catalog, e.g. gpt-5.6-luna."
}

variable "model_version" {
  type        = string
  default     = null
  description = "Model version; null lets Azure pick the default."
}

variable "sku_name" {
  type    = string
  default = "GlobalStandard"
}

variable "capacity" {
  type        = number
  description = "Capacity in thousands of tokens per minute."
}

variable "tags" {
  type = map(string)
}

variable "subscription_id" {
  type        = string
  description = "Azure subscription ID (consumed by the provider generated in root.hcl)"
}
