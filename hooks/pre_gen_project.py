"""Reject answers that would produce invalid Azure names or broken config files, before anything is written."""

import re
import sys

slug = "{{ cookiecutter.project_slug }}"
suffix = "{{ cookiecutter.name_suffix }}"
emails = "{{ cookiecutter.budget_alert_emails }}"
python_version = "{{ cookiecutter.python_version }}"
location = "{{ cookiecutter.azure_location }}"
amounts = {
    "budget_amount_dev": "{{ cookiecutter.budget_amount_dev }}",
    "budget_amount_uat": "{{ cookiecutter.budget_amount_uat }}",
    "budget_amount_prod": "{{ cookiecutter.budget_amount_prod }}",
}

errors = []

# Names are built as <type>-<slug>-<env>-<suffix>[-api]: the container registry (alphanumeric, max 50), the Foundry
# subdomain (max 64) and the web apps (max 60) are the tightest, so the slug must stay short.
if not re.fullmatch(r"[a-z][a-z0-9-]{1,26}[a-z0-9]", slug) or "--" in slug:
    errors.append(
        f"project_slug {slug!r} must be 3-28 chars: lowercase letters, digits and single hyphens, "
        "starting with a letter (it prefixes every Azure resource name)."
    )
if not re.fullmatch(r"[a-z0-9]{1,6}", suffix):
    errors.append(f"name_suffix {suffix!r} must be 1-6 lowercase letters or digits (it makes global names unique).")
if not re.fullmatch(r"3\.\d{1,2}", python_version):
    errors.append(f"python_version {python_version!r} must look like 3.13.")
if not re.fullmatch(r"[a-z]+[a-z0-9]*", location):
    errors.append(f"azure_location {location!r} must be an Azure region name such as westeurope.")
for key, value in amounts.items():
    if not re.fullmatch(r"\d+(\.\d+)?", value):
        errors.append(f"{key} {value!r} must be a number.")
for email in (e.strip() for e in emails.split(",")):
    if not re.fullmatch(r"[^@\s\"']+@[^@\s\"']+\.[^@\s\"']+", email):
        errors.append(f"budget_alert_emails: {email!r} is not a valid email address.")

if errors:
    print("Invalid answers:\n- " + "\n- ".join(errors), file=sys.stderr)
    sys.exit(1)
