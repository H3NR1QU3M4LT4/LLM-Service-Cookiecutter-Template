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

terraform {
  source = "${get_terragrunt_dir()}/../../../modules/foundry"
}

inputs = {
  resource_group_name = dependency.rg.outputs.name
  location            = dependency.rg.outputs.location
  name                = local.l.foundry_name
  project_name        = local.l.foundry_project_name
  deployment_name     = local.l.openai_deployment_name
  model_name          = local.l.openai_model_name
  model_version       = local.l.openai_model_version
  capacity            = local.l.openai_capacity
  tags                = local.l.tags
  subscription_id     = local.sub
}
