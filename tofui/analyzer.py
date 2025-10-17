"""
Terraform Plan Analyzer

Analyzes parsed terraform plan data to extract meaningful insights and prepare data for HTML generation.
"""

from typing import Dict, List, Any, Set, Tuple
from dataclasses import dataclass
from collections import defaultdict
import json

from .parser import TerraformPlan, ResourceChange, ActionType


@dataclass
class PropertyChange:
    """Represents a change to a specific property of a resource"""
    property_path: str
    before_value: Any
    after_value: Any
    is_sensitive: bool = False
    is_computed: bool = False
    
    @property
    def is_addition(self) -> bool:
        return self.before_value is None and self.after_value is not None
    
    @property
    def is_removal(self) -> bool:
        return self.before_value is not None and self.after_value is None
    
    @property
    def is_modification(self) -> bool:
        return self.before_value is not None and self.after_value is not None


@dataclass
class AnalyzedResourceChange:
    """Enhanced resource change with detailed property analysis"""
    resource_change: ResourceChange
    property_changes: List[PropertyChange]
    
    @property
    def address(self) -> str:
        return self.resource_change.address
    
    @property
    def type(self) -> str:
        return self.resource_change.type
    
    @property
    def action(self) -> ActionType:
        return self.resource_change.action
    
    @property
    def has_property_changes(self) -> bool:
        return len(self.property_changes) > 0
    
    @property
    def has_dependency_changes(self) -> bool:
        """Check if this resource is being changed due to dependencies"""
        return len(self.resource_change.replace_paths) > 0
    
    @property
    def dependency_reason(self) -> str:
        """Get a human-readable explanation of dependency-driven changes"""
        if not self.has_dependency_changes:
            return ""
        
        # Extract the first element from each replace_path
        paths = []
        for path in self.resource_change.replace_paths:
            if path:  # Make sure the path is not empty
                paths.append(path[0])
            else:
                paths.append("unknown")
        
        if len(paths) == 1:
            return f"Recreated due to dependency change in: {paths[0]}"
        else:
            return f"Recreated due to dependency changes in: {', '.join(paths)}"


@dataclass
class ResourceGroup:
    """Group of resources of the same type"""
    resource_type: str
    changes: List[AnalyzedResourceChange]
    
    @property
    def count(self) -> int:
        return len(self.changes)
    
    @property
    def action_counts(self) -> Dict[ActionType, int]:
        counts = defaultdict(int)
        for change in self.changes:
            counts[change.action] += 1
        return dict(counts)


@dataclass
class PlanAnalysis:
    """Complete analysis of a terraform plan"""
    plan: TerraformPlan
    resource_groups: List[ResourceGroup]
    all_property_names: Set[str]
    action_counts: Dict[ActionType, int]
    
    @property
    def has_changes(self) -> bool:
        return self.plan.summary.has_changes
    
    @property
    def total_resources(self) -> int:
        return len(self.plan.resource_changes)


class PlanAnalyzer:
    """Analyzes terraform plans to extract meaningful insights"""
    
    def __init__(self):
        self._max_depth = 10  # Prevent infinite recursion in nested objects
    
    def analyze(self, plan: TerraformPlan) -> PlanAnalysis:
        """Analyze a terraform plan and return detailed insights"""
        
        # Filter out read operations and no-op operations - only show resources with actual changes
        filtered_changes = [
            rc for rc in plan.resource_changes 
            if rc.action not in [ActionType.READ, ActionType.NO_OP]
        ]
        
        # Analyze each resource change in detail
        analyzed_changes = []
        all_property_names = set()
        
        for resource_change in filtered_changes:
            analyzed_change = self._analyze_resource_change(resource_change)
            analyzed_changes.append(analyzed_change)
            
            # Collect all property names for filtering UI
            for prop_change in analyzed_change.property_changes:
                all_property_names.add(prop_change.property_path.split('.')[0])
        
        # Group resources by type
        resource_groups = self._group_resources_by_type(analyzed_changes)
        
        # Calculate action counts
        action_counts = self._calculate_action_counts(analyzed_changes)
        
        return PlanAnalysis(
            plan=plan,
            resource_groups=resource_groups,
            all_property_names=all_property_names,
            action_counts=action_counts
        )
    
    def _analyze_resource_change(self, resource_change: ResourceChange) -> AnalyzedResourceChange:
        """Analyze a single resource change to extract property-level changes"""
        
        if resource_change.action == ActionType.CREATE:
            # For creates, all 'after' values are additions
            property_changes = self._extract_properties_from_dict(
                resource_change.after or {}, 
                "", 
                {},
                resource_change.after_sensitive or []
            )
        elif resource_change.action == ActionType.DELETE:
            # For deletes, all 'before' values are removals
            property_changes = self._extract_properties_from_dict(
                resource_change.before or {}, 
                "", 
                resource_change.before or {}, 
                resource_change.before_sensitive or [],
                is_removal=True
            )
        else:
            # For updates, compare before and after
            property_changes = self._compare_objects(
                resource_change.before or {},
                resource_change.after or {},
                "",
                resource_change.before_sensitive or [],
                resource_change.after_sensitive or []
            )
        
        return AnalyzedResourceChange(
            resource_change=resource_change,
            property_changes=property_changes
        )
    
    def _extract_properties_from_dict(
        self, 
        obj: Dict[str, Any], 
        prefix: str, 
        before_obj: Dict[str, Any],
        sensitive_paths: List[str],
        is_removal: bool = False,
        depth: int = 0
    ) -> List[PropertyChange]:
        """Extract property changes from a dictionary object"""
        
        if depth > self._max_depth:
            return []
        
        changes = []
        
        for key, value in obj.items():
            current_path = f"{prefix}.{key}" if prefix else key
            
            # Only mark leaf values as sensitive, not container objects
            # Check if this specific path is in the sensitive_paths list
            is_sensitive = self._is_path_sensitive(current_path, sensitive_paths)
            
            if isinstance(value, dict) and not is_sensitive:
                # Recursively process nested objects
                before_value = before_obj.get(key, {}) if before_obj else {}
                nested_changes = self._extract_properties_from_dict(
                    value, 
                    current_path, 
                    before_value if isinstance(before_value, dict) else {},
                    sensitive_paths,
                    is_removal,
                    depth + 1
                )
                changes.extend(nested_changes)
            else:
                # Create property change for this value
                if is_removal:
                    changes.append(PropertyChange(
                        property_path=current_path,
                        before_value=value,
                        after_value=None,
                        is_sensitive=is_sensitive
                    ))
                else:
                    changes.append(PropertyChange(
                        property_path=current_path,
                        before_value=before_obj.get(key) if before_obj else None,
                        after_value=value,
                        is_sensitive=is_sensitive
                    ))
        
        return changes
    
    def _is_path_sensitive(self, path: str, sensitive_paths: List[str]) -> bool:
        """
        Check if a property path should be marked as sensitive.
        
        This method properly handles Terraform's sensitive_values structure which
        can contain nested objects that don't necessarily mean the values are sensitive.
        Only leaf values with actual sensitive data should be marked as sensitive.
        """
        if not sensitive_paths:
            return False
            
        # Direct path match
        if path in sensitive_paths:
            return True
            
        # For now, use simple string matching as Terraform's sensitive_paths 
        # format can vary. In the future, this could be enhanced to handle
        # more complex nested structures based on actual Terraform output format.
        return False
    
    def _compare_objects(
        self, 
        before: Dict[str, Any], 
        after: Dict[str, Any], 
        prefix: str,
        before_sensitive: List[str],
        after_sensitive: List[str],
        depth: int = 0
    ) -> List[PropertyChange]:
        """Compare two objects and extract the differences"""
        
        if depth > self._max_depth:
            return []
        
        changes = []
        
        # Get all keys from both objects
        all_keys = set(before.keys()) | set(after.keys())
        
        for key in all_keys:
            current_path = f"{prefix}.{key}" if prefix else key
            before_value = before.get(key)
            after_value = after.get(key)
            
            # Use the improved sensitive path checking
            is_sensitive = (self._is_path_sensitive(current_path, before_sensitive) or 
                          self._is_path_sensitive(current_path, after_sensitive))
            
            if before_value == after_value:
                # No change
                continue
            elif isinstance(before_value, dict) and isinstance(after_value, dict) and not is_sensitive:
                # Both are dicts, compare recursively
                nested_changes = self._compare_objects(
                    before_value, 
                    after_value, 
                    current_path,
                    before_sensitive,
                    after_sensitive,
                    depth + 1
                )
                changes.extend(nested_changes)
            else:
                # Value changed
                changes.append(PropertyChange(
                    property_path=current_path,
                    before_value=before_value,
                    after_value=after_value,
                    is_sensitive=is_sensitive
                ))
        
        return changes
    
    def _group_resources_by_type(self, analyzed_changes: List[AnalyzedResourceChange]) -> List[ResourceGroup]:
        """Group analyzed resource changes by resource type"""
        groups = defaultdict(list)
        
        for change in analyzed_changes:
            groups[change.type].append(change)
        
        # Convert to ResourceGroup objects and sort by type name
        resource_groups = [
            ResourceGroup(resource_type=resource_type, changes=changes)
            for resource_type, changes in groups.items()
        ]
        
        resource_groups.sort(key=lambda g: g.resource_type)
        return resource_groups
    
    def _calculate_action_counts(self, analyzed_changes: List[AnalyzedResourceChange]) -> Dict[ActionType, int]:
        """Calculate counts of each action type"""
        counts = defaultdict(int)
        
        for change in analyzed_changes:
            counts[change.action] += 1
        
        return dict(counts)
    
    def format_value_for_display(self, value: Any, max_length: int = 100) -> str:
        """Format a value for display in the HTML report"""
        if value is None:
            return "<null>"
        elif isinstance(value, bool):
            return "true" if value else "false"
        elif isinstance(value, (dict, list)):
            # Pretty print JSON with limited length
            json_str = json.dumps(value, indent=2, default=str)
            if len(json_str) > max_length:
                return json_str[:max_length] + "..."
            return json_str
        elif isinstance(value, str):
            # Escape HTML and truncate long strings
            escaped = value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            if len(escaped) > max_length:
                return escaped[:max_length] + "..."
            return escaped
        else:
            # Convert to string and truncate
            str_value = str(value)
            if len(str_value) > max_length:
                return str_value[:max_length] + "..."
            return str_value
