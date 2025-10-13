"""
HTML Report Generator

Generates beautiful, interactive HTML reports from analyzed terraform plan data.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import html

from .analyzer import PlanAnalysis, AnalyzedResourceChange, PropertyChange, ActionType


class HTMLGenerator:
    """Generates interactive HTML reports from terraform plan analysis"""
    
    def __init__(self):
        self.plan_name = "Terraform Plan"
        self.timestamp = datetime.utcnow()
    
    def generate_report(
        self, 
        analysis: PlanAnalysis, 
        plan_name: Optional[str] = None,
        output_file: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate a complete HTML report from plan analysis"""
        
        self.plan_name = plan_name or "Terraform Plan"
        self.config = config or {}
        
        # Generate the complete HTML content
        html_content = self._generate_complete_html(analysis)
        
        # Write to file if specified
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
        
        return html_content
    
    def _generate_complete_html(self, analysis: PlanAnalysis) -> str:
        """Generate the complete HTML document"""
        
        # Generate data for JavaScript
        js_data = self._generate_javascript_data(analysis)
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Terraplan Report - {html.escape(self.plan_name)}</title>
    <style>
        {self._get_embedded_css()}
    </style>
</head>
<body>
    <div class="container">
        {self._generate_header(analysis)}
        {self._generate_summary(analysis)}
        {self._generate_filters(analysis)}
        {self._generate_resource_groups(analysis)}
        {self._generate_footer()}
    </div>
    
    <script>
        // Embedded plan data
        const planData = {js_data};
        
        {self._get_embedded_javascript()}
    </script>
</body>
</html>"""
    
    def _generate_header(self, analysis: PlanAnalysis) -> str:
        """Generate the report header"""
        formatted_time = self.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")
        
        return f"""
        <div class="header">
            <div class="plan-name"><strong>Plan:</strong> {html.escape(self.plan_name)}</div>
            <div class="meta-info"><strong>Terraform Version:</strong> {html.escape(analysis.plan.terraform_version)} • <strong>Generated:</strong> {formatted_time}</div>
        </div>
        """
    
    def _generate_summary(self, analysis: PlanAnalysis) -> str:
        """Generate the plan summary section"""
        summary = analysis.plan.summary
        
        if not summary.has_changes:
            return """
            <div class="summary no-changes">
                <h2>✅ No Changes</h2>
                <p>This plan contains no changes to your infrastructure.</p>
            </div>
            """
        
        return f"""
        <div class="summary">
            <div class="summary-stats">
                <div class="stat-item create">
                    <span class="stat-number">{summary.create}</span>
                    <span class="stat-label">to create</span>
                </div>
                <div class="stat-item update">
                    <span class="stat-number">{summary.update}</span>
                    <span class="stat-label">to update</span>
                </div>
                <div class="stat-item delete">
                    <span class="stat-number">{summary.delete}</span>
                    <span class="stat-label">to delete</span>
                </div>
            </div>
        </div>
        """
    
    def _generate_filters(self, analysis: PlanAnalysis) -> str:
        """Generate the filter controls"""
        if not analysis.has_changes:
            return ""
        
        # Get configuration settings
        config_actions = self.config.get("actions", {})
        config_properties = self.config.get("properties", {})
        config_display = self.config.get("display", {})
        
        default_selected_actions = config_actions.get("default_selected", ["create", "update", "delete"])
        available_properties = config_properties.get("available_to_hide", sorted(analysis.all_property_names))[:5]
        hidden_by_default = config_properties.get("hidden_by_default", [])
        
        # Get unique actions that exist in the plan
        available_actions = [action.value for action in analysis.action_counts.keys()]
        
        actions_html = ""
        for action in ["create", "update", "delete", "recreate", "read"]:
            if action in available_actions:
                checked = "checked" if action in default_selected_actions else ""
                actions_html += f"""
                <label class="filter-checkbox">
                    <input type="checkbox" value="{action}" {checked}> {action.title()}
                </label>
                """
        
        properties_html = ""
        for prop in available_properties:
            checked = "checked" if prop in hidden_by_default else ""
            properties_html += f"""
            <label class="filter-checkbox">
                <input type="checkbox" value="{html.escape(prop)}" {checked}> {html.escape(prop)}
            </label>
            """
        
        return f"""
        <div class="filters">
            <div class="filter-section">
                <h3>Hide Properties</h3>
                <div class="filter-group" id="property-filters">
                    {properties_html}
                </div>
            </div>
            <div class="filter-divider"></div>
            <div class="control-section">
                <button id="toggle-all" class="btn toggle-btn">Expand All</button>
            </div>
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
                <span class="group-summary">{counts_text}</span>
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
            properties_html = self._generate_property_changes(change.property_changes)
        
        return f"""
        <div class="resource-change {action_class}" data-action="{action_class}" data-address="{html.escape(change.address)}">
            <div class="resource-header" onclick="toggleResource(this)">
                <span class="action-icon">{action_icon}</span>
                <span class="resource-address">{html.escape(change.address)}</span>
                <span class="toggle-indicator">▼</span>
            </div>
            <div class="resource-details">
                {properties_html}
            </div>
        </div>
        """
    
    def _generate_property_changes(self, property_changes: List[PropertyChange]) -> str:
        """Generate HTML for property changes"""
        if not property_changes:
            return "<p>No detailed changes available.</p>"
        
        changes_html = ""
        for prop_change in property_changes:
            changes_html += self._generate_property_change(prop_change)
        
        return f"""
        <div class="property-changes">
            <table class="properties-table">
                <thead>
                    <tr>
                        <th>Property</th>
                        <th>Before</th>
                        <th>After</th>
                    </tr>
                </thead>
                <tbody>
                    {changes_html}
                </tbody>
            </table>
        </div>
        """
    
    def _generate_property_change(self, prop_change: PropertyChange) -> str:
        """Generate HTML for a single property change"""
        from .analyzer import PlanAnalyzer
        analyzer = PlanAnalyzer()
        
        property_path = html.escape(prop_change.property_path)
        
        if prop_change.is_sensitive:
            before_value = "<sensitive>"
            after_value = "<sensitive>"
        else:
            before_value = analyzer.format_value_for_display(prop_change.before_value)
            after_value = analyzer.format_value_for_display(prop_change.after_value)
        
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
        
        return f"""
        <tr class="property-change {change_class}" data-property="{html.escape(base_property)}">
            <td class="property-name">{property_path}</td>
            <td class="before-value"><pre>{html.escape(before_value)}</pre></td>
            <td class="after-value"><pre>{html.escape(after_value)}</pre></td>
        </tr>
        """
    
    def _generate_footer(self) -> str:
        """Generate the report footer"""
        # Get BUILD_URL from environment or config
        import os
        build_url = os.environ.get('BUILD_URL', self.config.get('build_url', ''))
        
        # Generate JSON filename (replace .html with .json)
        json_filename = self.plan_name.replace('.html', '') + '.json'
        
        buttons_html = ""
        if build_url:
            buttons_html += f'<a href="{build_url}" class="footer-btn" target="_blank">🔗 View Build</a>'
        
        buttons_html += f'<a href="{json_filename}" class="footer-btn" target="_blank">📄 View Raw JSON</a>'
        
        return f"""
        <div class="footer">
            <div class="footer-content">
                <div class="footer-text">
                    Generated by <strong>tofUI</strong> • 
                    Better OpenTofu & Terraform Plans
                </div>
                <div class="footer-buttons">
                    {buttons_html}
                </div>
            </div>
        </div>
        """
    
    def _get_action_icon(self, action: ActionType) -> str:
        """Get icon for action type"""
        icons = {
            ActionType.CREATE: "",
            ActionType.UPDATE: "", 
            ActionType.DELETE: "⚠️",
            ActionType.RECREATE: "⚠️",
            ActionType.READ: "",
            ActionType.NO_OP: "⭕"
        }
        return icons.get(action, "❓")
    
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
        """Get the embedded CSS styles"""
        return """
        * {
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 0;
            background-color: #f8f9fa;
            color: #333;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            min-height: 100vh;
        }
        
        .header {
            background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%);
            color: white;
            padding: 1rem;
            text-align: center;
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
        
        .summary {
            padding: 0.8rem;
            border-bottom: 1px solid #e9ecef;
        }
        
        .summary h2 {
            margin: 0 0 0.4rem 0;
            color: #495057;
        }
        
        .summary-stats {
            display: flex;
            gap: 0.8rem;
            justify-content: center;
        }
        
        .stat-item {
            text-align: center;
            padding: 0.4rem;
            border-radius: 4px;
            background: #f8f9fa;
            min-width: 48px;
        }
        
        .stat-item.create {
            background: #d4edda;
            color: #155724;
        }
        
        .stat-item.update {
            background: #fff3cd;
            color: #856404;
        }
        
        .stat-item.delete {
            background: #f8d7da;
            color: #721c24;
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
        
        .no-changes {
            text-align: center;
            color: #28a745;
        }
        
        .filters {
            padding: 1.5rem 2rem;
            background: #f8f9fa;
            border-bottom: 1px solid #e9ecef;
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            # gap: 2rem;
            # flex-wrap: wrap;
        }
        
        .filter-section h3 {
            margin: 0 0 0.5rem 0;
            font-size: 1rem;
            color: #495057;
        }
        
        .filter-group {
            display: flex;
            flex-direction: column;
            gap: 0.25rem;
        }
        
        .filter-checkbox {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.9rem;
            cursor: pointer;
        }
        
        .filter-checkbox input {
            margin: 0;
        }
        
        .btn {
            background: #6b7280;
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.9rem;
        }
        
        .btn:hover {
            background: #4b5563;
        }
        
        .sort-dropdown {
            padding: 0.5rem;
            border: 1px solid #ced4da;
            border-radius: 4px;
            font-size: 0.9rem;
            background: white;
            cursor: pointer;
        }
        
        .resource-groups {
            padding: 1.2rem;
        }
        
        .resource-group {
            margin-bottom: 0.4rem;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            overflow: hidden;
        }
        
        .group-header {
            background: #f8f9fa;
            padding: 0.6rem;
            border-bottom: 1px solid #e9ecef;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .group-header h3 {
            margin: 0;
            color: #495057;
        }
        
        .group-summary {
            font-size: 0.9rem;
            color: #6c757d;
        }
        
        .group-resources {
            padding: 1rem;
        }
        
        .resource-change {
            border: 1px solid #e9ecef;
            border-radius: 6px;
            margin-bottom: 1rem;
            overflow: hidden;
        }
        
        .resource-change.create {
            border-left: 16px solid #28a745;
        }
        
        .resource-change.update {
            border-left: 16px solid #ffc107;
        }
        
        .resource-change.delete {
            border-left: 16px solid #dc3545;
        }
        
        .resource-change.recreate {
            border-left: 16px solid #6f42c1;
        }
        
        .resource-header {
            padding: 1rem;
            background: #f8f9fa;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 0.75rem;
            user-select: none;
        }
        
        .resource-header:hover {
            background: #e9ecef;
        }
        
        .action-icon {
            font-size: 1.2rem;
        }
        
        .resource-address {
            font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, monospace;
            font-weight: 500;
            flex: 1;
        }
        
        .toggle-indicator {
            transition: transform 0.2s;
        }
        
        .resource-change.collapsed .toggle-indicator {
            transform: rotate(-90deg);
        }
        
        .resource-details {
            padding: 1rem;
            border-top: 1px solid #e9ecef;
        }
        
        .resource-change.collapsed .resource-details {
            display: none;
        }
        
        .properties-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9rem;
        }
        
        .properties-table th {
            background: #f8f9fa;
            padding: 0.75rem;
            text-align: left;
            font-weight: 600;
            color: #495057;
            border-bottom: 2px solid #dee2e6;
        }
        
        .properties-table td {
            padding: 0.75rem;
            border-bottom: 1px solid #dee2e6;
            vertical-align: top;
        }
        
        .property-name {
            font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, monospace;
            font-weight: 500;
            color: #495057;
            width: 25%;
        }
        
        .before-value, .after-value {
            width: 37.5%;
        }
        
        .before-value pre, .after-value pre {
            margin: 0;
            font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, monospace;
            font-size: 0.85rem;
            white-space: pre-wrap;
            word-break: break-all;
        }
        
        .property-change.addition .after-value {
            background: #d4edda;
            color: #155724;
        }
        
        .property-change.removal .before-value {
            background: #f8d7da;
            color: #721c24;
        }
        
        .property-change.modification .before-value {
            background: #fff3cd;
            color: #856404;
        }
        
        .property-change.modification .after-value {
            background: #d4edda;
            color: #155724;
        }
        
        .filter-divider {
            width: 1px;
            background: #dee2e6;
            height: 4rem;
            margin: 0 1rem;
        }
        
        .control-section {
            display: flex;
            align-items: flex-start;
            padding-top: 0.25rem;
        }
        
        .resource-change.recreate .property-change .before-value {
            background: #f8d7da;
            color: #721c24;
        }
        
        .footer {
            background: #f8f9fa;
            padding: 1.5rem 2rem;
            color: #6c757d;
            font-size: 0.9rem;
            border-top: 1px solid #e9ecef;
        }
        
        .footer-content {
            display: flex;
            justify-content: space-between;
            align-items: center;
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .footer-text {
            text-align: left;
        }
        
        .footer-buttons {
            display: flex;
            gap: 1rem;
        }
        
        .footer-btn {
            background: #6b7280;
            color: white;
            text-decoration: none;
            padding: 0.5rem 1rem;
            border-radius: 4px;
            font-size: 0.9rem;
            transition: background-color 0.2s;
        }
        
        .footer-btn:hover {
            background: #4b5563;
        }
        
        .hidden {
            display: none !important;
        }
        
        @media (max-width: 768px) {
            .header {
                padding: 1.5rem;
            }
            
            .header h1 {
                font-size: 2rem;
            }
            
            .summary-stats {
                flex-direction: column;
                align-items: center;
            }
            
            .filters {
                flex-direction: column;
                gap: 1rem;
            }
            
            .resource-groups {
                padding: 1rem;
            }
            
            .properties-table {
                font-size: 0.8rem;
            }
            
            .property-name {
                width: 30%;
            }
            
            .before-value, .after-value {
                width: 35%;
            }
        }
        """
    
    def _get_embedded_javascript(self) -> str:
        """Get the embedded JavaScript code"""
        return """
        // Initialize the application
        document.addEventListener('DOMContentLoaded', function() {
            initializeFilters();
            initializeToggleButtons();
            
            // Initially collapse all resources
            collapseAllResources();
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
            const toggleBtn = document.getElementById('toggle-all');
            
            if (toggleBtn) {
                toggleBtn.addEventListener('click', function() {
                    const isCurrentlyExpanded = toggleBtn.textContent.trim() === 'Collapse All';
                    
                    if (isCurrentlyExpanded) {
                        collapseAllResources();
                        toggleBtn.textContent = 'Expand All';
                    } else {
                        expandAllResources();
                        toggleBtn.textContent = 'Collapse All';
                    }
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
        
        function applyFilters() {
            // Get selected action filters
            const selectedActions = Array.from(
                document.querySelectorAll('#action-filters input[type="checkbox"]:checked')
            ).map(input => input.value);
            
            // Get selected property filters (properties to hide)
            const hiddenProperties = Array.from(
                document.querySelectorAll('#property-filters input[type="checkbox"]:checked')
            ).map(input => input.value);
            
            // Filter resources by action
            const resources = document.querySelectorAll('.resource-change');
            resources.forEach(resource => {
                const action = resource.dataset.action;
                if (selectedActions.length === 0 || selectedActions.includes(action)) {
                    resource.style.display = 'block';
                } else {
                    resource.style.display = 'none';
                }
            });
            
            // Filter properties with smart matching
            const propertyRows = document.querySelectorAll('.property-change');
            propertyRows.forEach(row => {
                const property = row.dataset.property;
                const propertyPath = row.querySelector('.property-name').textContent.trim();
                
                let shouldHide = false;
                for (const hiddenProp of hiddenProperties) {
                    // Direct match
                    if (property === hiddenProp) {
                        shouldHide = true;
                        break;
                    }
                    // Pattern matching for nested properties
                    if (hiddenProp === 'tags_all' && (property === 'tags' || propertyPath.startsWith('tags.'))) {
                        shouldHide = true;
                        break;
                    }
                    // Generic pattern matching for other nested properties
                    if (propertyPath.startsWith(hiddenProp + '.')) {
                        shouldHide = true;
                        break;
                    }
                }
                
                if (shouldHide) {
                    row.style.display = 'none';
                } else {
                    row.style.display = 'table-row';
                }
            });
            
            // Hide resource groups that have no visible resources
            const resourceGroups = document.querySelectorAll('.resource-group');
            resourceGroups.forEach(group => {
                const visibleResources = group.querySelectorAll('.resource-change:not([style*="display: none"])');
                if (visibleResources.length === 0) {
                    group.style.display = 'none';
                } else {
                    group.style.display = 'block';
                }
            });
        }
        
        function applySorting() {
            const resourceGroupsContainer = document.getElementById('resource-groups');
            const resourceGroups = Array.from(resourceGroupsContainer.querySelectorAll('.resource-group'));
            
            // Always use priority-based sorting: delete → recreate → update → create → read
            const actionPriority = {
                'delete': 1,
                'recreate': 2, 
                'update': 3,
                'create': 4,
                'read': 5
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
                            <span class="group-summary">${count} ${action}</span>
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
        """
