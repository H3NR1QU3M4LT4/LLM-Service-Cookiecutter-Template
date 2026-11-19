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
  source = "${get_terragrunt_dir()}/../../../modules/workbook"
}

inputs = {
  resource_group_name     = dependency.rg.outputs.name
  location                = dependency.rg.outputs.location
  display_name            = local.l.workbook_display_name
  application_insights_id = dependency.obs.outputs.application_insights_id
  tags                    = local.l.tags
  subscription_id         = local.sub
}
