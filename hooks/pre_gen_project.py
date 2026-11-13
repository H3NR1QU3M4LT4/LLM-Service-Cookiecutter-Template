"""Reject slugs and package names that would produce an invalid project."""

import re
import sys

slug = "{{ cookiecutter.project_slug }}"
package = "{{ cookiecutter.package_name }}"

if not re.fullmatch(r"[a-z][a-z0-9-]*", slug):
    sys.exit(f"ERROR: project_slug must be lowercase letters, digits and dashes: {slug!r}")
if not package.isidentifier() or package != package.lower():
    sys.exit(f"ERROR: package_name must be a lowercase Python identifier: {package!r}")
