"""
HTML Report Generator

Generates beautiful, interactive HTML reports from analyzed terraform plan data.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
import json
import html

from . import __version__
from .parser import ActionType  # at top of file if not already imported
from .analyzer import PlanAnalysis, AnalyzedResourceChange, PropertyChange, ActionType


class HTMLGenerator:
    """Generates interactive HTML reports from terraform plan analysis"""
    
    def __init__(self):
        self.plan_name = "tofUI Plan"
        self.timestamp = datetime.now(timezone.utc)
        # Gates the log terminal; set per-report by the generate_* methods below.
        self.log_file_available = False
    
    def generate_report(
        self, 
        analysis: PlanAnalysis, 
        plan_name: Optional[str] = None,
        output_file: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        log_file_available: bool = False
    ) -> str:
        """Generate a complete HTML report from plan analysis"""
        
        self.plan_name = plan_name or "tofUI Plan"
        self.config = config or {}
        self.log_file_available = log_file_available
        
        # Generate the complete HTML content
        html_content = self._generate_complete_html(analysis)
        
        # Write to file if specified
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
        
        return html_content
    
    def generate_error_report(
        self,
        error_output: Optional[str] = None,
        plan_error_data: Optional[str] = None,
        plan_name: Optional[str] = None,
        output_file: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        log_file_available: bool = False
    ) -> str:
        """Generate an error report for terraform failures"""
        
        self.plan_name = plan_name or "tofUI Error Report"
        self.config = config or {}
        self.log_file_available = log_file_available
        
        # Process error data
        processed_errors = self._process_terraform_errors(error_output, plan_error_data)
        
        # Generate the complete HTML content for error report
        html_content = self._generate_error_html(processed_errors)
        
        # Write to file if specified
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
        
        return html_content
    
    def generate_apply_report(
        self,
        apply_result,
        plan_name: Optional[str] = None,
        output_file: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        log_file_available: bool = False
    ) -> str:
        """Generate an apply report for terraform apply results"""
        
        self.plan_name = plan_name or "tofUI Apply Report"
        self.config = config or {}
        self.log_file_available = log_file_available
        
        # Generate the complete HTML content for apply report
        html_content = self._generate_apply_html(apply_result)
        
        # Write to file if specified
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
        
        return html_content
    
    def _generate_log_url_js(self) -> str:
        """Declare the explicit log URL for the log loader to try first.

        A signed bucket URL carries a per-object signature, so the relative
        candidates the loader falls back on cannot reach it.
        """
        import os

        log_url = self.config.get('log_url', '') or os.environ.get('TOFUI_LOG_URL', '')
        return f"const TOFUI_LOG_URL = {json.dumps(log_url or None)};"

    # ── Named palettes ────────────────────────────────────────────────────────
    # Each palette is a flat dict of CSS custom-property → value.
    # Derived from the Maze UI index.css design tokens where possible so that
    # tofUI looks native inside a Maze iframe (or standalone).

    _PALETTE_MAZE_DARK = {
        # Surfaces — zinc-950 base (Maze dark)
        "--bg-page":         "#09090b",   # zinc-950
        "--bg-surface":      "#111113",   # zinc-900-ish
        "--bg-muted":        "#18181b",   # zinc-900
        "--bg-header":       "#27272a",   # zinc-800 (overlay)
        # Text
        "--text-primary":    "#fafafa",   # zinc-50
        "--text-secondary":  "#a1a1aa",   # zinc-400
        "--text-muted":      "#71717a",   # zinc-500
        "--text-tertiary":   "#52525b",   # zinc-600
        # Borders
        "--border":          "#2a2a2f",   # Maze border-default
        "--border-strong":   "#52525b",   # zinc-600
        # Accents (Terraform action colours)
        "--accent-create":   "#3b82f6",   # blue-500  (Maze --success)
        "--accent-update":   "#f59e0b",   # amber-500 (Maze --warning)
        "--accent-delete":   "#ef4444",   # red-500   (Maze --error)
        "--accent-replace":  "#7c3aed",   # violet-600 (Maze --brand-primary)
        "--accent-read":     "#52525b",   # zinc-600
        # Action chips
        "--chip-create-bg":  "#0c1a2e",   # Maze --success-bg
        "--chip-create-fg":  "#93c5fd",   # blue-300
        "--chip-update-bg":  "#1c1000",   # Maze --warning-bg
        "--chip-update-fg":  "#fcd34d",   # amber-300
        "--chip-delete-bg":  "#1f0808",   # Maze --error-bg
        "--chip-delete-fg":  "#fca5a5",   # red-300
        "--chip-replace-bg": "#1a0a3d",   # Maze --info-bg
        "--chip-replace-fg": "#c4b5fd",   # violet-300
        # Diff table rows
        "--diff-add-bg":     "#0c1a2e",
        "--diff-add-fg":     "#93c5fd",
        "--diff-del-bg":     "#1f0808",
        "--diff-del-fg":     "#fca5a5",
        "--diff-mod-bg":     "#1c1000",
        "--diff-mod-fg":     "#fcd34d",
        # Terminal
        "--terminal-bg":     "#010409",
        "--terminal-fg":     "#e6edf3",
        # Shadows / radius (Maze tokens)
        "--shadow-sm":       "0 1px 2px rgba(0,0,0,0.5)",
        "--shadow-md":       "0 4px 16px rgba(0,0,0,0.6)",
        "--radius-sm":       "4px",
        "--radius-md":       "6px",
        "--radius-lg":       "10px",
    }

    _PALETTE_MAZE_LIGHT = {
        # Surfaces — warm cream / off-white (Maze light)
        "--bg-page":         "#f8f7f5",   # warm off-white
        "--bg-surface":      "#ffffff",
        "--bg-muted":        "#f3f2ef",   # light cream
        "--bg-header":       "#4b5563",   # grey-600
        # Text
        "--text-primary":    "#18181b",   # zinc-900
        "--text-secondary":  "#52525b",   # zinc-600
        "--text-muted":      "#71717a",   # zinc-500
        "--text-tertiary":   "#a1a1aa",   # zinc-400
        # Borders
        "--border":          "#d4d1cb",   # Maze border-default light
        "--border-strong":   "#9ca3af",   # grey-400
        # Accents
        "--accent-create":   "#2563eb",   # blue-600
        "--accent-update":   "#d97706",   # amber-600
        "--accent-delete":   "#dc2626",   # red-600
        "--accent-replace":  "#6d28d9",   # violet-700
        "--accent-read":     "#9ca3af",   # grey-400
        # Action chips
        "--chip-create-bg":  "#dbeafe",   # blue-100
        "--chip-create-fg":  "#1e40af",   # blue-800
        "--chip-update-bg":  "#fef3c7",   # amber-100
        "--chip-update-fg":  "#92400e",   # amber-800
        "--chip-delete-bg":  "#fee2e2",   # red-100
        "--chip-delete-fg":  "#991b1b",   # red-800
        "--chip-replace-bg": "#ede9fb",   # violet-100
        "--chip-replace-fg": "#4c1d95",   # violet-900
        # Diff table rows
        "--diff-add-bg":     "#dbeafe",
        "--diff-add-fg":     "#1e40af",
        "--diff-del-bg":     "#fee2e2",
        "--diff-del-fg":     "#991b1b",
        "--diff-mod-bg":     "#fef3c7",
        "--diff-mod-fg":     "#92400e",
        # Terminal
        "--terminal-bg":     "#1e1e1e",
        "--terminal-fg":     "#d4d4d4",
        # Shadows / radius
        "--shadow-sm":       "0 1px 2px rgba(0,0,0,0.06)",
        "--shadow-md":       "0 4px 16px rgba(0,0,0,0.08)",
        "--radius-sm":       "4px",
        "--radius-md":       "6px",
        "--radius-lg":       "10px",
    }

    # Legacy light palette — kept for backwards compatibility with old configs
    # that don't specify a theme name.
    _PALETTE_LIGHT_LEGACY = {
        "--bg-page":         "#f8f9fa",
        "--bg-surface":      "#ffffff",
        "--bg-muted":        "#f8f9fa",
        "--bg-header":       "#4b5563",
        "--text-primary":    "#212529",
        "--text-secondary":  "#495057",
        "--text-muted":      "#6c757d",
        "--text-tertiary":   "#adb5bd",
        "--border":          "#e9ecef",
        "--border-strong":   "#dee2e6",
        "--accent-create":   "#28a745",
        "--accent-update":   "#ffc107",
        "--accent-delete":   "#dc3545",
        "--accent-replace":  "#6f42c1",
        "--accent-read":     "#6c757d",
        "--chip-create-bg":  "#e8f6ee",
        "--chip-create-fg":  "#1a7f37",
        "--chip-update-bg":  "#fff6db",
        "--chip-update-fg":  "#7a5b00",
        "--chip-delete-bg":  "#fdeaea",
        "--chip-delete-fg":  "#9b2c2c",
        "--chip-replace-bg": "#f2ecfa",
        "--chip-replace-fg": "#4d2d8a",
        "--diff-add-bg":     "#d4edda",
        "--diff-add-fg":     "#155724",
        "--diff-del-bg":     "#f8d7da",
        "--diff-del-fg":     "#721c24",
        "--diff-mod-bg":     "#fff3cd",
        "--diff-mod-fg":     "#856404",
        "--terminal-bg":     "#1e1e1e",
        "--terminal-fg":     "#d4d4d4",
        "--shadow-sm":       "0 1px 2px rgba(0,0,0,0.06)",
        "--shadow-md":       "0 4px 16px rgba(0,0,0,0.08)",
        "--radius-sm":       "4px",
        "--radius-md":       "6px",
        "--radius-lg":       "10px",
    }

    def _resolve_theme_name(self) -> str:
        """Return the canonical theme name from config.

        Accepts:
          "auto" | "maze-auto"  → "maze-auto"  (default)
          "maze-dark"           → "maze-dark"
          "maze-light"          → "maze-light"
          "light"               → "light"
          <dict>                → "light" (legacy override-dict format, vars merged later)
          <anything else>       → "maze-auto"
        """
        raw = self.config.get("theme", "maze-auto")
        if isinstance(raw, dict):
            # Old format: {"theme": {"--bg-page": "#fff", ...}}
            # Treat as legacy light with the dict values as overrides.
            return "light-legacy-dict"
        aliases = {"auto": "maze-auto"}
        return aliases.get(raw, raw) if raw in ("auto", "maze-dark", "maze-light", "maze-auto", "light") else "maze-auto"

    def _get_theme_vars_css(self) -> str:
        """Emit CSS custom-property blocks for the selected theme.

        For static themes (maze-dark, maze-light, light) a single :root{} block
        is returned.

        For maze-auto: the light palette is the :root default; the dark palette
        is applied via both:
          1. @media (prefers-color-scheme: dark)  — OS/browser default
          2. :root[data-theme="dark"]             — explicit override from Maze
             postMessage (see _get_theme_script)
        The light palette is also pinned via :root[data-theme="light"] so that
        an explicit "light" message from Maze always wins over the OS setting.
        """
        theme = self._resolve_theme_name()

        def _props(palette: dict, extra_overrides: dict = None) -> str:
            merged = {**palette, **(extra_overrides or {})}
            return "\n    ".join(f"{k}: {v};" for k, v in merged.items())

        # Collect any explicit token overrides from config (theme_overrides key)
        overrides = self.config.get("theme_overrides", {})
        # Backwards-compat: old configs put the dict directly under "theme"
        if isinstance(self.config.get("theme"), dict):
            overrides = {**self.config["theme"], **overrides}

        if theme == "maze-dark":
            return f":root {{\n    {_props(self._PALETTE_MAZE_DARK, overrides)}\n}}"

        if theme == "maze-light":
            return f":root {{\n    {_props(self._PALETTE_MAZE_LIGHT, overrides)}\n}}"

        if theme in ("light", "light-legacy-dict"):
            return f":root {{\n    {_props(self._PALETTE_LIGHT_LEGACY, overrides)}\n}}"

        # maze-auto: light base, dark via media query + data-theme attribute
        light_props = _props(self._PALETTE_MAZE_LIGHT, overrides)
        dark_props  = _props(self._PALETTE_MAZE_DARK,  overrides)
        return f""":root {{
    {light_props}
}}

/* Explicit Maze postMessage override — dark */
:root[data-theme="dark"] {{
    {dark_props}
}}

/* OS/browser preference fallback when no explicit data-theme is set */
@media (prefers-color-scheme: dark) {{
    :root:not([data-theme="light"]) {{
        {dark_props}
    }}
}}"""

    def _get_theme_script(self) -> str:
        """Return inline JS for maze-auto theme only.

        Listens for Maze's postMessage: { type: 'theme', value: 'dark'|'light' }
        and applies it as a data-theme attribute on <html>, which the CSS then
        picks up immediately.  Sets the initial value from localStorage so the
        theme is stable across page loads without waiting for a message.
        """
        theme = self._resolve_theme_name()
        if theme != "maze-auto":
            return ""
        return """
        // ── tofUI Maze theme bridge ──────────────────────────────────────────
        (function () {
            var root = document.documentElement;
            // Restore last known theme immediately (avoids flash)
            try {
                var saved = localStorage.getItem('tofui-theme');
                if (saved === 'dark' || saved === 'light') root.dataset.theme = saved;
            } catch (e) {}

            window.addEventListener('message', function (e) {
                if (!e.data || e.data.type !== 'theme') return;
                var t = e.data.value;
                if (t !== 'dark' && t !== 'light') return;
                root.dataset.theme = t;
                try { localStorage.setItem('tofui-theme', t); } catch (e) {}
            });
        })();
        """

    def _generate_complete_html(self, analysis: PlanAnalysis) -> str:
        """Generate the complete HTML document"""
        
        # Generate data for JavaScript
        js_data = self._generate_javascript_data(analysis)
        
        # Determine which template to use based on plan status
        if not analysis.plan.summary.has_changes:
            content_body = self._generate_no_changes_content(analysis)
        else:
            content_body = f"""
                {self._generate_summary(analysis)}
                {self._generate_filters(analysis)}
                {self._generate_resource_groups(analysis)}
            """
        
        # Add outputs section if available
        outputs_section = self._generate_outputs_section(analysis)

        # sections.header / sections.footer booleans (default true)
        sections = self.config.get("sections", {})
        show_header = sections.get("header", True)
        show_footer = sections.get("footer", True)
            
        # Add terminal section for logs (empty unless a log was produced)
        terminal_section = self._generate_terminal_section_placeholder()
            
        theme_script = self._get_theme_script()
        return f"""<!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>tofUI - {html.escape(self.plan_name)}</title>
        <style>
            {self._get_theme_vars_css()}
            {self._get_embedded_css()}
        </style>
        {f'<script>{theme_script}</script>' if theme_script else ''}
    </head>
    <body>
        <div class="container">
            {self._generate_header(analysis) if show_header else ''}
            {content_body}
            {outputs_section}
            {terminal_section}
            {self._generate_footer() if show_footer else ''}
            {self._generate_watermark()}
        </div>
        
        <script>
            // Embedded plan data
            const planData = {js_data};
            {self._generate_log_url_js()}

            {self._get_embedded_javascript()}
        </script>
    </body>
    </html>"""
    
    def _generate_header(self, analysis: PlanAnalysis) -> str:
        """Generate the report header"""
        formatted_time = self.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")
        
        # Build version string only if not default value
        version_str = ""
        if analysis.plan.terraform_version and analysis.plan.terraform_version != "99.99":
            version_str = f"<strong>Version:</strong> {html.escape(analysis.plan.terraform_version)} • "
        
        return f"""
        <div class="header">
            <div class="plan-name"><strong>{html.escape(self.plan_name)}</strong></div>
            <div class="meta-info">{version_str}<strong>Generated:</strong> {formatted_time}</div>
        </div>
        """
    
    def _generate_summary(self, analysis: PlanAnalysis) -> str:
        """Generate the plan summary section"""
        # Change counts are shown on the action filter buttons; no separate block needed.
        return ""
    
    def _generate_filters(self, analysis: PlanAnalysis) -> str:
        """Generate the filter controls"""
        if not analysis.has_changes:
            return ""
        
        # Get configuration settings
        config_properties = self.config.get("properties", {})
        config_display = self.config.get("display", {})
        
        available_properties = config_properties.get("available_to_hide", sorted(analysis.all_property_names))[:5]
        hidden_by_default = config_properties.get("hidden_by_default", [])

        # Property checkboxes — rendered inside a dropdown panel
        properties_html = ""
        for prop in available_properties:
            checked = "checked" if prop in hidden_by_default else ""
            properties_html += f"""
            <label class="filter-checkbox">
                <input type="checkbox" value="{html.escape(prop)}" {checked}> {html.escape(prop)}
            </label>
            """

        # Count resources per action for the filter chips
        from collections import Counter
        action_counts = Counter()
        for group in analysis.resource_groups:
            for change in group.changes:
                action_counts[change.action.value] += 1

        chip_meta = [
            ("delete", "Delete"),
            ("replace", "Replace"),
            ("update", "Update"),
            ("create", "Create"),
        ]
        chips_html = ""
        for key, label in chip_meta:
            count = action_counts.get(key, 0)
            if count:
                chips_html += (
                    f'<button type="button" class="chip active" data-action="{key}">'
                    f'{label} <span class="chip-count">{count}</span></button>'
                )

        has_props = bool(available_properties)
        props_btn = (
            f'<button type="button" id="props-btn" class="toolbar-icon-btn" title="Hide properties" aria-expanded="false" aria-controls="props-panel">'
            f'<svg viewBox="0 0 16 16" width="14" height="14" fill="currentColor"><path d="M1 3h14v1.5H1zm2.5 4h9v1.5h-9zm2.5 4h4v1.5h-4z"/></svg>'
            f'</button>'
            if has_props else ''
        )
        props_panel = (
            f'<div id="props-panel" class="props-panel" hidden>'
            f'<div class="props-panel__inner" id="property-filters">{properties_html}</div>'
            f'</div>'
            if has_props else ''
        )

        return f"""
        <div class="toolbar">
            <div class="toolbar-search">
                <input type="search" id="resource-search" placeholder="Search resources…  (/)" autocomplete="off" spellcheck="false">
                <button type="button" id="search-clear" class="search-clear" title="Clear" aria-label="Clear search">✕</button>
            </div>
            <div class="chips" id="action-chips">{chips_html}</div>
            <div class="toolbar-right">
                <span class="results-count" id="results-count"></span>
                {props_btn}
                <button type="button" id="toggle-all" class="toolbar-icon-btn" title="Expand all" aria-label="Expand all resources">
                    <svg id="toggle-all-icon" viewBox="0 0 16 16" width="14" height="14" fill="currentColor">
                        <path d="M2 5l6 6 6-6z"/>
                    </svg>
                </button>
            </div>
        </div>
        {props_panel}
        <div class="filter-notice" id="filter-notice" role="status">
            <svg class="filter-notice-icon" viewBox="0 0 24 24" width="16" height="16" fill="currentColor" aria-hidden="true"><path d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z"/></svg>
            <span id="filter-notice-text">Filters active</span>
            <button type="button" id="filter-reset" class="filter-reset">Show all</button>
        </div>
        """
    
    def _generate_resource_groups(self, analysis: PlanAnalysis) -> str:
        """Generate the resource groups section"""
        if not analysis.has_changes:
            return ""
        
        groups_html = ""
        for group in analysis.resource_groups:
            groups_html += self._generate_resource_group(group)
        
        return f"""
        <div class="resource-groups" id="resource-groups">
            {groups_html}
        </div>
        <div class="no-results" id="no-results">No resources match your search or filters.</div>
        """

    def _generate_resource_group(self, group) -> str:
        """Generate HTML for a single resource group"""
        action_counts = group.action_counts
        counts_text = ", ".join([
            f"{count} {action.value}" 
            for action, count in action_counts.items()
        ])
        
        resources_html = ""
        for change in group.changes:
            resources_html += self._generate_resource_change(change)
        
        return f"""
        <div class="resource-group" data-resource-type="{html.escape(group.resource_type)}">
            <div class="group-header">
                <h3>{html.escape(group.resource_type)} ({group.count} resources)</h3>
            </div>
            <div class="group-resources">
                {resources_html}
            </div>
        </div>
        """
    
    def _generate_resource_change(self, change: AnalyzedResourceChange) -> str:
        """Generate HTML for a single resource change"""
        action_class = change.action.value
        action_icon = self._get_action_icon(change.action)
        
        properties_html = ""
        if change.has_property_changes:
            properties_html = self._generate_property_changes(change.property_changes, change.action)

        # Derive provider and module path for search/filtering
        rtype = change.type or ""
        provider = rtype.split("_", 1)[0] if "_" in rtype else rtype
        address = change.address or ""
        module_names = []
        parts = address.split(".")
        i = 0
        while i < len(parts) - 1:
            if parts[i] == "module":
                module_names.append(parts[i + 1])
                i += 2
            else:
                i += 1
        module = "/".join(module_names) if module_names else "root"

        return f"""
        <div class="resource-change {action_class}" data-action="{action_class}" data-address="{html.escape(address)}" data-type="{html.escape(rtype)}" data-provider="{html.escape(provider)}" data-module="{html.escape(module)}">
            <div class="resource-header" onclick="toggleResource(this)">
                <span class="resource-address">{html.escape(change.address)}</span>
                <span class="toggle-indicator"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="6 9 12 15 18 9"/></svg></span>
            </div>
            <div class="resource-details">
                {properties_html}
            </div>
        </div>
        """

    def _generate_property_changes(self, property_changes: List[PropertyChange], action: ActionType) -> str:
        """Generate HTML for property changes"""
    
        if not property_changes:
            return "<p>No detailed changes available.</p>"
        
        changes_html = ""
        for prop_change in property_changes:
            changes_html += self._generate_property_change(prop_change, action)
                
        return f"""
        <div class="property-changes">
            <table class="properties-table resizable-table">
                <colgroup>
                    <col class="col-prop">
                    <col class="col-before">
                    <col class="col-after">
                </colgroup>
                <thead>
                    <tr>
                        <th class="col-h-prop">Property</th>
                        <th class="col-h-before">Before<span class="col-resizer" title="Drag to resize"></span></th>
                        <th class="col-h-after">After</th>
                    </tr>
                </thead>
                <tbody>
                    {changes_html}
                </tbody>
            </table>
        </div>
        """
    
    def _generate_property_change(self, prop_change: PropertyChange, action: ActionType) -> str:
        """Generate HTML for a single property change"""
        from .analyzer import PlanAnalyzer
        analyzer = PlanAnalyzer()
        
        property_path = html.escape(prop_change.property_path)
        
        if prop_change.is_sensitive:
            before_value, after_value = "<sensitive>", "<sensitive>"
            before_mode = after_mode = "simple"
        else:
            before_value, before_mode = analyzer.format_value_for_display(prop_change.before_value)
            after_value,  after_mode  = analyzer.format_value_for_display(prop_change.after_value)

        known_after_apply = (
            action in (ActionType.UPDATE, ActionType.RECREATE)
            and prop_change.is_computed
        )

        # after
        if (before_mode == "empty" and after_mode == "empty"):
            return ""
        if (prop_change.is_addition and after_mode == "empty" and not known_after_apply):
            return ""
        if (prop_change.is_removal and before_mode == "empty"):
            return ""
        
        # Determine change type for styling
        change_class = ""
        if prop_change.is_addition:
            change_class = "addition"
            before_value = ""
        elif prop_change.is_removal:
            change_class = "removal"
            after_value = ""
        elif prop_change.is_modification:
            change_class = "modification"
        
        
        # Get base property name for filtering
        base_property = prop_change.property_path.split('.')[0]
        
        # Generate appropriate HTML based on content type
        def generate_value_html(value, mode, css_class):
            if mode == "empty":
                return f'<td class="{css_class}"></td>'
            elif mode == "simple":
                return f'<td class="{css_class}">{html.escape(value)}</td>'
            elif mode == "long_simple":
                return f'<td class="{css_class}"><div class="long-simple-value">{html.escape(value)}</div></td>'
            else:  # complex
                return f'<td class="{css_class}"><pre class="complex-value">{html.escape(value)}</pre></td>'
        
        before_html = generate_value_html(before_value, before_mode, "before-value")

        if known_after_apply:
            after_html = '<td class="after-value known-after-apply-cell"><em class="known-after-apply">known after apply</em></td>'
        else:
            after_html = generate_value_html(after_value, after_mode, "after-value")
        return f"""
        <tr class="property-change {change_class}" data-property="{html.escape(base_property)}">
            <td class="property-name">{property_path}</td>
            {before_html}
            {after_html}
        </tr>
        """
    
    def _generate_no_changes_content(self, analysis: PlanAnalysis) -> str:
        """Generate content for a plan with no changes — clean minimal layout."""
        return """
        <div class="state-card state-card--nochange">
            <div class="state-card__icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6L9 17l-5-5"/></svg>
            </div>
            <h2 class="state-card__title">No changes</h2>
            <p class="state-card__body">Your infrastructure matches the configuration.</p>
        </div>
        """

    def _generate_outputs_section(self, analysis: PlanAnalysis) -> str:
        """Generate the outputs section if outputs are available"""
        if not hasattr(analysis.plan, 'outputs') or not analysis.plan.outputs:
            return ""
        
        outputs_html = ""
        for name, output in analysis.plan.outputs.items():
            # Handle sensitive outputs
            if output.get('sensitive', False):
                details_html = """
                <div class="property-changes">
                    <table class="properties-table">
                        <thead>
                            <tr>
                                <th>Type</th>
                                <th>Value</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr class="property-change">
                                <td class="property-name">sensitive</td>
                                <td class="after-value"><pre>(sensitive value)</pre></td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                """
            else:
                value = output.get('value', '')
                from .analyzer import PlanAnalyzer
                analyzer = PlanAnalyzer()
                formatted_value, display_mode = analyzer.format_value_for_display(value)
                
                # Infer type from the actual value instead of relying on 'type' field
                output_type = self._infer_output_type(value, analysis.plan.configuration, name)
                
                # Generate appropriate HTML based on content type
                def generate_output_value_html(value, mode):
                    if mode == "empty":
                        return ""
                    elif mode == "simple":
                        return html.escape(value)
                    elif mode == "long_simple":
                        return f'<div class="long-simple-value">{html.escape(value)}</div>'
                    else:  # complex
                        return f'<pre class="complex-value">{html.escape(value)}</pre>'
                
                value_html = generate_output_value_html(formatted_value, display_mode)
                
                details_html = f"""
                <div class="property-changes">
                    <table class="properties-table">
                        <thead>
                            <tr>
                                <th>Type</th>
                                <th>Value</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr class="property-change">
                                <td class="property-name">{html.escape(output_type)}</td>
                                <td class="after-value">{value_html}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                """
            
            outputs_html += f"""
            <div class="resource-change read collapsed" data-action="read" data-address="output_{name}">
                <div class="resource-header" onclick="toggleResource(this)">
                    <span class="resource-address">{html.escape(name)}</span>
                    <span class="toggle-indicator"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="6 9 12 15 18 9"/></svg></span>
                </div>
                <div class="resource-details">
                    {details_html}
                </div>
            </div>
            """
        
        if not outputs_html:
            return ""
            
        return f"""
        <div class="resource-groups">
            <div class="resource-group" data-resource-type="outputs">
                <div class="group-header">
                    <h3>Outputs ({len(analysis.plan.outputs)} items)</h3>
                </div>
                <div class="group-resources">
                    {outputs_html}
                </div>
            </div>
        </div>
        """

    def _infer_output_type(self, value: Any, configuration: Dict[str, Any], output_name: str) -> str:
        """
        Infer the output type from the actual value and configuration.
        
        Args:
            value: The actual output value
            configuration: The terraform configuration section
            output_name: Name of the output
            
        Returns:
            str: The inferred type (e.g., 'string', 'number', 'object', 'list')
        """
        # First, try to get type from configuration if available
        try:
            config_outputs = configuration.get('root_module', {}).get('outputs', {})
            if output_name in config_outputs:
                output_config = config_outputs[output_name]
                if 'type' in output_config:
                    return output_config['type']
        except (KeyError, AttributeError):
            pass
        
        # If no type in configuration, infer from the value
        if value is None:
            return "null"
        elif isinstance(value, bool):
            return "bool"
        elif isinstance(value, int):
            return "number"
        elif isinstance(value, float):
            return "number"
        elif isinstance(value, str):
            return "string"
        elif isinstance(value, list):
            if len(value) == 0:
                return "list"
            # Check if it's a list of the same type
            first_type = type(value[0]).__name__
            if all(type(item).__name__ == first_type for item in value):
                if first_type == 'str':
                    return "list(string)"
                elif first_type in ['int', 'float']:
                    return "list(number)"
                elif first_type == 'bool':
                    return "list(bool)"
                elif first_type == 'dict':
                    return "list(object)"
            return "list"
        elif isinstance(value, dict):
            return "object"
        else:
            return "unknown"

    def _process_terraform_errors(self, error_output: Optional[str], plan_error_data: Optional[str]) -> Dict[str, Any]:
        """Process terraform error output and extract meaningful information"""
        
        errors = []
        warnings = []
        raw_output = ""
        
        # Process error output from stdin
        if error_output:
            raw_output += error_output + "\n"
            errors.extend(self._extract_errors_from_text(error_output))
            warnings.extend(self._extract_warnings_from_text(error_output))
        
        # Process plan error data
        if plan_error_data:
            raw_output += plan_error_data + "\n"
            try:
                # Try to parse as JSON first (might be terraform JSON error format)
                import json
                plan_json = json.loads(plan_error_data)
                if 'errors' in plan_json or 'diagnostics' in plan_json:
                    errors.extend(self._extract_errors_from_json(plan_json))
                    warnings.extend(self._extract_warnings_from_json(plan_json))
            except:
                # Not JSON, treat as text
                errors.extend(self._extract_errors_from_text(plan_error_data))
                warnings.extend(self._extract_warnings_from_text(plan_error_data))
        
        # If no specific errors found, at least show that terraform failed
        if not errors and not warnings:
            errors.append({
                'type': 'error',
                'message': 'The plan failed with exit code 1',
                'detail': 'No specific error details could be extracted from the output.'
            })
        
        return {
            'errors': errors,
            'warnings': warnings,
            'raw_output': raw_output.strip(),
            'has_errors': len(errors) > 0,
            'has_warnings': len(warnings) > 0
        }
    
    def _extract_errors_from_text(self, text: str) -> List[Dict[str, str]]:
        """Extract error messages from text output"""
        # First try to parse Terraform-style blocks
        terraform_blocks = self._parse_terraform_blocks(text)
        
        errors = []
        for block in terraform_blocks:
            if block['type'] == 'error':
                errors.append(block)
        
        # If no Terraform blocks found, fall back to generic parsing
        if not errors:
            lines = text.split('\n')
            for line in lines:
                line = line.strip()
                if any(keyword in line.lower() for keyword in ['error:', 'failed:', 'fatal:']):
                    errors.append({
                        'type': 'error',
                        'message': line,
                        'detail': ''
                    })
        
        return errors
    
    def _extract_warnings_from_text(self, text: str) -> List[Dict[str, str]]:
        """Extract warning messages from text output"""
        # First try to parse Terraform-style blocks
        terraform_blocks = self._parse_terraform_blocks(text)
        
        warnings = []
        for block in terraform_blocks:
            if block['type'] == 'warning':
                warnings.append(block)
        
        # If no Terraform blocks found, fall back to generic parsing
        if not warnings:
            lines = text.split('\n')
            for line in lines:
                line = line.strip()
                if any(keyword in line.lower() for keyword in ['warning:', 'warn:']):
                    warnings.append({
                        'type': 'warning',
                        'message': line,
                        'detail': ''
                    })
        
        return warnings
    
    def _extract_errors_from_json(self, plan_json: Dict[str, Any]) -> List[Dict[str, str]]:
        """Extract errors from terraform JSON error format"""
        errors = []
        
        # Handle terraform diagnostics format
        if 'diagnostics' in plan_json:
            for diagnostic in plan_json['diagnostics']:
                if diagnostic.get('severity') == 'error':
                    errors.append({
                        'type': 'error',
                        'message': diagnostic.get('summary', 'Unknown error'),
                        'detail': diagnostic.get('detail', '')
                    })
        
        # Handle generic errors array
        if 'errors' in plan_json:
            for error in plan_json['errors']:
                if isinstance(error, str):
                    errors.append({
                        'type': 'error',
                        'message': error,
                        'detail': ''
                    })
                elif isinstance(error, dict):
                    errors.append({
                        'type': 'error',
                        'message': error.get('message', str(error)),
                        'detail': error.get('detail', '')
                    })
        
        return errors
    
    def _extract_warnings_from_json(self, plan_json: Dict[str, Any]) -> List[Dict[str, str]]:
        """Extract warnings from terraform JSON error format"""
        warnings = []
        
        # Handle terraform diagnostics format
        if 'diagnostics' in plan_json:
            for diagnostic in plan_json['diagnostics']:
                if diagnostic.get('severity') == 'warning':
                    warnings.append({
                        'type': 'warning',
                        'message': diagnostic.get('summary', 'Unknown warning'),
                        'detail': diagnostic.get('detail', '')
                    })
        
        return warnings
    
    def _parse_terraform_blocks(self, text: str) -> List[Dict[str, str]]:
        """Parse Terraform-style error/warning blocks with box-drawing characters"""
        blocks = []
        lines = text.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].rstrip()
            
            # Look for start of Terraform block (╷)
            if line == '╷':
                block_lines = []
                i += 1
                
                # Collect all lines until we hit the end marker (╵) or end of text
                while i < len(lines):
                    current_line = lines[i].rstrip()
                    if current_line == '╵':
                        # End of block found
                        break
                    block_lines.append(current_line)
                    i += 1
                
                # Parse the collected block
                if block_lines:
                    parsed_block = self._parse_single_terraform_block(block_lines)
                    if parsed_block:
                        blocks.append(parsed_block)
            
            i += 1
        
        return blocks
    
    def _parse_single_terraform_block(self, block_lines: List[str]) -> Optional[Dict[str, str]]:
        """Parse a single Terraform error/warning block"""
        if not block_lines:
            return None
        
        # Remove box-drawing characters and clean up lines
        cleaned_lines = []
        for line in block_lines:
            # Remove leading │ and whitespace
            cleaned = line.lstrip('│ ').rstrip()
            if cleaned:  # Skip empty lines
                cleaned_lines.append(cleaned)
        
        if not cleaned_lines:
            return None
        
        # Determine if this is an error or warning
        first_line = cleaned_lines[0].lower()
        block_type = 'error'
        if 'warning:' in first_line:
            block_type = 'warning'
        elif 'error:' in first_line:
            block_type = 'error'
        
        # Extract the main message (first line after removing Error:/Warning: prefix)
        message = cleaned_lines[0]
        if ':' in message:
            message = message.split(':', 1)[1].strip()
        
        # Extract context information
        file_info = ""
        line_number = ""
        resource_info = ""
        detail_lines = []
        
        # Look for context lines (with, on, etc.)
        detail_start_idx = 1
        for i, line in enumerate(cleaned_lines[1:], 1):
            if line.strip().startswith('with '):
                resource_info = line.strip()
                detail_start_idx = i + 1
            elif line.strip().startswith('on '):
                # Extract file and line info: "on main.tf line 15, in ..."
                file_info = line.strip()
                if ' line ' in file_info:
                    parts = file_info.split(' line ')
                    if len(parts) >= 2:
                        file_path = parts[0].replace('on ', '').strip()
                        line_part = parts[1].split(',')[0].strip()
                        if line_part.isdigit():
                            line_number = line_part
                            file_info = f"{file_path}:{line_number}"
                detail_start_idx = i + 1
            elif line.strip() and not line.strip().startswith(('with ', 'on ')):
                break
        
        # Collect remaining lines as detail
        detail_lines = cleaned_lines[detail_start_idx:]
        detail = '\n'.join(detail_lines).strip()
        
        # Create structured error info
        result = {
            'type': block_type,
            'message': message,
            'detail': detail
        }
        
        # Add metadata if available
        if file_info:
            result['file'] = file_info
        if resource_info:
            result['resource'] = resource_info
        if line_number:
            result['line'] = line_number
        
        return result
    
    def _generate_error_html(self, processed_errors: Dict[str, Any]) -> str:
        """Generate complete HTML for error report"""

        sections = self.config.get("sections", {})
        show_header = sections.get("header", True)
        show_footer = sections.get("footer", True)
        
        theme_script = self._get_theme_script()
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>tofUI Error Report - {html.escape(self.plan_name)}</title>
    <style>
        {self._get_theme_vars_css()}
        {self._get_embedded_css()}
        {self._get_error_specific_css()}
    </style>
    {f'<script>{theme_script}</script>' if theme_script else ''}
</head>
<body>
    <div class="container">
        {self._generate_error_header() if show_header else ''}
        {self._generate_error_content(processed_errors)}
        {self._generate_footer() if show_footer else ''}
        {self._generate_watermark()}
    </div>
    
    <script>
        {self._generate_log_url_js()}
        {self._get_error_specific_javascript()}
    </script>
</body>
</html>"""
        
        return html_content
    
    def _generate_error_header(self) -> str:
        """Generate the error report header — neutral, no red gradient."""
        formatted_time = self.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")
        
        return f"""
        <div class="header">
            <div class="plan-name"><strong>{html.escape(self.plan_name)}</strong></div>
            <div class="meta-info"><strong>Generated:</strong> {formatted_time}</div>
        </div>
        """
    
    def _generate_error_content(self, processed_errors: Dict[str, Any]) -> str:
        """Generate the main error content section"""

        content = """
        <div class="state-card state-card--error">
            <div class="state-card__icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            </div>
            <h2 class="state-card__title">Plan failed</h2>
            <p class="state-card__body">There were errors during the infrastructure plan.</p>
        </div>
        """
        
        # Add errors section
        if processed_errors['has_errors']:
            content += self._generate_errors_section(processed_errors['errors'])
        
        # Terminal block for stack trace — always shown when raw_output is present
        if processed_errors['raw_output']:
            content += self._generate_error_terminal_section(processed_errors['raw_output'])
        
        return content
    
    def _generate_errors_section(self, errors: List[Dict[str, str]]) -> str:
        """Generate the errors section — clean error cards, no emoji."""
        errors_html = ""
        
        for i, error in enumerate(errors):
            error_detail = html.escape(error['detail']) if error['detail'] else ""
            error_message = html.escape(error['message'])
            file_info = html.escape(error.get('file', ''))
            resource_info = html.escape(error.get('resource', ''))

            meta_html = ""
            if file_info:
                meta_html += f'<span class="error-card__meta">{file_info}</span>'
            if resource_info:
                meta_html += f'<span class="error-card__meta">{resource_info}</span>'

            detail_html = ""
            if error_detail:
                detail_html = f'<pre class="error-card__trace">{error_detail}</pre>'
            
            errors_html += f"""
            <div class="error-card">
                <div class="error-card__header">
                    <span class="error-card__index">E{i+1}</span>
                    <span class="error-card__message">{error_message}</span>
                </div>
                {f'<div class="error-card__meta-row">{meta_html}</div>' if meta_html else ''}
                {detail_html}
            </div>
            """
        
        return f"""
        <div class="resource-groups">
            <div class="resource-group" data-resource-type="errors">
                <div class="group-header">
                    <h3>Errors ({len(errors)})</h3>
                </div>
                <div class="group-resources">
                    {errors_html}
                </div>
            </div>
        </div>
        """
    
    def _generate_warnings_section(self, warnings: List[Dict[str, str]]) -> str:
        """Generate the warnings section"""
        warnings_html = ""
        
        for warning in warnings:
            warning_detail = html.escape(warning['detail']) if warning['detail'] else ""
            warnings_html += f"""
            <div class="warning-item">
                <div class="warning-message">{html.escape(warning['message'])}</div>
                {f'<div class="warning-detail">{warning_detail}</div>' if warning_detail else ''}
            </div>
            """
        
        return f"""
        <div class="warnings-section">
            <h3>Warnings ({len(warnings)})</h3>
            <div class="warnings-container">
                {warnings_html}
            </div>
        </div>
        """
    
    def _generate_terminal_section_placeholder(self) -> str:
        """Generate terminal section with auto-loading logs.

        Returns nothing when no log was produced. The pane loads its content by
        fetching a log at runtime, so rendering it without one left the report
        showing "Log file not found in any expected location" — a failure
        message for something that was never asked for.
        """
        if not self.log_file_available:
            return ""
        return """
        <div class="terminal-section">
            <div class="terminal-header">
                <h3>Logs</h3>
                <button class="copy-btn" onclick="copyToClipboard('terminal-output')">Copy</button>
            </div>
            <div class="terminal-container">
                <pre id="terminal-output" class="terminal-output">Loading logs...</pre>
            </div>
        </div>
        """

    def _generate_error_terminal_section(self, raw_output: str) -> str:
        """Terminal block for error reports — always rendered when there is output."""
        escaped = html.escape(raw_output)
        return f"""
        <div class="terminal-section">
            <div class="terminal-header">
                <h3>Stack trace</h3>
                <button class="copy-btn" onclick="copyToClipboard('terminal-output')">Copy</button>
            </div>
            <div class="terminal-container">
                <pre id="terminal-output" class="terminal-output">{escaped}</pre>
            </div>
        </div>
        """
    
    def _generate_apply_html(self, apply_result) -> str:
        """Generate complete HTML for apply report"""

        sections = self.config.get("sections", {})
        show_header = sections.get("header", True)
        show_footer = sections.get("footer", True)
        
        theme_script = self._get_theme_script()
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>tofUI Apply Report - {html.escape(self.plan_name)}</title>
    <style>
        {self._get_theme_vars_css()}
        {self._get_embedded_css()}
        {self._get_apply_specific_css()}
    </style>
    {f'<script>{theme_script}</script>' if theme_script else ''}
</head>
<body>
    <div class="container">
        {self._generate_apply_header(apply_result) if show_header else ''}
        {self._generate_apply_content(apply_result)}
        {self._generate_terminal_section_placeholder()}
        {self._generate_footer() if show_footer else ''}
        {self._generate_watermark()}
    </div>
    
    <script>
        {self._generate_log_url_js()}
        {self._get_apply_specific_javascript()}
    </script>
</body>
</html>"""
        
        return html_content
    
    def _generate_apply_header(self, apply_result) -> str:
        """Generate the apply report header — neutral, no coloured gradient."""
        formatted_time = self.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")
        
        return f"""
        <div class="header">
            <div class="plan-name"><strong>{html.escape(self.plan_name)}</strong></div>
            <div class="meta-info"><strong>Generated:</strong> {formatted_time}</div>
        </div>
        """
    
    def _generate_apply_content(self, apply_result) -> str:
        """Generate the main apply content section"""
        from .apply_parser import ApplyResult
        
        content = ""
        
        # Add apply summary section
        content += self._generate_apply_summary_section(apply_result)
        
        # Add resource operations section if there are operations
        if apply_result.resource_operations:
            content += self._generate_resource_operations_section(apply_result.resource_operations)
        
        # Add errors section if there are errors
        if apply_result.errors:
            content += self._generate_apply_errors_section(apply_result.errors)
        
        # Add timing section if available
        if apply_result.timing and apply_result.timing.total_duration:
            content += self._generate_timing_section(apply_result.timing)
        
        return content
    
    def _generate_apply_summary_section(self, apply_result) -> str:
        """Generate the apply summary section — muted/neutral stat pills, no emoji."""
        from .apply_parser import ApplyResult
        
        SVG_CHECK = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6L9 17l-5-5"/></svg>'
        SVG_CROSS = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>'
        SVG_DASH  = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><line x1="5" y1="12" x2="19" y2="12"/></svg>'

        if apply_result.result == ApplyResult.SUCCESS_WITH_CHANGES:
            icon = SVG_CHECK
            title = "Apply complete"
            subtitle = "Infrastructure changes applied successfully."
            css_class = "state-card--nochange"
        elif apply_result.result == ApplyResult.SUCCESS_NO_CHANGES:
            icon = SVG_DASH
            title = "Nothing to do"
            subtitle = "No changes were required. Infrastructure is up to date."
            css_class = "state-card--nochange"
        elif apply_result.result == ApplyResult.FAILED:
            icon = SVG_CROSS
            title = "Apply failed"
            subtitle = "There were errors during the apply operation."
            css_class = "state-card--error"
        else:
            icon = SVG_DASH
            title = "Apply status unknown"
            subtitle = "The apply operation completed with unknown status."
            css_class = "state-card--nochange"
        
        stats_html = ""
        if apply_result.statistics:
            stats = apply_result.statistics
            if stats.resources_created > 0 or stats.resources_modified > 0 or stats.resources_destroyed > 0:
                stats_html = f"""
                <div class="summary-stats">
                    <div class="stat-item create">
                        <span class="stat-number">{stats.resources_created}</span>
                        <span class="stat-label">created</span>
                    </div>
                    <div class="stat-item update">
                        <span class="stat-number">{stats.resources_modified}</span>
                        <span class="stat-label">modified</span>
                    </div>
                    <div class="stat-item delete">
                        <span class="stat-number">{stats.resources_destroyed}</span>
                        <span class="stat-label">destroyed</span>
                    </div>
                </div>
                """
        
        return f"""
        <div class="state-card {css_class}">
            <div class="state-card__icon">{icon}</div>
            <h2 class="state-card__title">{title}</h2>
            <p class="state-card__body">{subtitle}</p>
            {stats_html}
        </div>
        """
    
    def _generate_resource_operations_section(self, resource_operations) -> str:
        """Generate the resource operations section"""
        if not resource_operations:
            return ""
        
        operations_html = ""
        for op in resource_operations:
            # Determine status label (text only, no emoji)
            status_labels = {
                "completed":   "done",
                "in_progress": "running",
                "failed":      "failed",
            }
            status_label = status_labels.get(op.status, op.status)
            status_class = op.status if op.status in status_labels else "unknown"
            
            duration_html = ""
            if op.duration:
                duration_html = f"<span class='operation-duration'>({op.duration})</span>"
            
            operations_html += f"""
            <div class="resource-change {op.action.value} collapsed" data-action="{op.action.value}" data-address="{html.escape(op.resource_address)}">
                <div class="resource-header" onclick="toggleResource(this)">
                    <span class="resource-address">{html.escape(op.resource_address)}</span>
                    <span class="action-label">{op.action.value}</span>
                    <span class="status-badge status-badge--{status_class}">{status_label}</span>
                    {duration_html}
                    <span class="toggle-indicator"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="6 9 12 15 18 9"/></svg></span>
                </div>
                <div class="resource-details">
                    <div class="operation-details">
                        <p><strong>Action:</strong> {op.action.value}</p>
                        <p><strong>Status:</strong> {op.status}</p>
                        {f"<p><strong>Duration:</strong> {op.duration}</p>" if op.duration else ""}
                    </div>
                </div>
            </div>
            """
        
        return f"""
        <div class="resource-groups">
            <div class="resource-group" data-resource-type="operations">
                <div class="group-header">
                    <h3>Resource operations ({len(resource_operations)})</h3>
                </div>
                <div class="group-resources">
                    {operations_html}
                </div>
            </div>
        </div>
        """
    
    def _generate_apply_errors_section(self, errors) -> str:
        """Generate the errors section for apply reports — matches error-card style."""
        if not errors:
            return ""
        
        errors_html = ""
        for i, error in enumerate(errors):
            error_message = html.escape(error.message) if hasattr(error, 'message') else html.escape(str(error))
            error_details = html.escape(error.details) if hasattr(error, 'details') and error.details else ""
            
            detail_html = ""
            if error_details:
                detail_html = f'<pre class="error-card__trace">{error_details}</pre>'
            
            errors_html += f"""
            <div class="error-card">
                <div class="error-card__header">
                    <span class="error-card__index">E{i+1}</span>
                    <span class="error-card__message">{error_message}</span>
                </div>
                {detail_html}
            </div>
            """
        
        return f"""
        <div class="resource-groups">
            <div class="resource-group" data-resource-type="errors">
                <div class="group-header">
                    <h3>Errors ({len(errors)})</h3>
                </div>
                <div class="group-resources">
                    {errors_html}
                </div>
            </div>
        </div>
        """
    
    def _generate_timing_section(self, timing) -> str:
        """Generate the timing section"""
        if not timing:
            return ""
        
        timing_html = ""
        if timing.total_duration:
            timing_html += f"<p><strong>Total duration:</strong> {timing.total_duration}</p>"
        if hasattr(timing, 'start_time') and timing.start_time:
            timing_html += f"<p><strong>Started:</strong> {timing.start_time}</p>"
        if hasattr(timing, 'end_time') and timing.end_time:
            timing_html += f"<p><strong>Completed:</strong> {timing.end_time}</p>"
        
        if not timing_html:
            return ""
        
        return f"""
        <div class="timing-section">
            <h3>Timing</h3>
            <div class="timing-details">
                {timing_html}
            </div>
        </div>
        """
    
    def _get_apply_specific_css(self) -> str:
        """Get CSS specific to apply reports"""
        return """
        .action-label {
            font-size: 0.8rem;
            background: var(--bg-muted);
            padding: 0.2rem 0.5rem;
            border-radius: var(--radius-sm);
            color: var(--text-secondary);
            margin-left: auto;
            margin-right: 0.5rem;
        }

        .status-badge {
            font-size: 0.75rem;
            padding: 0.15rem 0.5rem;
            border-radius: var(--radius-sm);
            font-family: 'JetBrains Mono', 'SF Mono', Monaco, Consolas, monospace;
        }
        .status-badge--completed  { background: var(--diff-add-bg); color: var(--diff-add-fg); }
        .status-badge--failed     { background: var(--diff-del-bg); color: var(--diff-del-fg); }
        .status-badge--in_progress{ background: var(--diff-mod-bg); color: var(--diff-mod-fg); }
        .status-badge--unknown    { background: var(--bg-muted);    color: var(--text-muted); }
        
        .operation-duration {
            font-size: 0.8rem;
            color: var(--text-muted);
            margin-left: 0.5rem;
        }
        
        .operation-details {
            font-family: 'JetBrains Mono', 'SF Mono', Monaco, Consolas, monospace;
            font-size: 0.9rem;
            padding: 1rem;
        }
        
        .timing-section {
            padding: 1.5rem 2rem;
            border-bottom: 1px solid var(--border);
        }
        
        .timing-section h3 {
            margin: 0 0 1rem 0;
            color: var(--text-secondary);
        }
        
        .timing-details {
            font-family: 'JetBrains Mono', 'SF Mono', Monaco, Consolas, monospace;
            font-size: 0.9rem;
            color: var(--text-muted);
        }
        """
    
    def _get_apply_specific_javascript(self) -> str:
        """Get JavaScript specific to apply reports"""
        return """
        // Initialize the apply page
        document.addEventListener('DOMContentLoaded', function() {
            // Initialize collapsible elements
            collapseAllResources();
            
            // Auto-load logs
            autoLoadLogs();
        });
        
        function autoLoadLogs() {
            // Try different log locations based on environment
            const baseName = window.location.pathname.split('/').pop().replace('.html', '');
            
            const logUrls = [
                // Explicit URL (e.g. a signed bucket URL) wins when provided
                ...(typeof TOFUI_LOG_URL !== 'undefined' && TOFUI_LOG_URL ? [TOFUI_LOG_URL] : []),
                `${baseName}.log`,  // Local: same directory
                `../logs/${baseName}.log`,  // GitHub Pages: logs folder
                `logs/${baseName}.log`  // Alternative GitHub Pages path
            ];
            
            tryLoadLog(logUrls, 0);
        }
        
        function filterTerraformLogs(logContent) {
            const lines = logContent.split('\\n');
            
            // Look for trigger lines to start from
            const triggerPatterns = [
                'Terraform will perform the following actions:',
                'Terraform planned the following actions, but then encountered a problem:',
                'No changes. Your infrastructure matches the configuration.'
            ];
            
            let startIndex = -1;
            for (let i = 0; i < lines.length; i++) {
                const line = lines[i].trim();
                for (const pattern of triggerPatterns) {
                    if (line.includes(pattern)) {
                        startIndex = i;
                        break;
                    }
                }
                if (startIndex !== -1) break;
            }
            
            // If no trigger found, return original content
            if (startIndex === -1) {
                return logContent;
            }
            
            // Return content starting from the trigger line
            return lines.slice(startIndex).join('\\n');
        }
        
        function tryLoadLog(urls, index) {
            if (index >= urls.length) {
                document.getElementById('terminal-output').textContent = 
                    'Error: Log file not found in any expected location\\nTried:\\n' + urls.join('\\n');
                return;
            }
            
            fetch(urls[index])
                .then(response => {
                    if (!response.ok) throw new Error('Not found');
                    return response.text();
                })
                .then(data => {
                    const filteredData = filterTerraformLogs(data);
                    document.getElementById('terminal-output').textContent = filteredData;
                })
                .catch(() => tryLoadLog(urls, index + 1));
        }
        
        function toggleResource(header) {
            const resourceChange = header.closest('.resource-change');
            resourceChange.classList.toggle('collapsed');
        }
        
        function collapseAllResources() {
            const resources = document.querySelectorAll('.resource-change');
            resources.forEach(resource => {
                resource.classList.add('collapsed');
            });
        }
        
        function copyToClipboard(elementId) {
            const element = document.getElementById(elementId);
            const text = element.textContent;
            
            navigator.clipboard.writeText(text).then(function() {
                // Show feedback
                const btn = document.querySelector('.copy-btn');
                const originalText = btn.textContent;
                btn.textContent = 'Copied!';
                btn.style.background = '#6c757d';
                
                setTimeout(function() {
                    btn.textContent = originalText;
                    btn.style.background = '#6c757d';
                }, 2000);
            }).catch(function(err) {
                console.error('Could not copy text: ', err);
                alert('Failed to copy to clipboard');
            });
        }
        """

    def _get_error_specific_css(self) -> str:
        """Get CSS specific to error reports — clean card layout, no red gradient."""
        return """
        /* Error card layout */
        .error-card {
            border: 1px solid var(--border);
            border-left: 4px solid var(--accent-delete);
            border-radius: var(--radius-md);
            margin-bottom: 1rem;
            overflow: hidden;
            background: var(--bg-surface);
        }

        .error-card__header {
            display: flex;
            align-items: baseline;
            gap: 0.75rem;
            padding: 0.85rem 1rem;
            background: var(--bg-muted);
            border-bottom: 1px solid var(--border);
        }

        .error-card__index {
            font-family: 'JetBrains Mono', 'SF Mono', Monaco, Consolas, monospace;
            font-size: 0.75rem;
            font-weight: 600;
            color: var(--accent-delete);
            flex-shrink: 0;
        }

        .error-card__message {
            font-family: 'JetBrains Mono', 'SF Mono', Monaco, Consolas, monospace;
            font-size: 0.9rem;
            color: var(--text-primary);
            word-break: break-word;
        }

        .error-card__meta-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            padding: 0.5rem 1rem;
            border-bottom: 1px solid var(--border);
            background: var(--bg-surface);
        }

        .error-card__meta {
            font-family: 'JetBrains Mono', 'SF Mono', Monaco, Consolas, monospace;
            font-size: 0.8rem;
            color: var(--text-muted);
            background: var(--bg-muted);
            padding: 0.1rem 0.4rem;
            border-radius: var(--radius-sm);
        }

        .error-card__trace {
            margin: 0;
            padding: 1rem;
            font-family: 'JetBrains Mono', 'SF Mono', Monaco, Consolas, monospace;
            font-size: 0.85rem;
            color: var(--terminal-fg);
            background: var(--terminal-bg);
            white-space: pre-wrap;
            word-break: break-word;
            overflow-x: auto;
            max-height: 300px;
            overflow-y: auto;
            line-height: 1.45;
        }
        """
    
    def _get_error_specific_javascript(self) -> str:
        """Get JavaScript specific to error reports"""
        return """
        // Initialize the error page
        document.addEventListener('DOMContentLoaded', function() {
            // Auto-load logs for error pages
            autoLoadLogs();
        });
        
        function autoLoadLogs() {
            // Try different log locations based on environment
            const baseName = window.location.pathname.split('/').pop().replace('.html', '');
            
            const logUrls = [
                // Explicit URL (e.g. a signed bucket URL) wins when provided
                ...(typeof TOFUI_LOG_URL !== 'undefined' && TOFUI_LOG_URL ? [TOFUI_LOG_URL] : []),
                `${baseName}.log`,  // Local: same directory
                `../logs/${baseName}.log`,  // GitHub Pages: logs folder
                `logs/${baseName}.log`  // Alternative GitHub Pages path
            ];
            
            tryLoadLog(logUrls, 0);
        }
        
        function filterTerraformLogs(logContent) {
            const lines = logContent.split('\\\\n');
            
            // Look for trigger lines to start from
            const triggerPatterns = [
                'Terraform will perform the following actions:',
                'Terraform planned the following actions, but then encountered a problem:',
                'No changes. Your infrastructure matches the configuration.'
            ];
            
            let startIndex = -1;
            for (let i = 0; i < lines.length; i++) {
                const line = lines[i].trim();
                for (const pattern of triggerPatterns) {
                    if (line.includes(pattern)) {
                        startIndex = i;
                        break;
                    }
                }
                if (startIndex !== -1) break;
            }
            
            // If no trigger found, return original content
            if (startIndex === -1) {
                return logContent;
            }
            
            // Return content starting from the trigger line
            return lines.slice(startIndex).join('\\\\n');
        }
        
        function tryLoadLog(urls, index) {
            if (index >= urls.length) {
                document.getElementById('terminal-output').textContent = 
                    'Error: Log file not found in any expected location\\\\nTried:\\\\n' + urls.join('\\\\n');
                return;
            }
            
            fetch(urls[index])
                .then(response => {
                    if (!response.ok) throw new Error('Not found');
                    return response.text();
                })
                .then(data => {
                    const filteredData = filterTerraformLogs(data);
                    document.getElementById('terminal-output').textContent = filteredData;
                })
                .catch(() => tryLoadLog(urls, index + 1));
        }
        
        function toggleResource(header) {
            const resourceChange = header.closest('.resource-change');
            resourceChange.classList.toggle('collapsed');
        }
        
        function copyToClipboard(elementId) {
            const element = document.getElementById(elementId);
            const text = element.textContent;
            
            navigator.clipboard.writeText(text).then(function() {
                // Show feedback
                const btn = document.querySelector('.copy-btn');
                const originalText = btn.textContent;
                btn.textContent = 'Copied!';
                btn.style.background = '#6c757d';
                
                setTimeout(function() {
                    btn.textContent = originalText;
                    btn.style.background = '#6c757d';
                }, 2000);
            }).catch(function(err) {
                console.error('Could not copy text: ', err);
                alert('Failed to copy to clipboard');
            });
        }
        """

    def _generate_footer(self) -> str:
        """Generate the footer — only rendered when there are action buttons to show."""
        import os
        build_url = os.environ.get('BUILD_URL', self.config.get('build_url', ''))
        debug_json = self.config.get('debug_json', False)

        buttons_html = ""
        if build_url:
            buttons_html += f'<a href="{html.escape(build_url)}" class="footer-btn" target="_blank">View Build</a>'

        if debug_json:
            json_url = self.config.get('json_url', '') or os.environ.get('TOFUI_JSON_URL', '')
            if not json_url:
                json_url = self.plan_name.replace('.html', '') + '.json'
            buttons_html += f'<a href="{html.escape(json_url)}" class="footer-btn" target="_blank">View JSON</a>'

        if not buttons_html:
            return ""

        return f"""
        <div class="footer">
            <div class="footer-buttons">{buttons_html}</div>
        </div>
        """

    def _generate_watermark(self) -> str:
        """Always-rendered credit line — links to GitHub, shows version."""
        version_text = f" v{__version__}" if __version__ and __version__ != "99.99" else ""
        return f"""
        <div class="tofui-watermark">
            <a href="https://github.com/65156/tofUI" target="_blank" rel="noopener">Generated by tofUI{version_text}</a>
        </div>
        """
    
    def _get_action_icon(self, action: ActionType) -> str:
        """Get icon for action type — returns empty string; action shown via CSS stripe colour."""
        return ""
    
    def _generate_javascript_data(self, analysis: PlanAnalysis) -> str:
        """Generate JavaScript data object"""
        data = {
            "summary": {
                "create": analysis.plan.summary.create,
                "update": analysis.plan.summary.update,
                "delete": analysis.plan.summary.delete,
                "has_changes": analysis.plan.summary.has_changes
            },
            "actions": [action.value for action in analysis.action_counts.keys()],
            "properties": list(analysis.all_property_names)
        }
        return json.dumps(data)
    
    def _get_embedded_css(self) -> str:
        """Get the embedded CSS styles — all colours via CSS custom properties."""
        return """
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

        *, *::before, *::after {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            font-size: 14px;
            line-height: 1.5;
            background-color: var(--bg-page);
            color: var(--text-primary);
            -webkit-font-smoothing: antialiased;
        }

        /* Scrollbars — Maze style */
        ::-webkit-scrollbar              { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track        { background: transparent; }
        ::-webkit-scrollbar-thumb        { background: var(--border); border-radius: 3px; }
        ::-webkit-scrollbar-thumb:hover  { background: var(--border-strong); }

        .container {
            width: 100%;
            background: var(--bg-surface);
            min-height: 100%;
            display: flex;
            flex-direction: column;
        }

        .header {
            background: var(--bg-header);
            color: #fff;
            padding: 1rem;
            text-align: center;
        }

        .known-after-apply {
            color: var(--accent-create);
            font-style: italic;
            opacity: 0.8;
        }

        .known-after-apply-cell {
            background: var(--diff-add-bg) !important;
            color: var(--diff-add-fg);
        }

        .plan-name {
            margin: 0;
            font-size: 1.2rem;
            font-weight: 300;
            margin-bottom: 0.3rem;
        }

        .meta-info {
            opacity: 0.9;
            font-size: 0.85rem;
            font-weight: 300;
        }

        /* State card — shared by no-changes, error, apply summary */
        .state-card {
            padding: 2rem;
            text-align: center;
            border-bottom: 1px solid var(--border);
        }
        .state-card__icon {
            display: flex;
            justify-content: center;
            margin-bottom: 0.75rem;
            color: var(--text-muted);
        }
        .state-card__icon svg {
            width: 2rem;
            height: 2rem;
        }
        .state-card__title {
            margin: 0 0 0.5rem 0;
            font-size: 1.3rem;
            font-weight: 600;
            color: var(--text-primary);
        }
        .state-card__body {
            margin: 0;
            color: var(--text-secondary);
            font-size: 0.95rem;
        }
        .state-card--nochange .state-card__icon { color: var(--accent-create); }
        .state-card--error   .state-card__icon { color: var(--accent-delete); }
        .state-card--error .state-card__title  { color: var(--accent-delete); }

        .summary-stats {
            display: flex;
            gap: 0.8rem;
            justify-content: center;
            margin-top: 1rem;
        }

        .stat-item {
            text-align: center;
            padding: 0.4rem 0.6rem;
            border-radius: var(--radius-sm);
            background: var(--bg-muted);
            min-width: 52px;
        }
        .stat-item.create {
            background: var(--diff-add-bg);
            color: var(--diff-add-fg);
        }
        .stat-item.update {
            background: var(--diff-mod-bg);
            color: var(--diff-mod-fg);
        }
        .stat-item.delete {
            background: var(--diff-del-bg);
            color: var(--diff-del-fg);
        }
        .stat-number {
            display: block;
            font-size: 1.2rem;
            font-weight: bold;
        }
        .stat-label {
            font-size: 0.54rem;
            text-transform: uppercase;
            letter-spacing: 0.3px;
        }

        /* ── Toolbar (single sticky row: search + chips + icon buttons) ──── */
        .toolbar {
            position: sticky;
            top: 0;
            z-index: 20;
            display: flex;
            flex-wrap: nowrap;
            align-items: center;
            gap: 0.5rem 0.6rem;
            padding: 0.45rem 0.8rem;
            background: var(--bg-surface);
            border-bottom: 1px solid var(--border);
            box-shadow: var(--shadow-sm);
        }
        .toolbar-search {
            position: relative;
            flex: 1 1 180px;
            min-width: 140px;
        }
        #resource-search {
            width: 100%;
            height: 30px;
            padding: 0 1.8rem 0 0.7rem;
            font-size: 0.82rem;
            border: 1px solid var(--border);
            border-radius: var(--radius-sm);
            outline: none;
            box-sizing: border-box;
            background: var(--bg-muted);
            color: var(--text-primary);
        }
        #resource-search:focus {
            border-color: var(--border-strong);
            background: var(--bg-surface);
        }
        .search-clear {
            position: absolute;
            right: 0.4rem;
            top: 50%;
            transform: translateY(-50%);
            border: none;
            background: transparent;
            cursor: pointer;
            color: var(--text-tertiary);
            font-size: 0.78rem;
            line-height: 1;
            padding: 0.2rem;
            display: none;
        }
        .search-clear.visible { display: block; }

        .chips { display: flex; flex-wrap: wrap; gap: 0.3rem; }
        .chip {
            display: inline-flex;
            align-items: center;
            gap: 0.3rem;
            height: 26px;
            padding: 0 0.6rem;
            border-radius: var(--radius-sm);
            border: 1px solid var(--border);
            border-left: 3px solid var(--border);
            background: var(--bg-surface);
            color: var(--text-tertiary);
            font-family: 'JetBrains Mono', 'SF Mono', Monaco, Consolas, monospace;
            font-size: 0.75rem;
            font-weight: 500;
            cursor: pointer;
            user-select: none;
            box-sizing: border-box;
            transition: background 0.1s ease, color 0.1s ease;
        }
        .chip:not(.active):hover { background: var(--bg-muted); }
        .chip.active { color: var(--text-primary); border-color: transparent; }
        .chip.active[data-action="delete"]  { background: var(--chip-delete-bg);  border-left-color: var(--accent-delete);  color: var(--chip-delete-fg); }
        .chip.active[data-action="replace"] { background: var(--chip-replace-bg); border-left-color: var(--accent-replace); color: var(--chip-replace-fg); }
        .chip.active[data-action="update"]  { background: var(--chip-update-bg);  border-left-color: var(--accent-update);  color: var(--chip-update-fg); }
        .chip.active[data-action="create"]  { background: var(--chip-create-bg);  border-left-color: var(--accent-create);  color: var(--chip-create-fg); }
        .chip-count {
            font-variant-numeric: tabular-nums;
            font-weight: 600;
            background: rgba(0,0,0,0.06);
            border-radius: var(--radius-sm);
            padding: 0 0.3rem;
        }
        .chip.active .chip-count { background: rgba(0,0,0,0.10); }

        /* Toolbar right cluster: count + icon buttons */
        .toolbar-right {
            margin-left: auto;
            display: flex;
            align-items: center;
            gap: 0.25rem;
            flex-shrink: 0;
        }
        .results-count {
            font-size: 0.75rem;
            color: var(--text-muted);
            white-space: nowrap;
            padding-right: 0.35rem;
        }
        .toolbar-icon-btn {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 26px;
            height: 26px;
            border: 1px solid var(--border);
            border-radius: var(--radius-sm);
            background: var(--bg-surface);
            color: var(--text-secondary);
            cursor: pointer;
            padding: 0;
            transition: background 0.1s ease, color 0.1s ease;
            flex-shrink: 0;
        }
        .toolbar-icon-btn:hover { background: var(--bg-muted); color: var(--text-primary); }
        .toolbar-icon-btn[aria-expanded="true"] { background: var(--bg-muted); color: var(--text-primary); }

        /* Properties dropdown panel */
        .props-panel {
            background: var(--bg-surface);
            border-bottom: 1px solid var(--border);
            padding: 0.55rem 0.8rem;
        }
        .props-panel[hidden] { display: none; }
        .props-panel__inner {
            display: flex;
            flex-wrap: wrap;
            gap: 0.3rem 0.8rem;
        }
        .filter-checkbox {
            display: flex;
            align-items: center;
            gap: 0.4rem;
            font-size: 0.8rem;
            cursor: pointer;
            color: var(--text-secondary);
        }
        .filter-checkbox input { margin: 0; cursor: pointer; }

        /* Filter active notice */
        .no-results {
            display: none;
            padding: 2rem 1rem;
            text-align: center;
            color: var(--text-muted);
            font-size: 0.85rem;
        }
        .no-results.visible { display: block; }
        .filter-notice {
            display: none;
            align-items: center;
            gap: 0.6rem;
            padding: 0.45rem 0.8rem;
            background: var(--diff-mod-bg);
            border-bottom: 1px solid var(--border);
            color: var(--diff-mod-fg);
            font-size: 0.78rem;
            font-weight: 500;
        }
        .filter-notice.visible { display: flex; }
        .filter-notice-icon { flex-shrink: 0; }
        .filter-reset {
            margin-left: auto;
            border: 1px solid var(--border-strong);
            background: transparent;
            color: var(--diff-mod-fg);
            padding: 0.2rem 0.5rem;
            border-radius: var(--radius-sm);
            font-size: 0.75rem;
            font-weight: 500;
            cursor: pointer;
        }
        .filter-reset:hover { opacity: 0.8; }
        .resource-change.highlighted {
            box-shadow: 0 0 0 2px var(--accent-replace);
            border-radius: var(--radius-md);
        }

        /* ── Resource groups ─────────────────────────────────────────────── */
        .resource-groups { padding: 0.6rem; }

        .resource-group {
            margin-bottom: 0.35rem;
            border: 1px solid var(--border);
            border-radius: var(--radius-md);
            overflow: hidden;
        }

        .group-header {
            background: var(--bg-muted);
            padding: 0.35rem 0.65rem;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .group-header h3 {
            margin: 0;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            color: var(--text-muted);
        }

        .group-resources { padding: 0.35rem; }

        .resource-change {
            border: 1px solid var(--border);
            border-radius: var(--radius-sm);
            margin-bottom: 0.3rem;
            overflow: hidden;
        }

        .resource-change.create  { border-left: 4px solid var(--accent-create); }
        .resource-change.update  { border-left: 4px solid var(--accent-update); }
        .resource-change.delete  { border-left: 4px solid var(--accent-delete); }
        .resource-change.replace { border-left: 4px solid var(--accent-replace); }
        .resource-change.read    { border-left: 4px solid var(--accent-read); }

        .resource-header {
            padding: 0.45rem 0.7rem;
            background: var(--bg-muted);
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            user-select: none;
            min-height: 34px;
        }
        .resource-header:hover { background: var(--border); }

        .resource-address {
            font-family: 'JetBrains Mono', 'SF Mono', Monaco, Consolas, monospace;
            font-size: 0.8rem;
            font-weight: 500;
            flex: 1;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .toggle-indicator {
            display: flex;
            align-items: center;
            flex-shrink: 0;
            width: 16px;
            height: 16px;
            color: var(--text-muted);
            transition: transform 0.2s;
        }
        .toggle-indicator svg { width: 16px; height: 16px; }

        .resource-change.collapsed .toggle-indicator {
            transform: rotate(-90deg);
        }

        .resource-details {
            padding: 0;
            border-top: 1px solid var(--border);
        }

        .resource-change.collapsed .resource-details { display: none; }

        /* Outputs Section */
        .outputs-section {
            padding: 1.5rem 2rem;
            border-top: 1px solid var(--border);
        }
        .outputs-section h2 {
            margin: 0 0 1rem 0;
            color: var(--text-secondary);
            font-size: 1.4rem;
        }

        .outputs-container {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 1rem;
        }

        .output-item {
            background: var(--bg-muted);
            border: 1px solid var(--border);
            border-radius: var(--radius-md);
            overflow: hidden;
        }
        .output-name {
            background: var(--border);
            padding: 0.75rem;
            font-family: 'JetBrains Mono', 'SF Mono', Monaco, Consolas, monospace;
            font-weight: 500;
            color: var(--text-secondary);
            border-bottom: 1px solid var(--border-strong);
        }
        .output-details { padding: 0.75rem; }
        .output-value {
            margin: 0 0 0.5rem 0;
            font-family: 'JetBrains Mono', 'SF Mono', Monaco, Consolas, monospace;
            font-size: 0.85rem;
            white-space: pre-wrap;
            word-break: break-all;
            overflow-x: auto;
        }
        .output-type {
            font-size: 0.8rem;
            color: var(--text-muted);
            display: block;
            margin-top: 0.5rem;
        }
        .sensitive-value {
            color: var(--text-muted);
            font-style: italic;
            background: var(--bg-muted);
            padding: 0.25rem 0.5rem;
            border-radius: var(--radius-sm);
        }

        .command-box {
            background: var(--bg-muted);
            border-radius: var(--radius-md);
            padding: 0.2rem;
            margin: 0.2rem 0;
        }
        .command {
            background: var(--terminal-bg);
            color: var(--terminal-fg);
            padding: 0.6rem 0.8rem;
            border-radius: var(--radius-sm);
            font-family: 'JetBrains Mono', 'SF Mono', Monaco, Consolas, monospace;
            margin-top: 0.75rem;
        }

        /* Terminal Section */
        .terminal-section {
            padding: 1.5rem 2rem;
            border-top: 1px solid var(--border);
        }
        .terminal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
        }
        .terminal-header h3 {
            margin: 0;
            color: var(--text-secondary);
        }
        .copy-btn {
            background: var(--text-muted);
            color: var(--bg-surface);
            border: none;
            padding: 0.4rem 0.85rem;
            border-radius: var(--radius-sm);
            cursor: pointer;
            font-size: 0.85rem;
        }
        .copy-btn:hover { opacity: 0.8; }
        .terminal-container {
            background: var(--terminal-bg);
            border-radius: var(--radius-lg);
            overflow: hidden;
            box-shadow: var(--shadow-md);
        }
        .terminal-output {
            background: var(--terminal-bg);
            color: var(--terminal-fg);
            padding: 1.5rem;
            margin: 0;
            font-family: 'JetBrains Mono', 'SF Mono', Monaco, Consolas, monospace;
            font-size: 0.9rem;
            line-height: 1.4;
            white-space: pre-wrap;
            word-break: break-word;
            overflow-x: auto;
            max-height: 400px;
            overflow-y: auto;
        }

        /* Properties diff table */
        .properties-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9rem;
            table-layout: fixed;
        }
        .properties-table th {
            background: var(--bg-muted);
            padding: 0.5rem 0.75rem;
            text-align: left;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            font-size: 0.75rem;
            font-weight: 600;
            color: var(--text-muted);
            border-bottom: 1px solid var(--border);
            position: relative;
        }

        /* Resizable Before/After columns */
        .resizable-table { --before-w: 37.5%; --after-w: 37.5%; }
        .resizable-table .col-prop { width: 25%; }
        .resizable-table .col-before { width: var(--before-w); }
        .resizable-table .col-after { width: var(--after-w); }
        .resource-change.delete .resizable-table { --before-w: 52%; --after-w: 23%; }
        .resource-change.create .resizable-table { --before-w: 23%; --after-w: 52%; }
        .resizable-table .before-value,
        .resizable-table .after-value { width: auto; max-width: none; }
        .col-resizer {
            position: absolute;
            top: 0;
            bottom: 0;
            right: -5px;
            width: 10px;
            height: 100%;
            cursor: col-resize;
            z-index: 2;
        }
        .col-resizer::after {
            content: "";
            position: absolute;
            left: 50%;
            top: 0;
            bottom: 0;
            height: 100%;
            width: 1px;
            transform: translateX(-50%);
            background: var(--border);
        }
        .col-resizer:hover::after,
        .col-resizer.dragging::after { background: var(--text-tertiary); }

        .properties-table td {
            padding: 0.5rem;
            border: none;
            vertical-align: top;
        }
        .properties-table tbody tr + tr td {
            border-top: 1px solid var(--border);
        }
        .property-name {
            font-family: 'JetBrains Mono', 'SF Mono', Monaco, Consolas, monospace;
            font-size: 0.8rem;
            font-weight: 500;
            color: var(--text-secondary);
            width: 25%;
        }
        .before-value, .after-value {
            font-family: 'JetBrains Mono', 'SF Mono', Monaco, Consolas, monospace;
            font-size: 0.8rem;
            width: 37.5%;
            max-width: 37.5%;
            min-width: 0;
        }
        .before-value pre, .after-value pre {
            margin: 0;
            font-family: 'JetBrains Mono', 'SF Mono', Monaco, Consolas, monospace;
            font-size: 0.8rem;
            white-space: pre-wrap;
            word-break: break-all;
            max-height: 200px;
            max-width: 100%;
            overflow: auto;
            background: var(--bg-muted);
            border: 1px solid var(--border);
            border-radius: var(--radius-sm);
            padding: 0.5rem;
        }
        .before-value pre.long-value, .after-value pre.long-value {
            font-size: 0.68rem;
            white-space: pre;
            word-break: normal;
        }
        .long-simple-value {
            font-family: 'JetBrains Mono', 'SF Mono', Monaco, Consolas, monospace;
            font-size: 0.8rem;
            white-space: nowrap;
            overflow-x: auto;
            overflow-y: hidden;
            max-width: 100%;
            padding: 0.5rem;
            border: 1px solid var(--border);
            border-radius: var(--radius-sm);
            background: var(--bg-muted);
        }
        .complex-value {
            margin: 0;
            font-family: 'JetBrains Mono', 'SF Mono', Monaco, Consolas, monospace;
            font-size: 0.8rem;
            white-space: pre-wrap;
            word-break: normal;
            max-height: 100px;
            min-height: 60px;
            max-width: 100%;
            overflow: auto;
            background: var(--bg-muted);
            border: 1px solid var(--border);
            border-radius: var(--radius-sm);
            padding: 0.5rem;
            line-height: 1.2;
        }

        /* Diff row colouring */
        .property-change.addition .after-value    { background: var(--diff-add-bg); color: var(--diff-add-fg); }
        .property-change.removal .before-value    { background: var(--diff-del-bg); color: var(--diff-del-fg); }
        .property-change.modification .before-value { background: var(--diff-mod-bg); color: var(--diff-mod-fg); }
        .property-change.modification .after-value  { background: var(--diff-add-bg); color: var(--diff-add-fg); }
        .resource-change.replace .property-change .before-value { background: var(--diff-del-bg); color: var(--diff-del-fg); }

        /* Footer */
        .footer {
            background: var(--bg-muted);
            padding: 1.5rem 2rem;
            color: var(--text-muted);
            font-size: 0.9rem;
            border-top: 1px solid var(--border);
            margin-top: auto;
        }
        .footer-content {
            display: flex;
            justify-content: space-between;
            align-items: center;
            max-width: 1200px;
            margin: 0 auto;
        }
        .footer-text { text-align: left; }
        .footer-buttons { display: flex; gap: 1rem; }
        .footer-btn {
            background: var(--bg-header);
            color: #fff;
            text-decoration: none;
            padding: 0.5rem 1rem;
            border-radius: var(--radius-sm);
            font-size: 0.9rem;
        }
        .footer-btn:hover { opacity: 0.85; }

        /* Watermark */
        .tofui-watermark {
            text-align: right;
            padding: 0.4rem 1.2rem 0.6rem;
            font-size: 0.75rem;
            font-style: italic;
        }
        .tofui-watermark a {
            color: var(--text-tertiary);
            text-decoration: none;
        }
        .tofui-watermark a:hover { text-decoration: underline; }

        .hidden { display: none !important; }

        @media (max-width: 600px) {
            .toolbar { flex-wrap: wrap; }
            .chips { order: 2; width: 100%; }
            .toolbar-right { order: 3; }
            .properties-table { font-size: 0.75rem; }
            .property-name { width: 30%; }
            .before-value, .after-value { width: 35%; }
        }
        """
    
    def _get_embedded_javascript(self) -> str:
        """Get the embedded JavaScript code"""
        return """
        // Initialize the application
        document.addEventListener('DOMContentLoaded', function() {
            initializeFilters();
            initializeSearch();
            initializeToggleButtons();
            initializeColumnResizers();

            // Initially collapse all resources
            collapseAllResources();

            // Apply filters + counts, then honor any deep link (#address)
            applyFilters();
            handleDeepLink();

            // Auto-load logs
            autoLoadLogs();
        });
        
        function initializeFilters() {
            // Property filters (hide properties)
            const propertyFilters = document.querySelectorAll('#property-filters input[type="checkbox"]');
            propertyFilters.forEach(filter => {
                filter.addEventListener('change', applyFilters);
            });
            
            // Always sort by action priority
            applySorting();
        }
        
        function initializeToggleButtons() {
            // Expand/collapse all — icon button; rotate SVG chevron to show state
            const toggleBtn = document.getElementById('toggle-all');
            const toggleIcon = document.getElementById('toggle-all-icon');
            let allExpanded = false;

            if (toggleBtn) {
                toggleBtn.addEventListener('click', function() {
                    allExpanded = !allExpanded;
                    if (allExpanded) {
                        expandAllResources();
                        toggleBtn.title = 'Collapse all';
                        toggleBtn.setAttribute('aria-label', 'Collapse all resources');
                        if (toggleIcon) toggleIcon.style.transform = 'rotate(180deg)';
                    } else {
                        collapseAllResources();
                        toggleBtn.title = 'Expand all';
                        toggleBtn.setAttribute('aria-label', 'Expand all resources');
                        if (toggleIcon) toggleIcon.style.transform = '';
                    }
                });
            }

            // Properties panel toggle
            const propsBtn = document.getElementById('props-btn');
            const propsPanel = document.getElementById('props-panel');
            if (propsBtn && propsPanel) {
                propsBtn.addEventListener('click', function() {
                    const open = propsPanel.hidden;
                    propsPanel.hidden = !open;
                    propsBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
                });
            }
        }
        
        function toggleResource(header) {
            const resourceChange = header.closest('.resource-change');
            resourceChange.classList.toggle('collapsed');
        }
        
        function expandAllResources() {
            const resources = document.querySelectorAll('.resource-change');
            resources.forEach(resource => {
                resource.classList.remove('collapsed');
            });
        }
        
        function collapseAllResources() {
            const resources = document.querySelectorAll('.resource-change');
            resources.forEach(resource => {
                resource.classList.add('collapsed');
            });
        }
        
        function initializeSearch() {
            const search = document.getElementById('resource-search');
            const clear = document.getElementById('search-clear');

            if (search) {
                search.addEventListener('input', function() {
                    if (clear) clear.classList.toggle('visible', search.value.length > 0);
                    applyFilters();
                });
            }
            if (clear) {
                clear.addEventListener('click', function() {
                    if (search) { search.value = ''; search.focus(); }
                    clear.classList.remove('visible');
                    applyFilters();
                });
            }

            // Action filter chips toggle their action on/off
            document.querySelectorAll('#action-chips .chip').forEach(chip => {
                chip.addEventListener('click', function() {
                    chip.classList.toggle('active');
                    applyFilters();
                });
            });

            // "Show all" reset in the filter notice
            const reset = document.getElementById('filter-reset');
            if (reset) reset.addEventListener('click', resetFilters);

            // Keyboard: '/' focuses search, Esc clears/blurs it
            document.addEventListener('keydown', function(e) {
                if (e.key === '/' && document.activeElement !== search) {
                    e.preventDefault();
                    if (search) search.focus();
                } else if (e.key === 'Escape' && document.activeElement === search) {
                    search.value = '';
                    if (clear) clear.classList.remove('visible');
                    applyFilters();
                    search.blur();
                }
            });
        }

        function getActiveActions() {
            const chips = document.querySelectorAll('#action-chips .chip');
            if (!chips.length) return null; // no chips => don't filter by action
            const active = new Set();
            chips.forEach(c => { if (c.classList.contains('active')) active.add(c.dataset.action); });
            return active;
        }

        function applyFilters() {
            // 1) Property-level hiding (the "Hide Properties" checkboxes)
            const hiddenProperties = Array.from(
                document.querySelectorAll('#property-filters input[type="checkbox"]:checked')
            ).map(input => input.value);

            const propertyRows = document.querySelectorAll('.property-change');
            propertyRows.forEach(row => {
                const property = row.dataset.property;
                const nameEl = row.querySelector('.property-name');
                const propertyPath = nameEl ? nameEl.textContent.trim() : '';

                let shouldHide = false;
                for (const hiddenProp of hiddenProperties) {
                    if (property === hiddenProp) { shouldHide = true; break; }
                    if (hiddenProp === 'tags_all' && (property === 'tags' || propertyPath.startsWith('tags.'))) { shouldHide = true; break; }
                    if (propertyPath.startsWith(hiddenProp + '.')) { shouldHide = true; break; }
                }
                row.style.display = shouldHide ? 'none' : 'table-row';
            });

            // 2) Resource-level filtering by search text + active action chips.
            //    Scoped to the main plan groups so the Outputs section (which
            //    reuses .resource-change with data-action="read") is untouched.
            const container = document.getElementById('resource-groups');
            const search = document.getElementById('resource-search');
            const q = (search ? search.value : '').trim().toLowerCase();
            const activeActions = getActiveActions();

            const resources = container ? Array.from(container.querySelectorAll('.resource-change')) : [];
            let visibleCount = 0;
            resources.forEach(res => {
                const haystack = (
                    (res.dataset.address || '') + ' ' +
                    (res.dataset.type || '') + ' ' +
                    (res.dataset.provider || '') + ' ' +
                    (res.dataset.module || '')
                ).toLowerCase();
                const matchesSearch = !q || haystack.indexOf(q) !== -1;
                const matchesAction = !activeActions || activeActions.has(res.dataset.action);
                const show = matchesSearch && matchesAction;
                res.style.display = show ? '' : 'none';
                if (show) visibleCount++;
            });

            // 3) Update group visibility + header counts to reflect what's visible
            const groups = container ? container.querySelectorAll('.resource-group') : [];
            groups.forEach(group => {
                const groupResources = Array.from(group.querySelectorAll('.resource-change'));
                const visible = groupResources.filter(r => r.style.display !== 'none').length;
                group.style.display = visible === 0 ? 'none' : 'block';
                const heading = group.querySelector('.group-header h3');
                if (heading && group.dataset.resourceType) {
                    const label = group.dataset.resourceType.charAt(0).toUpperCase() + group.dataset.resourceType.slice(1);
                    heading.textContent = `${label} (${visible} resource${visible === 1 ? '' : 's'})`;
                }
            });

            // 4) Results counter + empty state
            const rc = document.getElementById('results-count');
            if (rc) rc.textContent = `Showing ${visibleCount} of ${resources.length}`;
            const nr = document.getElementById('no-results');
            if (nr) nr.classList.toggle('visible', resources.length > 0 && visibleCount === 0);

            // 5) Inline warning when any filter is active
            const chips = document.querySelectorAll('#action-chips .chip');
            const filtersActive = q.length > 0 || (activeActions !== null && activeActions.size < chips.length);
            const notice = document.getElementById('filter-notice');
            if (notice) {
                notice.classList.toggle('visible', filtersActive);
                const nt = document.getElementById('filter-notice-text');
                if (nt) nt.textContent = `Filters are active — showing ${visibleCount} of ${resources.length} resources.`;
            }
        }

        function resetFilters() {
            const search = document.getElementById('resource-search');
            const clear = document.getElementById('search-clear');
            if (search) search.value = '';
            if (clear) clear.classList.remove('visible');
            document.querySelectorAll('#action-chips .chip').forEach(c => c.classList.add('active'));
            applyFilters();
        }

        function initializeColumnResizers() {
            document.querySelectorAll('.resizable-table .col-resizer').forEach(function(res) {
                res.addEventListener('mousedown', startColumnResize);
            });
        }

        function startColumnResize(e) {
            e.preventDefault();
            const resizer = e.currentTarget;
            const table = resizer.closest('table');
            const beforeCol = table.querySelector('col.col-before');
            const afterCol = table.querySelector('col.col-after');
            const beforeTh = table.querySelector('.col-h-before');
            const afterTh = table.querySelector('.col-h-after');
            if (!beforeCol || !afterCol || !beforeTh || !afterTh) return;

            const startX = e.clientX;
            const startBefore = beforeTh.offsetWidth;
            const pairWidth = startBefore + afterTh.offsetWidth;
            const tableWidth = table.getBoundingClientRect().width;
            const minW = 60;
            resizer.classList.add('dragging');
            document.body.style.userSelect = 'none';

            function onMove(ev) {
                let newBefore = startBefore + (ev.clientX - startX);
                newBefore = Math.max(minW, Math.min(pairWidth - minW, newBefore));
                beforeCol.style.width = (newBefore / tableWidth * 100) + '%';
                afterCol.style.width = ((pairWidth - newBefore) / tableWidth * 100) + '%';
            }
            function onUp() {
                resizer.classList.remove('dragging');
                document.body.style.userSelect = '';
                document.removeEventListener('mousemove', onMove);
                document.removeEventListener('mouseup', onUp);
            }
            document.addEventListener('mousemove', onMove);
            document.addEventListener('mouseup', onUp);
        }

        function handleDeepLink() {
            if (!location.hash || location.hash.length < 2) return;
            const addr = decodeURIComponent(location.hash.slice(1));
            let el = null;
            try {
                el = document.querySelector('.resource-change[data-address="' + (window.CSS && CSS.escape ? CSS.escape(addr) : addr) + '"]');
            } catch (e) { return; }
            if (!el) return;
            el.classList.remove('collapsed');
            el.scrollIntoView({ behavior: 'smooth', block: 'center' });
            el.classList.add('highlighted');
            setTimeout(() => el.classList.remove('highlighted'), 2200);
        }
        
        function applySorting() {
            const resourceGroupsContainer = document.getElementById('resource-groups');
            if (!resourceGroupsContainer) return; // No resources to sort
            
            const resourceGroups = Array.from(resourceGroupsContainer.querySelectorAll('.resource-group'));
            
            // Always use priority-based sorting: delete → replace → update → create
            const actionPriority = {
                'delete': 1,
                'replace': 2,
                'update': 3,
                'create': 4
            };
            
            // Collect all resources from all groups
            const allResources = [];
            resourceGroups.forEach(group => {
                const resources = Array.from(group.querySelectorAll('.resource-change'));
                resources.forEach(resource => {
                    allResources.push({
                        element: resource,
                        action: resource.dataset.action,
                        address: resource.dataset.address
                    });
                });
            });
            
            // Sort by action priority, then by address
            allResources.sort((a, b) => {
                const priorityA = actionPriority[a.action] || 999;
                const priorityB = actionPriority[b.action] || 999;
                
                if (priorityA !== priorityB) {
                    return priorityA - priorityB;
                }
                return a.address.localeCompare(b.address);
            });
            
            // Clear existing groups and create new action-based groups
            resourceGroupsContainer.innerHTML = '';
            
            const actionGroups = {};
            allResources.forEach(resource => {
                const action = resource.action;
                if (!actionGroups[action]) {
                    actionGroups[action] = [];
                }
                actionGroups[action].push(resource.element);
            });
            
            // Create HTML for action groups in priority order
            Object.keys(actionPriority).forEach(action => {
                if (actionGroups[action] && actionGroups[action].length > 0) {
                    const groupDiv = document.createElement('div');
                    groupDiv.className = 'resource-group';
                    groupDiv.dataset.resourceType = action;
                    
                    const count = actionGroups[action].length;
                    const actionTitle = action.charAt(0).toUpperCase() + action.slice(1);
                    
                    groupDiv.innerHTML = `
                        <div class="group-header">
                            <h3>${actionTitle} (${count} resources)</h3>
                        </div>
                        <div class="group-resources"></div>
                    `;
                    
                    const resourcesContainer = groupDiv.querySelector('.group-resources');
                    actionGroups[action].forEach(resourceElement => {
                        resourcesContainer.appendChild(resourceElement);
                    });
                    
                    resourceGroupsContainer.appendChild(groupDiv);
                }
            });
            
            // Re-apply filters after sorting
            applyFilters();
        }
        
        function autoLoadLogs() {
            // Try different log locations based on environment
            const baseName = window.location.pathname.split('/').pop().replace('.html', '');
            
            const logUrls = [
                // Explicit URL (e.g. a signed bucket URL) wins when provided
                ...(typeof TOFUI_LOG_URL !== 'undefined' && TOFUI_LOG_URL ? [TOFUI_LOG_URL] : []),
                `${baseName}.log`,  // Local: same directory
                `../logs/${baseName}.log`,  // GitHub Pages: logs folder
                `logs/${baseName}.log`  // Alternative GitHub Pages path
            ];
            
            tryLoadLog(logUrls, 0);
        }
        
        function filterTerraformLogs(logContent) {
            const lines = logContent.split('\\n');
            
            // Look for trigger lines to start from
            const triggerPatterns = [
                'Terraform will perform the following actions:',
                'Terraform planned the following actions, but then encountered a problem:',
                'No changes. Your infrastructure matches the configuration.'
            ];
            
            let startIndex = -1;
            for (let i = 0; i < lines.length; i++) {
                const line = lines[i].trim();
                for (const pattern of triggerPatterns) {
                    if (line.includes(pattern)) {
                        startIndex = i;
                        break;
                    }
                }
                if (startIndex !== -1) break;
            }
            
            // If no trigger found, return original content
            if (startIndex === -1) {
                return logContent;
            }
            
            // Return content starting from the trigger line
            return lines.slice(startIndex).join('\\n');
        }
        
        function tryLoadLog(urls, index) {
            if (index >= urls.length) {
                document.getElementById('terminal-output').textContent = 
                    'Error: Log file not found in any expected location\\nTried:\\n' + urls.join('\\n');
                return;
            }
            
            fetch(urls[index])
                .then(response => {
                    if (!response.ok) throw new Error('Not found');
                    return response.text();
                })
                .then(data => {
                    const filteredData = filterTerraformLogs(data);
                    document.getElementById('terminal-output').textContent = filteredData;
                })
                .catch(() => tryLoadLog(urls, index + 1));
        }
        
        function copyToClipboard(elementId) {
            const element = document.getElementById(elementId);
            const text = element.textContent;
            
            navigator.clipboard.writeText(text).then(function() {
                // Show feedback
                const btn = document.querySelector('.copy-btn');
                const originalText = btn.textContent;
                btn.textContent = 'Copied!';
                btn.style.background = '#6c757d';
                
                setTimeout(function() {
                    btn.textContent = originalText;
                    btn.style.background = '#6c757d';
                }, 2000);
            }).catch(function(err) {
                console.error('Could not copy text: ', err);
                alert('Failed to copy to clipboard');
            });
        }
        """
