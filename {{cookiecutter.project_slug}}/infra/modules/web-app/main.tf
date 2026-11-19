resource "azurerm_linux_web_app" "this" {
  name                = var.name
  resource_group_name = var.resource_group_name
  location            = var.location
  service_plan_id     = var.service_plan_id
  https_only          = true
  tags                = var.tags

  identity {
    type = "SystemAssigned"
  }

  site_config {
    always_on                               = true
    ftps_state                              = "Disabled"
    minimum_tls_version                     = "1.2"
    health_check_path                       = var.health_check_path
    container_registry_use_managed_identity = true

    application_stack {
      docker_image_name   = "${var.image_repository}:${var.image_tag}"
      docker_registry_url = "https://${var.acr_login_server}"
    }
  }

  app_settings = merge(var.app_settings, { WEBSITES_PORT = tostring(var.port) })
}

# The app pulls its image with its managed identity (no registry password).
resource "azurerm_role_assignment" "acr_pull" {
  scope                = var.acr_id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_linux_web_app.this.identity[0].principal_id
}

# Extra roles, keyed by a static name so the keys are known at plan time.
resource "azurerm_role_assignment" "extra" {
  for_each             = var.role_assignments
  scope                = each.value.scope
  role_definition_name = each.value.role
  principal_id         = azurerm_linux_web_app.this.identity[0].principal_id
}
