# Dashboard over Application Insights (queries in workbook.json). The name must be a GUID; a v5 UUID of the display
# name keeps it stable across applies.
resource "azurerm_application_insights_workbook" "api" {
  name                = uuidv5("dns", var.display_name)
  resource_group_name = var.resource_group_name
  location            = var.location
  display_name        = var.display_name
  source_id           = lower(var.application_insights_id)
  category            = "workbook"
  data_json           = file("${path.module}/workbook.json")
  tags                = var.tags
}
