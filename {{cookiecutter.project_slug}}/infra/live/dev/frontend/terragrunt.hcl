include "root" {
  path = find_in_parent_folders("root.hcl")
}

locals {
  env_cfg = read_terragrunt_config(find_in_parent_folders("env.hcl"))
  l       = local.env_cfg.locals
  sub     = local.env_cfg.inputs.subscription_id
  rg_name = local.l.resource_group_name
  rg_id   = "/subscriptions/${local.sub}/resourceGroups/${local.rg_name}"
}

dependency "rg" {
  config_path = "../resource-group"

  mock_outputs_allowed_terraform_commands = ["init", "validate", "plan", "destroy"]
  mock_outputs_merge_strategy_with_state  = "shallow"
  mock_outputs = {
    name     = local.rg_name
    id       = local.rg_id
    location = local.l.location
  }
}

dependency "plan" {
  config_path = "../app-service-plan"

  mock_outputs_allowed_terraform_commands = ["init", "validate", "plan", "destroy"]
  mock_outputs_merge_strategy_with_state  = "shallow"
  mock_outputs = {
    id = "${local.rg_id}/providers/Microsoft.Web/serverFarms/mock"
  }
}

dependency "acr" {
  config_path = "../container-registry"

  mock_outputs_allowed_terraform_commands = ["init", "validate", "plan", "destroy"]
  mock_outputs_merge_strategy_with_state  = "shallow"
  mock_outputs = {
    id           = "${local.rg_id}/providers/Microsoft.ContainerRegistry/registries/mock"
    login_server = "mock.azurecr.io"
  }
}

dependency "backend" {
  config_path = "../backend"

  mock_outputs_allowed_terraform_commands = ["init", "validate", "plan", "destroy"]
  mock_outputs_merge_strategy_with_state  = "shallow"
  mock_outputs = {
    default_hostname = "mock.azurewebsites.net"
  }
}

terraform {
  source = "${get_terragrunt_dir()}/../../../modules/web-app"
}

inputs = {
  resource_group_name = dependency.rg.outputs.name
  location            = dependency.rg.outputs.location
  name                = local.l.frontend_app_name
  service_plan_id     = dependency.plan.outputs.id
  port                = 8080
  image_repository    = "frontend"
  image_tag           = local.l.image_tag
  acr_id              = dependency.acr.outputs.id
  acr_login_server    = dependency.acr.outputs.login_server

  # nginx proxies /api/ to the backend and adds the key; it never reaches the browser.
  app_settings = {
    BACKEND_URL = "https://${dependency.backend.outputs.default_hostname}"
    API_KEY     = get_env("TF_VAR_api_key", "")
  }

  tags            = local.l.tags
  subscription_id = local.sub
}
