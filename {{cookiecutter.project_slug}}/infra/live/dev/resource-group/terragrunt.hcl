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

terraform {
  source = "${get_terragrunt_dir()}/../../../modules/resource-group"
}

inputs = {
  name            = local.rg_name
  location        = local.l.location
  tags            = local.l.tags
  subscription_id = local.sub
}
