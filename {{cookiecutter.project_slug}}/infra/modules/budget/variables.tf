variable "resource_group_id" {
  type = string
}

variable "resource_group_name" {
  type = string
}

variable "contact_emails" {
  type = list(string)

  validation {
    condition     = length(var.contact_emails) > 0
    error_message = "contact_emails must contain at least one email address."
  }
}

variable "amount" {
  type        = number
  description = "Monthly budget amount, in the subscription's currency."
}

variable "start_date" {
  type        = string
  description = "RFC 3339, the first day of a month."
}

variable "subscription_id" {
  type        = string
  description = "Azure subscription ID (consumed by the provider generated in root.hcl)"
}
