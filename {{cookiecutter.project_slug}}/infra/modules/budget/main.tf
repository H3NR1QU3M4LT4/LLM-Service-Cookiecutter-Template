# Alerts only: Azure has no native way to hard-block spend at a resource group level.
resource "azurerm_consumption_budget_resource_group" "budget" {
  name              = "budget-${var.resource_group_name}"
  resource_group_id = var.resource_group_id

  amount     = var.amount
  time_grain = "Monthly"

  time_period {
    start_date = var.start_date
  }

  notification {
    enabled        = true
    threshold      = 80
    operator       = "GreaterThanOrEqualTo"
    threshold_type = "Actual"
    contact_emails = var.contact_emails
  }

  notification {
    enabled        = true
    threshold      = 100
    operator       = "GreaterThanOrEqualTo"
    threshold_type = "Forecasted"
    contact_emails = var.contact_emails
  }
}
