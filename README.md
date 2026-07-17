# tofUI 🎨

[![Install](https://img.shields.io/badge/brew%20install-tofui-orange?logo=homebrew&logoColor=white)](https://github.com/65156/homebrew-tofui)
[![Release](https://img.shields.io/github/v/release/65156/tofUI?label=release)](https://github.com/65156/tofUI/releases/latest)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](https://opensource.org/licenses/MIT)

Beautiful, interactive HTML reports from OpenTofu & Terraform plans.

👉 **[Live example report](https://65156.github.io/tofUI/has-changes-example.html)** · more in [examples.md](examples.md)

## Install

```bash
brew tap 65156/tofui
brew install tofui
```

> **Homebrew 6.0+** requires trusting third-party taps. If you see
> `Refusing to load formula … from untrusted tap`, run `brew trust 65156/tofui`
> and re-run the install.

<details>
<summary>Other install methods</summary>

```bash
# Homebrew, without tapping first
brew install 65156/tofui/tofui

# pip (from PyPI) — generating reports needs no dependencies at all
pip install tofui

# pip (latest from GitHub)
pip install git+https://github.com/65156/tofUI.git
```

Publishing backends are opt-in, so a plain install stays dependency-free.
Add only what you use:

| Extra | Installs | Needed for |
|---|---|---|
| `tofui[s3]` | boto3 | `--s3-bucket` |
| `tofui[gcs]` | google-cloud-storage | `--gcs-bucket` |
| `tofui[ghpages]` | requests | `--github-repo` |
| `tofui[dashboard]` | requests | `--dashboard-repo` |

```bash
pip install 'tofui[gcs]'          # one backend
pip install 'tofui[s3,ghpages]'   # or combine
```

</details>

## Usage

**1. Produce a plan JSON** with OpenTofu or Terraform:

```bash
# OpenTofu
tofu plan -out=plan.tfplan
tofu show -json plan.tfplan > plan.json

# Terraform
terraform plan -out=plan.tfplan
terraform show -json plan.tfplan > plan.json
```

**2. Generate the report** (`--build-name` sets the output filename):

```bash
tofui plan.json --build-name my-plan
```

**3. Open it:**

```bash
open my-plan.html
```

That's the whole workflow. For S3/GCS/GitHub Pages uploads, dashboard publishing,
CI/CD, and configuration, see **[examples.md](examples.md)**.

### Hosting reports on a private bucket

Upload to a private S3 or GCS bucket and get a signed link to share on a PR —
no public hosting required:

```bash
# GCS (requires: pip install 'tofui[gcs]')
tofui plan.json --build-name "pr-42-$GITHUB_SHA" \
  --gcs-bucket my-project-tf-plan-reports --gcs-prefix plans/pr-42

# S3
tofui plan.json --build-name "pr-42-$GITHUB_SHA" \
  --s3-bucket my-tf-plan-reports --s3-prefix plans/pr-42
```

Both upload with `Content-Type: text/html` so the report renders in the browser
rather than downloading, and print a signed URL valid for `--signed-url-expiry`
(default `7d`, which is the maximum both providers allow). Pass `--no-signed-url`
for a public bucket where a plain object URL is enough.

When `--stdout-tf-log` is used, the terraform log is uploaded and signed
alongside the report automatically, and the report is pointed at that signed URL
— so the log terminal works from the bucket with nothing extra to configure. The
log lands next to the report, so a single signed report link stays self-sufficient.

Signing GCS URLs needs a key to sign with: either a service-account key via
`GOOGLE_APPLICATION_CREDENTIALS`, or `roles/iam.serviceAccountTokenCreator` on
the active identity so tofUI can sign through the IAM API (e.g. under Workload
Identity Federation).

## Contributing

```bash
git clone https://github.com/65156/tofUI.git
cd tofUI
python -m venv venv && source venv/bin/activate
pip install -e '.[dev]'
python test_tofui.py
```

Then fork, branch, and open a pull request.

## License

[MIT](LICENSE)
