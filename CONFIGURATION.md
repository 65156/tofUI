# tofUI Configuration Guide

This guide covers all configuration options, presets, theme customizations, and section visibility for tofUI reports.

---

## 1. Using a Config File

Pass your JSON configuration file using the `--config` / `-c` flag:

```bash
tofui plan.json --build-name my-plan --config tofui_config.json
```

---

## 2. Bundled Presets

`tofui` includes pre-configured preset files inside the package:

| Preset | Description |
|---|---|
| `tofui_maze_embed.json` | Optimized for embedding in Maze UI / iframes (`theme: "maze-auto"`, header/footer suppressed). |
| `tofui_light.json` | Standalone light theme with all sections visible (`theme: "maze-light"`). |

### Loading a Bundled Preset via CLI

```bash
# Maze UI Embed preset
PRESET=$(python -c "import tofui.presets, os; print(os.path.join(os.path.dirname(tofui.presets.__file__), 'tofui_maze_embed.json'))")
tofui plan.json --build-name my-plan --config "$PRESET"

# Standalone Light preset
PRESET=$(python -c "import tofui.presets, os; print(os.path.join(os.path.dirname(tofui.presets.__file__), 'tofui_light.json'))")
tofui plan.json --build-name my-plan --config "$PRESET"
```

---

## 3. Theme Selection (`theme` & `--theme`)

You can set the theme name via the CLI flag `--theme` or inside your config JSON:

```bash
tofui plan.json --build-name my-plan --theme maze-auto
```

```json
{
  "theme": "maze-auto"
}
```

### Supported Theme Names

| Theme Name | Description |
|---|---|
| `maze-auto` / `auto` *(default)* | Automatic theme adaptation: listens for Maze UI parent window `postMessage` (`{ type: 'theme', value: 'dark'|'light' }`) and falls back to OS/browser dark mode preference. |
| `maze-dark` | Fixed Maze dark palette (zinc-950 base). |
| `maze-light` | Fixed Maze light palette (warm off-white surface, blue accents). |
| `light` | Legacy tofUI light palette. |

---

## 4. Custom CSS Property Overrides

All report colours and radii are CSS custom properties. You can override individual tokens using `theme_overrides` in your config JSON:

```json
{
  "theme": "maze-auto",
  "theme_overrides": {
    "--bg-page": "#0d1117",
    "--bg-surface": "#161b22",
    "--text-primary": "#e6edf3"
  }
}
```

### Complete Theme Keys Reference

| CSS Property | Purpose |
|---|---|
| `--bg-page` | Page background |
| `--bg-surface` | Card / panel surface background |
| `--bg-muted` | Group headers, filter chips, secondary backgrounds |
| `--bg-header` | Report header bar background |
| `--text-primary` | Main body text |
| `--text-secondary` | Labels and table text |
| `--text-muted` | Muted column headers, status text |
| `--text-tertiary` | Watermark, decorative borders |
| `--border` | Default hairline border |
| `--border-strong` | Stronger border (table headers, active borders) |
| `--accent-create` | Create action stripe |
| `--accent-update` | Update action stripe |
| `--accent-delete` | Delete action stripe |
| `--accent-replace` | Replace action stripe |
| `--accent-read` | Read action stripe |
| `--chip-create-bg` / `--chip-create-fg` | Create action filter chip |
| `--chip-update-bg` / `--chip-update-fg` | Update action filter chip |
| `--chip-delete-bg` / `--chip-delete-fg` | Delete action filter chip |
| `--chip-replace-bg` / `--chip-replace-fg` | Replace action filter chip |
| `--diff-add-bg` / `--diff-add-fg` | Addition diff row highlight |
| `--diff-del-bg` / `--diff-del-fg` | Deletion diff row highlight |
| `--diff-mod-bg` / `--diff-mod-fg` | Modification diff row highlight |
| `--terminal-bg` / `--terminal-fg` | Terminal code block background and text |

---

## 5. Section Visibility (`sections`)

You can control whether the report header and footer render:

```json
{
  "sections": {
    "header": false,
    "footer": false
  }
}
```

*Note: The unified watermark (`tofui-watermark`) is always rendered at the bottom for attribution.*

---

## 6. Property Filtering & Display Options

Control which properties are collapsible or hidden by default:

```json
{
  "properties": {
    "available_to_hide": ["tags", "tags_all", "timeouts"],
    "hidden_by_default": ["tags_all"]
  },
  "display": {
    "expand_all_default": false
  }
}
```
