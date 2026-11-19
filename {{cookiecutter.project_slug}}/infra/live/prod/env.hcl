locals {
  env      = "prod"
  location = get_env("REGION", "{{ cookiecutter.azure_location }}")

  resource_group_name = get_env("AZURE_RG_PROD", "rg-{{ cookiecutter.project_slug }}-prod")

  # Names that must be globally unique carry {{ cookiecutter.name_suffix }}; change it if Azure says a name is taken.
  log_analytics_name        = "log-{{ cookiecutter.project_slug }}-prod"
  application_insights_name = "appi-{{ cookiecutter.project_slug }}-prod"
  foundry_name              = "ais-{{ cookiecutter.project_slug }}-prod-{{ cookiecutter.name_suffix }}"
  foundry_project_name      = "aip-{{ cookiecutter.project_slug }}-prod"
  acr_name                  = "acr{{ cookiecutter.project_slug.replace('-', '') }}prod{{ cookiecutter.name_suffix }}"
  app_service_plan_name     = "plan-{{ cookiecutter.project_slug }}-prod"
  backend_app_name          = "app-{{ cookiecutter.project_slug }}-prod-{{ cookiecutter.name_suffix }}-api"
  frontend_app_name         = "app-{{ cookiecutter.project_slug }}-prod-{{ cookiecutter.name_suffix }}-web"
  workbook_display_name     = "{{ cookiecutter.project_slug }}-prod API"

  app_service_sku = "P1v3"

  # Foundry deployment. Check the model is available in the region: az cognitiveservices model list -l <region>
  openai_deployment_name = "chat"
  openai_model_name      = "{{ cookiecutter.azure_openai_model }}"
  openai_model_version   = null
  openai_capacity        = 50

  # Set by CI/deploy: the image tag to run and the version shown on /status and in telemetry.
  image_tag   = get_env("IMAGE_TAG", "latest")
  app_version = get_env("APP_VERSION", "0.0.1")

  budget_amount       = {{ cookiecutter.budget_amount_prod }}
  budget_start_date   = "{% now 'utc', '%Y-%m-01' %}T00:00:00Z"
  budget_alert_emails = [for e in split(",", "{{ cookiecutter.budget_alert_emails }}") : trimspace(e)]

  tags = {
    Environment = "prod"
    Owner       = "{{ cookiecutter.author_email }}"
    ManagedBy   = "Terragrunt"
  }
}

inputs = {
  subscription_id = get_env("TF_VAR_subscription_id", "")
}
