"""
HTML Report Generator

Generates beautiful, interactive HTML reports from analyzed terraform plan data.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import html

from .parser import ActionType  # at top of file if not already imported
from .analyzer import PlanAnalysis, AnalyzedResourceChange, PropertyChange, ActionType


class HTMLGenerator:
    """Generates interactive HTML reports from terraform plan analysis"""
    
    def __init__(self):
        self.plan_name = "tofUI Plan"
        self.timestamp = datetime.utcnow()
    
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
        
        # Generate the complete HTML content for apply report
        html_content = self._generate_apply_html(apply_result)
        
        # Write to file if specified
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
        
        return html_content
    
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
        
        # Determine theme class based on plan status
        theme_class = ""
        if not analysis.plan.summary.has_changes:
            theme_class = "theme-green"
        else:
            theme_class = "theme-yellow"
            
        # Add terminal section for logs
        terminal_section = self._generate_terminal_section_placeholder()
            
        return f"""<!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>tofUI - {html.escape(self.plan_name)}</title>
        <style>
            {self._get_embedded_css()}
            {self._get_theme_css()}
        </style>
    </head>
    <body class="{theme_class}">
        <div class="container">
            {self._generate_header(analysis)}
            {content_body}
            {outputs_section}
            {terminal_section}
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
            <div class="plan-name"><strong>{html.escape(self.plan_name)}</strong></div>
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
                    <span class="stat-label">add</span>
                </div>
                <div class="stat-item update">
                    <span class="stat-number">{summary.update}</span>
                    <span class="stat-label">change</span>
                </div>
                <div class="stat-item delete">
                    <span class="stat-number">{summary.delete}</span>
                    <span class="stat-label">destroy</span>
                </div>
            </div>
        </div>
        """
    
    def _generate_filters(self, analysis: PlanAnalysis) -> str:
        """Generate the filter controls"""
        if not analysis.has_changes:
            return ""
        
        # Get configuration settings
        config_properties = self.config.get("properties", {})
        config_display = self.config.get("display", {})
        
        available_properties = config_properties.get("available_to_hide", sorted(analysis.all_property_names))[:5]
        hidden_by_default = config_properties.get("hidden_by_default", [])
        
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
        
        return f"""
        <div class="resource-change {action_class}" data-action="{action_class}" data-address="{html.escape(change.address)}">
            <div class="resource-header" onclick="toggleResource(this)">
                <span class="resource-address">{html.escape(change.address)}</span>
                <span class="toggle-indicator">▼</span>
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
        """Generate content for a plan with no changes"""
        summary = analysis.plan.summary
        resource_count = summary.resources_total or 0
        
        return f"""
        <div class="no-changes-summary no-changes">
            <div class="no-changes-icon">✅</div>
            <h2>No Changes Detected</h2>
            <p>Your infrastructure matches the configuration.</p>
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
                    <span class="toggle-indicator">▼</span>
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
        
        # Generate the complete HTML content
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>tofUI Error Report - {html.escape(self.plan_name)}</title>
    <style>
        {self._get_embedded_css()}
        {self._get_error_specific_css()}
    </style>
</head>
<body>
    <div class="container">
        {self._generate_error_header()}
        {self._generate_error_content(processed_errors)}
        {self._generate_footer()}
    </div>
    
    <script>
        {self._get_error_specific_javascript()}
    </script>
</body>
</html>"""
        
        return html_content
    
    def _generate_error_header(self) -> str:
        """Generate the error report header"""
        formatted_time = self.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")
        
        return f"""
        <div class="header error-header">
            <div class="plan-name"><strong>{html.escape(self.plan_name)}</strong></div>
            <div class="meta-info"><strong>Generated:</strong> {formatted_time}</div>
        </div>
        """
    
    def _generate_error_content(self, processed_errors: Dict[str, Any]) -> str:
        """Generate the main error content section"""
        
        content = """
        <div class="error-summary">
            <div class="error-icon">❌</div>
            <h2>Issues Detected</h2>
            <p>There were fatal errors during your infrastructure plan.</p>
        </div>
        """
        
        # Add errors section
        if processed_errors['has_errors']:
            content += self._generate_errors_section(processed_errors['errors'])
        
        # Note: Warnings are not displayed in error reports as requested
        # if processed_errors['has_warnings']:
        #     content += self._generate_warnings_section(processed_errors['warnings'])
        
        # Add raw output section
        if processed_errors['raw_output']:
            content += self._generate_terminal_output_section(processed_errors['raw_output'])
        
        return content
    
    def _generate_errors_section(self, errors: List[Dict[str, str]]) -> str:
        """Generate the errors section with expandable format"""
        errors_html = ""
        
        for i, error in enumerate(errors):
            error_detail = html.escape(error['detail']) if error['detail'] else ""
            error_message = html.escape(error['message'])
            
            # Create expandable error items like resource deletions (no emoji)
            details_html = ""
            if error_detail:
                details_html = f"""
                <div class="property-changes">
                    <table class="properties-table">
                        <thead>
                            <tr>
                                <th>Error Details</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr class="property-change">
                                <td class="error-detail-content">{error_detail}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                """
            else:
                details_html = "<p>No additional details available.</p>"
            
            errors_html += f"""
            <div class="resource-change delete collapsed" data-action="delete" data-address="error_{i+1}">
                <div class="resource-header" onclick="toggleResource(this)">
                    <span class="resource-address">Error {i+1}: {error_message}</span>
                    <span class="toggle-indicator">▼</span>
                </div>
                <div class="resource-details">
                    {details_html}
                </div>
            </div>
            """
        
        return f"""
        <div class="resource-groups">
            <div class="resource-group" data-resource-type="errors">
                <div class="group-header">
                    <h3>Errors ({len(errors)} items)</h3>
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
            <h3>⚠️ Warnings ({len(warnings)})</h3>
            <div class="warnings-container">
                {warnings_html}
            </div>
        </div>
        """
    
    def _generate_terminal_section_placeholder(self) -> str:
        """Generate terminal section with auto-loading logs"""
        return f"""
        <div class="terminal-section">
            <div class="terminal-header">
                <h3>Logs</h3>
                <button class="copy-btn" onclick="copyToClipboard('terminal-output')">Copy to Clipboard</button>
            </div>
            <div class="terminal-container">
                <pre id="terminal-output" class="terminal-output">Loading logs...</pre>
            </div>
        </div>
        """

    def _generate_terminal_output_section(self, raw_output: str) -> str:
        """Generate the terminal-style output section with auto-loading"""
        return f"""
        <div class="terminal-section">
            <div class="terminal-header">
                <h3>Logs</h3>
                <button class="copy-btn" onclick="copyToClipboard('terminal-output')">Copy to Clipboard</button>
            </div>
            <div class="terminal-container">
                <pre id="terminal-output" class="terminal-output">Loading logs...</pre>
            </div>
        </div>
        """
    
    def _get_theme_css(self) -> str:
        """Get theme-specific CSS for different report types"""
        return """
        /* Yellow Theme (Changes) */
        .theme-yellow .header {
            background: linear-gradient(135deg, #ffda18 0%, #f4c430 100%);
            color: #333;
        }
        
        .theme-yellow .filters {
            background: #fffbf0;
            border-bottom: 1px solid #ffda18;
        }
        
        .theme-yellow .btn {
            background: #ffda18;
            color: #333;
        }
        
        .theme-yellow .btn:hover {
            background: #f4c430;
        }
        
        .theme-yellow .footer-btn {
            background: #ffda18;
            color: #333;
        }
        
        .theme-yellow .footer-btn:hover {
            background: #f4c430;
        }
        
        /* Green Theme (No Changes) */
        .theme-green .header {
            background: linear-gradient(135deg, #28a745 0%, #218838 100%);
        }
        
        .theme-green .command-box {
            background: #d4edda;
            border: 1px solid #c3e6cb;
        }
        
        .theme-green .output-item {
            border: 1px solid #c3e6cb;
        }
        
        .theme-green .output-name {
            background: #d4edda;
            border-bottom: 1px solid #c3e6cb;
        }
        
        .theme-green .footer-btn {
            background: #28a745;
        }
        
        .theme-green .footer-btn:hover {
            background: #218838;
        }
        
        .load-logs-btn {
            background: #6c757d;
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.9rem;
            margin-right: 0.5rem;
        }
        
        .theme-yellow .load-logs-btn {
            background: #ffda18;
            color: #333;
        }
        
        .theme-green .load-logs-btn {
            background: #28a745;
            color: white;
        }
        """
    
    def _generate_apply_html(self, apply_result) -> str:
        """Generate complete HTML for apply report"""
        from .apply_parser import ApplyResult
        
        # Determine theme based on apply result
        theme_class = ""
        if apply_result.result == ApplyResult.SUCCESS_WITH_CHANGES:
            theme_class = "theme-green"
        elif apply_result.result == ApplyResult.SUCCESS_NO_CHANGES:
            theme_class = "theme-green"
        elif apply_result.result == ApplyResult.FAILED:
            theme_class = "theme-red"
        else:
            theme_class = "theme-yellow"
        
        # Generate the complete HTML content
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>tofUI Apply Report - {html.escape(self.plan_name)}</title>
    <style>
        {self._get_embedded_css()}
        {self._get_apply_specific_css()}
    </style>
</head>
<body class="{theme_class}">
    <div class="container">
        {self._generate_apply_header(apply_result)}
        {self._generate_apply_content(apply_result)}
        {self._generate_terminal_section_placeholder()}
        {self._generate_footer()}
    </div>
    
    <script>
        {self._get_apply_specific_javascript()}
    </script>
</body>
</html>"""
        
        return html_content
    
    def _generate_apply_header(self, apply_result) -> str:
        """Generate the apply report header"""
        from .apply_parser import ApplyResult
        formatted_time = self.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")
        
        return f"""
        <div class="header apply-header">
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
        """Generate the apply summary section"""
        from .apply_parser import ApplyResult
        
        if apply_result.result == ApplyResult.SUCCESS_WITH_CHANGES:
            icon = "🎉"
            title = "Apply Success"
            subtitle = "Infrastructure changes have been applied successfully."
            css_class = "success-summary"
        elif apply_result.result == ApplyResult.SUCCESS_NO_CHANGES:
            icon = "✅"
            title = "No Changes"
            subtitle = "No changes were required. Infrastructure is up to date."
            css_class = "no-changes-summary"
        elif apply_result.result == ApplyResult.FAILED:
            icon = "❌"
            title = "Apply Failed"
            subtitle = "There were errors during the apply operation."
            css_class = "error-summary"
        else:
            icon = "❓"
            title = "Apply Status Unknown"
            subtitle = "The apply operation completed with unknown status."
            css_class = "unknown-summary"
        
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
        <div class="apply-summary {css_class}">
            <h2>{icon} {title}</h2>
            <p>{subtitle}</p>
            {stats_html}
        </div>
        """
    
    def _generate_resource_operations_section(self, resource_operations) -> str:
        """Generate the resource operations section"""
        if not resource_operations:
            return ""
        
        operations_html = ""
        for op in resource_operations:
            # Determine status styling
            if op.status == "completed":
                status_class = "completed"
                status_icon = "✅"
            elif op.status == "in_progress":
                status_class = "in_progress"
                status_icon = "⏳"
            elif op.status == "failed":
                status_class = "failed"
                status_icon = "❌"
            else:
                status_class = "unknown"
                status_icon = "❓"
            
            # Format duration
            duration_html = ""
            if op.duration:
                duration_html = f"<span class='operation-duration'>({op.duration})</span>"
            
            operations_html += f"""
            <div class="resource-change {op.action.value} collapsed" data-action="{op.action.value}" data-address="{html.escape(op.resource_address)}">
                <div class="resource-header" onclick="toggleResource(this)">
                    <span class="status-icon {status_class}">{status_icon}</span>
                    <span class="resource-address">{html.escape(op.resource_address)}</span>
                    <span class="action-label">{op.action.value}</span>
                    {duration_html}
                    <span class="toggle-indicator">▼</span>
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
                    <h3>Resource Operations ({len(resource_operations)} items)</h3>
                </div>
                <div class="group-resources">
                    {operations_html}
                </div>
            </div>
        </div>
        """
    
    def _generate_apply_errors_section(self, errors) -> str:
        """Generate the errors section for apply reports"""
        if not errors:
            return ""
        
        errors_html = ""
        for i, error in enumerate(errors):
            error_message = html.escape(error.message) if hasattr(error, 'message') else html.escape(str(error))
            error_details = html.escape(error.details) if hasattr(error, 'details') and error.details else ""
            
            details_html = ""
            if error_details:
                details_html = f"""
                <div class="property-changes">
                    <table class="properties-table">
                        <thead>
                            <tr>
                                <th>Error Details</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr class="property-change">
                                <td class="error-detail-content">{error_details}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                """
            else:
                details_html = "<p>No additional details available.</p>"
            
            errors_html += f"""
            <div class="resource-change delete collapsed" data-action="delete" data-address="error_{i+1}">
                <div class="resource-header" onclick="toggleResource(this)">
                    <span class="resource-address">Error {i+1}: {error_message}</span>
                    <span class="toggle-indicator">▼</span>
                </div>
                <div class="resource-details">
                    {details_html}
                </div>
            </div>
            """
        
        return f"""
        <div class="resource-groups">
            <div class="resource-group" data-resource-type="errors">
                <div class="group-header">
                    <h3>Errors ({len(errors)} items)</h3>
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
            timing_html += f"<p><strong>Total Duration:</strong> {timing.total_duration}</p>"
        if hasattr(timing, 'start_time') and timing.start_time:
            timing_html += f"<p><strong>Started:</strong> {timing.start_time}</p>"
        if hasattr(timing, 'end_time') and timing.end_time:
            timing_html += f"<p><strong>Completed:</strong> {timing.end_time}</p>"
        
        if not timing_html:
            return ""
        
        return f"""
        <div class="timing-section">
            <h3>⏱️ Timing Information</h3>
            <div class="timing-details">
                {timing_html}
            </div>
        </div>
        """
    
    def _get_apply_specific_css(self) -> str:
        """Get CSS specific to apply reports"""
        return """
        /* Apply Report Specific Styles */
        .header.apply-header {
            background: linear-gradient(135deg, #7b28a7 0%, #542188 100%) !important;
        }
        
        .apply-summary {
            padding: 2rem;
            text-align: center;
            border-bottom: 1px solid #e9ecef;
        }
        
        .apply-summary.success-summary {
        }
        
        .apply-summary.no-changes-summary {
        }
        
        .apply-summary.error-summary {
            background: #f8d7da;
            color: #721c24;
        }
        
        .apply-summary.unknown-summary {
            background: #fff3cd;
            color: #856404;
        }
        
        .apply-summary h2 {
            margin: 0 0 1rem 0;
        }
        
        .apply-icon {
            font-size: 2.5rem;
            margin-bottom: 1rem;
        }
        
        .status-info {
            font-size: 1.1rem;
            margin-bottom: 0.5rem;
            opacity: 0.95;
        }
        
        .status-icon {
            margin-right: 0.5rem;
        }
        
        .status-icon.completed {
            color: #28a745;
        }
        
        .status-icon.in_progress {
            color: #ffc107;
        }
        
        .status-icon.failed {
            color: #dc3545;
        }
        
        .status-icon.unknown {
            color: #6c757d;
        }
        
        .action-label {
            font-size: 0.8rem;
            background: #f8f9fa;
            padding: 0.2rem 0.5rem;
            border-radius: 3px;
            color: #495057;
            margin-left: auto;
            margin-right: 0.5rem;
        }
        
        .operation-duration {
            font-size: 0.8rem;
            color: #6c757d;
            margin-left: 0.5rem;
        }
        
        .operation-details {
            font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, monospace;
            font-size: 0.9rem;
        }
        
        .timing-section {
            padding: 1.5rem 2rem;
            border-bottom: 1px solid #e9ecef;
        }
        
        .timing-section h3 {
            margin: 0 0 1rem 0;
            color: #495057;
        }
        
        .timing-details {
            font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, monospace;
            font-size: 0.9rem;
            color: #6c757d;
        }
        
        /* Red Theme for Failed Apply */
        .theme-red .header.apply-header {
            background: linear-gradient(135deg, #dc3545 0%, #b02a37 100%) !important;
        }
        
        .theme-red .footer-btn {
            background: #dc3545;
        }
        
        .theme-red .footer-btn:hover {
            background: #b02a37;
        }
        
        .theme-red .load-logs-btn {
            background: #dc3545;
            color: white;
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
                'Terraform planned the following actions, but then encountered a problem:'
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
        """Get CSS specific to error reports"""
        return """
        .header.error-header {
            background: linear-gradient(135deg, #dc3545 0%, #b02a37 100%) !important;
        }
        
        .error-summary {
            padding: 2rem;
            text-align: center;
            background: #f8d7da;
            color: #721c24;
            border-bottom: 1px solid #f5c6cb;
        }

        .error-summary h2 {
            margin: 0 0 1rem 0;
            color: #721c24;
        }   
        
        .errors-section, .warnings-section {
            padding: 1.5rem 2rem;
            border-bottom: 1px solid #e9ecef;
        }
        
        .errors-section h3 {
            color: #dc3545;
            margin: 0 0 1rem 0;
        }
        
        .warnings-section h3 {
            color: #ffc107;
            margin: 0 0 1rem 0;
        }
        
        .error-item, .warning-item {
            background: #f8f9fa;
            border-left: 4px solid #dc3545;
            padding: 1rem;
            margin-bottom: 1rem;
            border-radius: 0 4px 4px 0;
        }
        
        .warning-item {
            border-left-color: #ffc107;
        }
        
        .error-message, .warning-message {
            font-weight: 500;
            margin-bottom: 0.5rem;
            font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, monospace;
        }
        
        .error-detail, .warning-detail {
            font-size: 0.9rem;
            color: #6c757d;
            white-space: pre-wrap;
        }
        
        /* Collapsible Error Styling */
        .error-change {
            border: 1px solid #e9ecef;
            border-radius: 6px;
            margin-bottom: 1rem;
            overflow: hidden;
            border-left: 4px solid #dc3545;
        }
        
        .error-header {
            padding: 1rem;
            background: #f8f9fa;
        }
        
        .error-header:hover {
            background: #e9ecef;
        }
        
        .error-header-nonclick {
            padding: 1rem;
            background: #f8f9fa;
            display: flex;
            align-items: center;
            gap: 0.75rem;
            user-select: none;
            cursor: default;
        }
        
        .error-header-nonclick:hover {
            background: #f8f9fa;
        }
        
        .error-icon {
            font-size: 2.5rem;
        }
        
        .error-address {
            font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, monospace;
            font-weight: 500;
            flex: 1;
        }
        
        .error-change .toggle-indicator {
            transition: transform 0.2s;
        }
        
        .error-change.collapsed .toggle-indicator {
            transform: rotate(-90deg);
        }
        
        .error-details {
            padding: 1rem;
            border-top: 1px solid #e9ecef;
            background: #fff;
        }
        
        .error-change.collapsed .error-details {
            display: none;
        }
        
        .error-detail-content {
            font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, monospace;
            font-size: 0.9rem;
            color: #6c757d;
            white-space: pre-wrap;
            line-height: 1.4;
        }
        
        .terminal-section {
            padding: 1.5rem 2rem;
        }
        
        .terminal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
        }
        
        .terminal-header h3 {
            margin: 0;
            color: #495057;
        }
        
        .copy-btn {
            background: #6c757d;
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.9rem;
        }
        
        .copy-btn:hover {
            background: #5a6268;
        }
        
        .terminal-container {
            background: #1e1e1e;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        .terminal-output {
            background: #1e1e1e;
            color: #d4d4d4;
            padding: 1.5rem;
            margin: 0;
            font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, monospace;
            font-size: 0.9rem;
            line-height: 1.4;
            white-space: pre-wrap;
            word-break: break-word;
            overflow-x: auto;
            max-height: 400px;
            overflow-y: auto;
        }
        
        /* Syntax highlighting for terraform output */
        .terminal-output {
            /* Error text in white */
            color: #d4d4d4;
        }
        
        @media (max-width: 768px) {
            .terminal-header {
                flex-direction: column;
                align-items: flex-start;
                gap: 1rem;
            }
            
            .terminal-output {
                font-size: 0.8rem;
                padding: 1rem;
            }
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
                'Terraform planned the following actions, but then encountered a problem:'
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
        """Generate the report footer"""
        # Get BUILD_URL from environment or config
        import os
        build_url = os.environ.get('BUILD_URL', self.config.get('build_url', ''))
        
        # Check if debug_json is enabled before showing JSON button
        debug_json = self.config.get('debug_json', False)
        
        buttons_html = ""
        if build_url:
            buttons_html += f'<a href="{build_url}" class="footer-btn" target="_blank">🔗 View Build</a>'
        
        # Only show JSON button if debug_json flag is enabled
        if debug_json:
            # Get JSON URL from config (passed from CLI) or environment variable as fallback
            json_url = self.config.get('json_url', '') or os.environ.get('TOFUI_JSON_URL', '')
            
            if not json_url:
                # Fallback to relative filename if no URL provided
                json_url = self.plan_name.replace('.html', '') + '.json'
            
            buttons_html += f'<a href="{json_url}" class="footer-btn" target="_blank">📄 View JSON</a>'
        
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
            display: flex;
            flex-direction: column;
        }
        
        .header {
            background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%);
            color: white;
            padding: 1rem;
            text-align: center;
        }
        
        .known-after-apply {
            color: #a3c5a8;
            font-style: italic;
            opacity: 0.8;
        }

        .known-after-apply-cell {
            background: #d4edda !important;
            color: #155724;
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
        
        .filters {
            padding: 1.5rem 2rem;
            background: #f8f9fa;
            border-bottom: 1px solid #e9ecef;
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
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
        
        .resource-change.read {
            border-left: 16px solid #6c757d;
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
        
        /* Outputs Section Styling */
        .outputs-section {
            padding: 1.5rem 2rem;
            border-top: 1px solid #e9ecef;
        }

        .outputs-section h2 {
            margin: 0 0 1rem 0;
            color: #495057;
            font-size: 1.4rem;
        }

        .outputs-container {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 1rem;
        }

        .output-item {
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 6px;
            overflow: hidden;
        }

        .output-name {
            background: #e9ecef;
            padding: 0.75rem;
            font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, monospace;
            font-weight: 500;
            color: #495057;
            border-bottom: 1px solid #dee2e6;
        }

        .output-details {
            padding: 0.75rem;
        }

        .output-value {
            margin: 0 0 0.5rem 0;
            font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, monospace;
            font-size: 0.85rem;
            white-space: pre-wrap;
            word-break: break-all;
            overflow-x: auto;
        }

        .output-type {
            font-size: 0.8rem;
            color: #6c757d;
            display: block;
            margin-top: 0.5rem;
        }

        .sensitive-value {
            color: #6c757d;
            font-style: italic;
            background: #f1f3f5;
            padding: 0.25rem 0.5rem;
            border-radius: 3px;
        }

        .no-changes-summary {
            padding: 2rem;
            text-align: center;
            background: #d4edda;
            color: #155724;
            border-bottom: 1px solid #d4edda;
        }

        .no-changes-summary h2 {
            margin: 0 0 1rem 0;
            color: #155724;
        }

        .no-changes-icon {
            font-size: 2.5rem;
            color: #28a745;
        }

        .command-box {
            background: #f1f3f5;
            border-radius: 6px;
            padding: 0.2rem;
            margin: 0.2rem 0;
        }

        .command {
            background: #212529;
            color: #f8f9fa;
            padding: 0.6rem 0.8rem;
            border-radius: 4px;
            font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, monospace;
            margin-top: 0.75rem;
        }
        
        /* Terminal Section Styling */
        .terminal-section {
            padding: 1.5rem 2rem;
            border-top: 1px solid #e9ecef;
        }
        
        .terminal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
        }
        
        .terminal-header h3 {
            margin: 0;
            color: #495057;
        }
        
        .load-logs-btn {
            background: #6c757d;
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.9rem;
            margin-right: 0.5rem;
        }
        
        .load-logs-btn:hover {
            background: #5a6268;
        }
        
        .copy-btn {
            background: #6c757d;
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.9rem;
        }
        
        .copy-btn:hover {
            background: #5a6268;
        }
        
        .terminal-container {
            background: #1e1e1e;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        .terminal-output {
            background: #1e1e1e;
            color: #d4d4d4;
            padding: 1.5rem;
            margin: 0;
            font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, monospace;
            font-size: 0.9rem;
            line-height: 1.4;
            white-space: pre-wrap;
            word-break: break-word;
            overflow-x: auto;
            max-height: 400px;
            overflow-y: auto;
        }
        
        .properties-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9rem;
            table-layout: fixed; /* Use fixed layout for better column control */
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
            padding: 0.5rem; #decrease this to decrease padding between properties
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
            max-width: 37.5%;
            min-width: 0; /* Allow shrinking */
        }
        
        .before-value pre, .after-value pre {
            margin: 0;
            font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, monospace;
            font-size: 0.85rem;
            white-space: pre-wrap;
            word-break: break-all;
            /* Apply consistent constraints to ALL pre elements */
            max-height: 200px;
            max-width: 100%;
            overflow: auto;
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 4px;
            padding: 0.5rem;
        }
        
        /* Styling for long values - additional styling for complex content */
        .before-value pre.long-value, .after-value pre.long-value {
            font-size: 0.68rem; /* 20% smaller than 0.85rem */
            white-space: pre;
            word-break: normal;
        }
        
        /* Custom scrollbar styling for long values */
        .before-value pre.long-value::-webkit-scrollbar, .after-value pre.long-value::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        
        .before-value pre.long-value::-webkit-scrollbar-track, .after-value pre.long-value::-webkit-scrollbar-track {
            background: #f1f1f1;
            border-radius: 4px;
        }
        
        .before-value pre.long-value::-webkit-scrollbar-thumb, .after-value pre.long-value::-webkit-scrollbar-thumb {
            background: #c1c1c1;
            border-radius: 4px;
        }
        
        .before-value pre.long-value::-webkit-scrollbar-thumb:hover, .after-value pre.long-value::-webkit-scrollbar-thumb:hover {
            background: #a8a8a8;
        }
        
        /* Long simple values - horizontal scroll only for ARNs, URLs, etc */
        .long-simple-value {
            font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, monospace;
            font-size: 0.8rem;
            white-space: nowrap;
            overflow-x: auto;
            overflow-y: hidden;
            max-width: 100%;
            padding: 0.5rem;
            border: 1px solid #e9ecef;
            border-radius: 4px;
            background: #f8f9fa;
        }
        
        /* Custom scrollbar for long simple values */
        .long-simple-value::-webkit-scrollbar {
            height: 6px;
        }
        
        .long-simple-value::-webkit-scrollbar-track {
            background: #f1f1f1;
            border-radius: 3px;
        }
        
        .long-simple-value::-webkit-scrollbar-thumb {
            background: #c1c1c1;
            border-radius: 3px;
        }
        
        .long-simple-value::-webkit-scrollbar-thumb:hover {
            background: #a8a8a8;
        }
        
        /* Complex content - 5-line container with both scrolls for JSON, multiline */
        .complex-value {
            margin: 0;
            font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, monospace;
            font-size: 0.75rem;
            white-space: pre-wrap;
            word-break: normal;
            max-height: 100px; /* Exactly 5 lines with line-height 1.2 */
            min-height: 60px;  /* Ensure it shows as a container even for short content */
            max-width: 100%;
            overflow: auto;
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 4px;
            padding: 0.5rem;
            line-height: 1.2;
        }
        
        /* Custom scrollbar styling for complex values */
        .complex-value::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        
        .complex-value::-webkit-scrollbar-track {
            background: #f1f1f1;
            border-radius: 4px;
        }
        
        .complex-value::-webkit-scrollbar-thumb {
            background: #c1c1c1;
            border-radius: 4px;
        }
        
        .complex-value::-webkit-scrollbar-thumb:hover {
            background: #a8a8a8;
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
            visibility: hidden;
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
            margin-top: auto;
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
            background: #dc3545;
            color: white;
            text-decoration: none;
            padding: 0.5rem 1rem;
            border-radius: 4px;
            font-size: 0.9rem;
            transition: background-color 0.2s;
        }
        
        .footer-btn:hover {
            background: #721c24;
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
            // Get selected property filters (properties to hide)
            const hiddenProperties = Array.from(
                document.querySelectorAll('#property-filters input[type="checkbox"]:checked')
            ).map(input => input.value);
            
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
            if (!resourceGroupsContainer) return; // No resources to sort
            
            const resourceGroups = Array.from(resourceGroupsContainer.querySelectorAll('.resource-group'));
            
            // Always use priority-based sorting: delete → recreate → update → create
            const actionPriority = {
                'delete': 1,
                'recreate': 2, 
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
                `${baseName}.log`,  // Local: same directory
                `../logs/${baseName}.log`,  // GitHub Pages: logs folder
                `logs/${baseName}.log`  // Alternative GitHub Pages path
            ];
            
            tryLoadLog(logUrls, 0);
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
                    document.getElementById('terminal-output').textContent = data;
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
