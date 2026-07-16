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

# pip (from PyPI)
pip install tofui

# pip (latest from GitHub)
pip install git+https://github.com/65156/tofUI.git
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

That's the whole workflow. For S3/GitHub Pages uploads, dashboard publishing,
CI/CD, and configuration, see **[examples.md](examples.md)**.

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
