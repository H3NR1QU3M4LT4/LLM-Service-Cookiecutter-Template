output "application_insights_id" {
  value = azurerm_application_insights.appinsights.id
}

output "application_insights_name" {
  value = azurerm_application_insights.appinsights.name
}

output "connection_string" {
  value     = azurerm_application_insights.appinsights.connection_string
  sensitive = true
}

output "log_analytics_workspace_id" {
  value = azurerm_log_analytics_workspace.logs.id
}
