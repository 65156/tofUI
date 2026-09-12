# Changelog

## 2.0.0 — Maze UI Integration Release

### Breaking changes
- Python package version bumped to `2.0.0`.
- Old theme-class body attributes (`theme-yellow`, `theme-green`, `theme-red`) removed; theming is now entirely driven by CSS custom properties.
- `_get_theme_css()` removed. Use the `theme` block in your config JSON instead.

### New: theme config system
All visual colours are now CSS custom properties (`--bg-*`, `--text-*`, `--border-*`, `--accent-*`, `--chip-*`, `--diff-*`, `--terminal-*`).

The generator emits a `:root { }` block at the top of every report.  Defaults reproduce the previous light palette exactly; overriding any key in the config `theme` block changes only that value.

```json
{
  "theme": {
    "--bg-page":    "#0d1117",
    "--bg-surface": "#161b22",
    "--text-primary": "#e6edf3"
  }
}
```

Full key reference: see **README — Theme configuration**.

### New: preset files
Two ready-made config presets ship inside the package:

| File | Purpose |
|---|---|
| `tofui/presets/tofui_maze_embed.json` | Full dark palette, header/footer hidden — for Maze UI embed |
| `tofui/presets/tofui_light.json` | Standard light palette, all sections visible |

Load with `--config "$(python -c "import tofui.presets, os; print(os.path.join(os.path.dirname(tofui.presets.__file__), 'tofui_maze_embed.json'))")"`.

### New: `sections` config block
Control header and footer visibility per-report without editing the generator:

```json
{
  "sections": { "header": false, "footer": false }
}
```

Honoured in all three generators (plan, apply, error).

### New: tofui-watermark
Every report now includes a `<div class="tofui-watermark">` at the bottom.  It is always rendered — even when `sections.footer = false` — links to the GitHub repo, shows the package version, and uses `var(--text-tertiary)` so it fades into the background in any palette.

### Plan report overhaul
- All emoji removed from headings and section labels.
- No-changes page: replaced green-block with a clean `.state-card` layout.
- Error/failed page: replaced big red gradient header with neutral header; errors now render as `.error-card` blocks with an inline stack trace terminal (always shown when output is available, regardless of `log_file_available`).

### Apply report overhaul
- Summary bar: emoji removed; `state-card` layout used for all result states.
- Stat pills (`created / modified / destroyed`) use `var(--diff-*)` colours, matching the diff table.
- Apply errors section: uses the same `.error-card` layout as plan errors.
- No-changes apply ("Nothing to do"): minimal `state-card` — no icon emoji.
- Resource operations: status shown as text badge (`.status-badge`) instead of emoji icons.

### CSS / architecture
- All hardcoded hex values in `_get_embedded_css` replaced with `var(--*)` calls.
- Old per-theme body-class CSS (`theme-yellow`, `theme-green`, `theme-red`) removed — no longer needed.
- `resource-change.highlighted` box-shadow wired into embedded CSS (was missing from production path).
- Scrollbar CSS vendor prefixes removed (declutters ~50 lines, kept functional equivalents).
- Footer buttons: emoji labels removed, `var(--bg-header)` colour.

## 1.5.2 and earlier

See git log.
