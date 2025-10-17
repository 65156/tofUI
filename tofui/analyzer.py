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
        sensitive_structure: Any,
        is_removal: bool = False,
        depth: int = 0
    ) -> List[PropertyChange]:
        """Extract property changes from a dictionary object"""
        
        if depth > self._max_depth:
            return []
        
        changes = []
        
        for key, value in obj.items():
            current_path = f"{prefix}.{key}" if prefix else key
            
            # Get the sensitive structure for this key
            sensitive_for_key = self._get_sensitive_for_key(sensitive_structure, key)
            
            # Check if this specific value is marked as sensitive
            is_sensitive = self._is_value_sensitive(value, sensitive_for_key)
            
            # Skip empty values unless they're sensitive (sensitive values should always be shown)
            if not is_sensitive and self._should_skip_empty_value(value):
                continue
            
            if isinstance(value, dict) and not is_sensitive:
                # Recursively process nested objects
                before_value = before_obj.get(key, {}) if before_obj else {}
                nested_changes = self._extract_properties_from_dict(
                    value, 
                    current_path, 
                    before_value if isinstance(before_value, dict) else {},
                    sensitive_for_key,
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
    
    def _get_sensitive_for_key(self, sensitive_structure: Any, key: str) -> Any:
        """
        Extract the sensitive structure for a specific key.
        
        Terraform's sensitive_values structure mirrors the actual values structure.
        """
        if not sensitive_structure:
            return None
            
        if isinstance(sensitive_structure, dict):
            return sensitive_structure.get(key)
        elif isinstance(sensitive_structure, list):
            # For lists, we can't map by key, so return None
            return None
        else:
            return None
    
    def _should_skip_empty_value(self, value: Any) -> bool:
        """
        Check if a value should be skipped because it's empty/null.
        
        Skip display of:
        - Empty arrays: []
        - Empty objects: {}
        - Null/None values
        - Empty strings (after JSON formatting)
        """
        if value is None:
            return True
        if isinstance(value, list) and len(value) == 0:
            return True
        if isinstance(value, dict) and len(value) == 0:
            return True
        if isinstance(value, str) and value.strip() == "":
            return True
        return False
    
    def _is_value_sensitive(self, value: Any, sensitive_structure: Any) -> bool:
        """
        Check if a specific value should be marked as sensitive based on Terraform's structure.
        
        The key insight: Terraform's sensitive_values contains the STRUCTURE but only
        marks actual sensitive leaf values as True. Empty objects/arrays mean the 
        structure exists but contains no sensitive values.
        """
        if not sensitive_structure:
            return False
            
        # If the sensitive structure is explicitly True, then this value is sensitive
        if sensitive_structure is True:
            return True
            
        # If it's an empty dict {}, empty list [], or any other structure,
        # it means the container exists but the values inside are NOT sensitive
        if isinstance(sensitive_structure, (dict, list)):
            if not sensitive_structure:  # Empty dict or list
                return False
            # For non-empty structures, we need to check if ANY child is True
            # But for the current level, the container itself is not sensitive
            return False
            
        # Any other value (False, None, etc.) means not sensitive
        return False
    
    def _is_path_sensitive(self, path: str, sensitive_paths: List[str]) -> bool:
        """
        Legacy method - kept for backward compatibility but should not be used
        with the new sensitive structure handling.
        """
        if not sensitive_paths:
            return False
            
        # Direct path match
        if path in sensitive_paths:
            return True
            
        return False
    
    def _compare_objects(
        self, 
        before: Dict[str, Any], 
        after: Dict[str, Any], 
        prefix: str,
        before_sensitive: Any,
        after_sensitive: Any,
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
            
            # Get sensitive structures for this key from both before and after
            before_sensitive_for_key = self._get_sensitive_for_key(before_sensitive, key)
            after_sensitive_for_key = self._get_sensitive_for_key(after_sensitive, key)
            
            # Check if either value is marked as sensitive
            is_sensitive = (self._is_value_sensitive(before_value, before_sensitive_for_key) or 
                          self._is_value_sensitive(after_value, after_sensitive_for_key))
            
            # Skip empty values unless they're sensitive or there's an actual change
            if not is_sensitive and before_value == after_value and self._should_skip_empty_value(after_value):
                continue
            
            if before_value == after_value:
                # No change
                continue
            elif isinstance(before_value, dict) and isinstance(after_value, dict) and not is_sensitive:
                # Both are dicts, compare recursively
                nested_changes = self._compare_objects(
                    before_value, 
                    after_value, 
                    current_path,
                    before_sensitive_for_key,
                    after_sensitive_for_key,
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
    
    def format_value_for_display(self, value: Any) -> tuple[str, bool]:
        """
        Format a value for display in the HTML report.
        
        Returns:
            tuple: (formatted_value, is_long_value)
                - formatted_value: The formatted string to display
                - is_long_value: True if this should be displayed in a scrollable container
        """
        if value is None:
            return "<null>", False
        elif isinstance(value, bool):
            return "true" if value else "false", False
        elif isinstance(value, (dict, list)):
            # Pretty print JSON - never truncate
            json_str = json.dumps(value, indent=2, default=str)
            # Consider it "long" if it has multiple lines or is over 150 characters
            is_long = '\n' in json_str or len(json_str) > 150
            return json_str, is_long
        elif isinstance(value, str):
            # Escape HTML but never truncate
            escaped = value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            # Consider it "long" if it's over 100 characters or has multiple lines
            is_long = len(escaped) > 100 or '\n' in escaped
            return escaped, is_long
        else:
            # Convert to string but never truncate
            str_value = str(value)
            # Consider it "long" if it's over 100 characters
            is_long = len(str_value) > 100
            return str_value, is_long
