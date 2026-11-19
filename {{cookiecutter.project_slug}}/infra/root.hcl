# Remote state in an existing storage account (TG_STATE_* env vars), one state per unit; provider and versions are
# generated into every unit, so modules carry no provider config.
remote_state {
  backend = "azurerm"
  generate = {
    path      = "backend.tf"
    if_exists = "overwrite_terragrunt"
  }
  config = {
    resource_group_name  = get_env("TG_STATE_RESOURCE_GROUP")
    storage_account_name = get_env("TG_STATE_STORAGE_ACCOUNT")
    container_name       = get_env("TG_STATE_CONTAINER", "tfstate")
    key                  = "${path_relative_to_include()}/terraform.tfstate"
    use_azuread_auth     = true
  }
}

generate "versions" {
  path      = "versions.auto.tf"
  if_exists = "overwrite_terragrunt"
  contents  = <<EOF
terraform {
  required_version = ">= 1.9"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }
}
EOF
}

generate "provider" {
  path      = "provider.auto.tf"
  if_exists = "overwrite_terragrunt"
  contents  = <<EOF
provider "azurerm" {
  features {
    cognitive_account {
      purge_soft_delete_on_destroy = false
    }
  }
  subscription_id                 = var.subscription_id
  resource_provider_registrations = "none"
}
EOF
}
