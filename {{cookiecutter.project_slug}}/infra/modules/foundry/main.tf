# Microsoft Foundry resource (AIServices account with project management enabled).
resource "azurerm_cognitive_account" "foundry" {
  name                = var.name
  location            = var.location
  resource_group_name = var.resource_group_name
  kind                = "AIServices"
  sku_name            = "S0"

  custom_subdomain_name      = var.name
  project_management_enabled = true
  # Entra ID only: the backend authenticates with its managed identity, there is no key to leak.
  local_auth_enabled = false

  identity {
    type = "SystemAssigned"
  }

  tags = var.tags
}

resource "azurerm_cognitive_deployment" "chat" {
  name                 = var.deployment_name
  cognitive_account_id = azurerm_cognitive_account.foundry.id

  sku {
    name     = var.sku_name
    capacity = var.capacity
  }

  model {
    format  = "OpenAI"
    name    = var.model_name
    version = var.model_version
  }
}

# Depends on the deployment explicitly: the account serializes write operations, and without this Azure rejects the
# parallel writes with "Another operation is in progress on the resource".
resource "azurerm_cognitive_account_project" "project" {
  name                 = var.project_name
  cognitive_account_id = azurerm_cognitive_account.foundry.id
  location             = var.location

  identity {
    type = "SystemAssigned"
  }

  tags = var.tags

  depends_on = [azurerm_cognitive_deployment.chat]
}
