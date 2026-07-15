# tofUI Examples

Detailed usage beyond the basic workflow in the [README](README.md).

## Live example reports

- [Large plan](https://65156.github.io/tofUI/large-plan-example.html) — 21 resources across AWS, Kubernetes, GCP & Helm, with creates, deletes, updates, and replacements, plus the auto-loaded terraform log
- [Has changes](https://65156.github.io/tofUI/has-changes-example.html) — a simple plan with a single change
- [Has errors](https://65156.github.io/tofUI/has-errors-example.html) — a plan that failed with errors
- [No changes](https://65156.github.io/tofUI/no-changes-example.html) — infrastructure already up to date

## Generating the plan JSON

```bash
# OpenTofu
tofu plan -out=plan.tfplan
tofu show -json plan.tfplan > plan.json

# Terraform
terraform plan -out=plan.tfplan
terraform show -json plan.tfplan > plan.json
```

## Basic usage

```bash
# Minimal — --build-name is required and sets the output filename (my-plan.html)
tofui plan.json --build-name my-plan

# Custom title shown at the top of the report
tofui plan.json --build-name my-plan --display-name "Production Deploy"

# With a configuration file
tofui plan.json --build-name my-plan --config tofui-config.json

# Verbose output
tofui plan.json --build-name my-plan --verbose
```

## S3 upload

```bash
# Upload to an S3 bucket
tofui plan.json --build-name prod --s3-bucket my-terraform-reports

# With a key prefix and region
tofui plan.json --build-name prod \
  --s3-bucket my-terraform-reports \
  --s3-prefix reports/production/ \
  --s3-region us-west-2
```

## GitHub Pages upload

```bash
# Upload to a repo's gh-pages branch
tofui plan.json --build-name production \
  --github-repo owner/terraform-reports \
  --folder aws_us_east_2

# Token via environment variable (recommended)
export GITHUB_TOKEN="ghp_xxxxxxxxxxxx"
tofui plan.json --build-name staging \
  --github-repo owner/terraform-reports \
  --folder release-v2.1

# GitHub Enterprise
tofui plan.json --build-name production \
  --github-repo owner/terraform-reports \
  --github-enterprise-url https://github.example.com \
  --github-branch gh-pages
```

## CI/CD pipelines

Use a dynamic `--build-name` (e.g. `${BUILD_ID}`) so reports don't overwrite each other.

```bash
# With S3
tofui plan.json \
  --build-name "build-${BUILD_NUMBER}" \
  --s3-bucket company-terraform-reports \
  --s3-prefix builds/ \
  --build-url "https://ci.example.com/job/123" \
  --verbose

# With GitHub Pages
tofui plan.json \
  --build-name "${CI_JOB_NAME}-${BUILD_NUMBER}" \
  --github-repo company/terraform-reports \
  --folder "build-$(date +%Y-%m-%d)" \
  --build-url "https://ci.example.com/job/123"
```

Pass `--stdout-tf-log terraform.log` to attach the raw terraform log, which the
report loads into its **Logs** section.

## Dashboard publishing

Track reports across repositories in a centralized dashboard.

```bash
# Plan report (for PRs)
tofui plan.json \
  --build-name "pr-456" \
  --github-repo "myorg/infrastructure" \
  --folder "aws_us_east_2" \
  --dashboard-repo "myorg/tofui-dashboard" \
  --status terraform_plan:2

# Apply report (for merges/deploys)
tofui \
  --apply-mode \
  --stdout-tf-log apply.log \
  --terraform-exit-code 0 \
  --build-name "deploy-123" \
  --github-repo "myorg/infrastructure" \
  --folder "aws_us_east_2" \
  --dashboard-repo "myorg/tofui-dashboard" \
  --status terraform_apply:0 \
  --status tfsec:0
```

See **[DASHBOARD.md](DASHBOARD.md)** for full dashboard documentation.

## Configuration

Pass a JSON config with `--config`:

```json
{
  "properties": {
    "available_to_hide": ["tags", "timeouts"],
    "hidden_by_default": ["tags"]
  },
  "display": {
    "expand_all_default": false
  }
}
```

## CLI reference

Run `tofui --help` for the full, authoritative list. Common options:

| Option | Purpose |
| --- | --- |
| `plan_file` | Path to the terraform plan JSON (positional; not required with `--apply-mode`) |
| `--build-name`, `-n` | **Required.** Report name / output filename |
| `--display-name`, `-d` | Title shown in the report |
| `--build-url` | Build link shown in the report footer |
| `--config`, `-c` | Path to a configuration JSON file |
| `--terraform-exit-code {0,1,2}` | 0=no changes, 1=error, 2=changes |
| `--stdout-tf-log` | Terraform log file (or `-` for stdin) to attach to the report |
| `--apply-mode` | Build an apply report from logs instead of a plan JSON |
| `--s3-bucket` / `--s3-prefix` / `--s3-region` | Upload to S3 |
| `--github-repo` / `--github-token` / `--folder` / `--github-branch` / `--github-enterprise-url` | Upload to GitHub Pages |
| `--dashboard-repo` / `--status` | Publish to a tracking dashboard |
| `--verbose` / `--debug` | Diagnostic output |

## Supported plan format versions

tofUI supports terraform/OpenTofu plan JSON format versions **1.0**, **1.1**, and **1.2**.
