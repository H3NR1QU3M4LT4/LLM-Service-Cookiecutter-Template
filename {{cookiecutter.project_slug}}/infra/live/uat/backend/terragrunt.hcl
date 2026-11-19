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

dependency "foundry" {
  config_path = "../foundry"

  mock_outputs_allowed_terraform_commands = ["init", "validate", "plan", "destroy"]
  mock_outputs_merge_strategy_with_state  = "shallow"
  mock_outputs = {
    id              = "${local.rg_id}/providers/Microsoft.CognitiveServices/accounts/mock"
    endpoint        = "https://mock.cognitiveservices.azure.com/"
    deployment_name = "chat"
  }
}

dependency "obs" {
  config_path = "../observability"

  mock_outputs_allowed_terraform_commands = ["init", "validate", "plan", "destroy"]
  mock_outputs_merge_strategy_with_state  = "shallow"
  mock_outputs = {
    application_insights_id = "${local.rg_id}/providers/Microsoft.Insights/components/mock"
    connection_string       = "InstrumentationKey=00000000-0000-0000-0000-000000000000"
  }
}

terraform {
  source = "${get_terragrunt_dir()}/../../../modules/web-app"
}

inputs = {
  resource_group_name = dependency.rg.outputs.name
  location            = dependency.rg.outputs.location
  name                = local.l.backend_app_name
  service_plan_id     = dependency.plan.outputs.id
  port                = 8000
  health_check_path   = "/status"
  image_repository    = "backend"
  image_tag           = local.l.image_tag
  acr_id              = dependency.acr.outputs.id
  acr_login_server    = dependency.acr.outputs.login_server

  app_settings = {
    ENVIRONMENT                           = local.l.env
    APP_VERSION                           = local.l.app_version
    API_KEY                               = get_env("TF_VAR_api_key", "")
    AZURE_OPENAI_ENDPOINT                 = dependency.foundry.outputs.endpoint
    AZURE_OPENAI_DEPLOYMENT               = dependency.foundry.outputs.deployment_name
    APPLICATIONINSIGHTS_CONNECTION_STRING = dependency.obs.outputs.connection_string
  }

  # The backend reaches the model with its managed identity (ENVIRONMENT != local never uses a key).
  role_assignments = {
    openai_user = {
      scope = dependency.foundry.outputs.id
      role  = "Cognitive Services OpenAI User"
    }
  }

  tags            = local.l.tags
  subscription_id = local.sub
}
