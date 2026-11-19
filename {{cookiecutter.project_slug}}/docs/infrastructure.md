# Infrastructure

`infra/` is Terragrunt over small Terraform modules (azurerm 4), laid out like the `llm-monorepo` template:

```
infra/
├── root.hcl                      # azurerm remote state; generates the provider and versions for every unit
├── modules/                      # one module per resource kind
│   ├── resource-group  observability  foundry  container-registry  app-service-plan
│   └── web-app  budget  workbook
└── live/{dev,uat,prod}/
    ├── env.hcl                   # names, region, SKUs, model capacity, budget, tags for that environment
    └── <unit>/terragrunt.hcl     # resource-group, observability, foundry, container-registry,
                                  # app-service-plan, backend, frontend, budget, workbook
```

Each unit has its own state (`<env>/<unit>/terraform.tfstate`) and declares its `dependency` blocks, so
`terragrunt run-all` applies them in order: resource group, then observability, foundry, registry and plan, then
backend, then frontend, budget and workbook.

## What each environment gets

| Resource | Purpose |
|---|---|
| Resource group `rg-<slug>-<env>` | Everything below; the budget is scoped to it |
| Log Analytics + Application Insights | Telemetry (see [observability.md](observability.md)) |
| Container registry (Basic, admin off) | Holds the `backend` and `frontend` images |
| App Service plan (Linux) | `B1` in dev and uat, `P1v3` in prod (`env.hcl`) |
| Web app `...-api` | Backend container, port 8000, health check `/status` |
| Web app `...-web` | Frontend container (nginx), port 8080; proxies `/api/` to the backend and adds `X-API-Key` |
| Foundry (`AIServices` account, project, model deployment) | The LLM; key auth disabled, Entra ID only |
| Role assignments | Both apps `AcrPull`; backend `Cognitive Services OpenAI User` on Foundry |
| Consumption budget | Emails at 80% actual, 100% actual and 100% forecast |
| Workbook | The API dashboard |

Both web apps use a system-assigned managed identity. The backend runs with `ENVIRONMENT=dev|uat|prod`, so it
authenticates to the model with `DefaultAzureCredential` (the managed identity), never with a key.

## Per-environment settings

Edit `infra/live/<env>/env.hcl` (generated from the cookiecutter answers):

| Setting | Meaning |
|---|---|
| `openai_model_name` | `gpt-5.6-luna` by default; `openai_model_version` is `null` (Azure picks the default). Check regional availability: `az cognitiveservices model list -l <region>` |
| `openai_capacity` | Thousands of tokens per minute: 10 dev, 20 uat, 50 prod |
| `app_service_sku` | Plan size |
| `budget_amount`, `budget_alert_emails` | Monthly budget and who is emailed |
| names | `...-<name_suffix>` makes web apps, registry and Foundry names globally unique; change `name_suffix` if Azure says a name is taken |
| resource group | Created by the `resource-group` unit; override the name with `AZURE_RG_<ENV>` |

`image_tag` and `app_version` come from the `IMAGE_TAG` and `APP_VERSION` environment variables.

## Deploy

Prerequisites: Terraform >= 1.9, Terragrunt, the Azure CLI, and an existing storage account for the state.

```bash
az login
export TG_STATE_RESOURCE_GROUP=<rg of the state storage account>
export TG_STATE_STORAGE_ACCOUNT=<state storage account>
export TF_VAR_subscription_id=<subscription id of this environment>
export TF_VAR_api_key=$(openssl rand -base64 32)       # keep it: the apps and CI need the same value per environment
export IMAGE_TAG=0.1.0 APP_VERSION=0.1.0

cd infra/live/dev                                       # or uat / prod
terragrunt run-all plan
terragrunt run-all apply
```

The apps exist after `apply` but their images do not yet. Build them in the registry (no local Docker needed;
`apps/backend/uv.lock` and `apps/frontend/package-lock.json` must be committed), then restart the apps:

```bash
ACR=<acr name>                                          # e.g. acrmyllmservicedev001
az acr build --registry $ACR --image backend:$IMAGE_TAG  ../../../apps/backend
az acr build --registry $ACR --image frontend:$IMAGE_TAG ../../../apps/frontend
az webapp restart -g <resource group> -n <backend app name>
az webapp restart -g <resource group> -n <frontend app name>
```

To release a new version, build with a new tag and `terragrunt run-all apply` with the new `IMAGE_TAG` and
`APP_VERSION`.

## GitHub Actions

`.github/workflows/infra.yml` (Actions, "Infrastructure - Terragrunt", manual) runs `hclfmt` and `terraform fmt`
checks, `init`, `validate` and `plan` for the chosen environment. `apply` and `destroy` run only after a successful
plan and the GitHub Environment approval; `destroy` also needs `destroy_confirmation = DESTROY`. Per GitHub
Environment (`dev`, `uat`, `prod`) set:

| Kind | Name |
|---|---|
| Secret | `AZURE_CREDENTIALS_<ENV>`: service principal JSON (`clientId`, `clientSecret`, `tenantId`, `subscriptionId`) |
| Secret | `API_KEY_<ENV>`: the backend `API_KEY` for that environment |
| Variable | `AZURE_SUBSCRIPTION_ID_<ENV>` |
| Variable | `TF_STATE_RESOURCE_GROUP`, `TF_STATE_STORAGE_ACCOUNT`, `TF_STATE_CONTAINER` (default `tfstate`) |

`.github/workflows/ci.yml` still gates every pull request with the quality hooks. The service principal needs
Contributor and User Access Administrator (it creates role assignments) on the environment's subscription or
resource group, and Storage Blob Data Contributor on the state storage account.

## Budget

`modules/budget` creates a monthly budget on the resource group (it includes the model, so token spend counts).

- A budget only alerts. It does not stop or throttle anything. To cap model spend, also lower `openai_capacity`.
- Cost data lags by hours, so alerts are not instant.
- `budget_start_date` is the first day of the month the project was generated; it must be the first day of a month.

## Not covered (decide before production)

- **The backend is reachable from the internet.** `X-API-Key` is the only gate. Put Entra ID login in front of the
  frontend (App Service Authentication), and restrict the backend with access restrictions or a private endpoint so
  only the frontend can reach it. Without login on the frontend, anyone who finds its URL can call `/ask` with the key
  attached.
- **`API_KEY` is a plain app setting**, visible to anyone with portal access to the app. Move it to Key Vault references.
- **Ollama fallback does not exist in Azure.** The backend always registers it as the fallback; in Azure it fails fast
  (connection refused) after its retries when the primary fails. Host Ollama somewhere reachable or accept that
  there is no fallback.
- Rate limiting, WAF/Front Door, custom domains and alert rules on errors or latency.
- **Verification:** the modules pass `terraform validate` and the Terragrunt files pass `hclfmt` on a rendered project.
  Nothing was planned or applied against a real subscription (no state storage, no credentials), so expect to adjust
  names, SKUs, the model's availability in your region, or the Foundry project resource on the first run.
