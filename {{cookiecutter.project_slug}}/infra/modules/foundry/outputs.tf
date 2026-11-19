output "id" {
  value = azurerm_cognitive_account.foundry.id
}

output "endpoint" {
  value = azurerm_cognitive_account.foundry.endpoint
}

output "deployment_name" {
  value = azurerm_cognitive_deployment.chat.name
}
