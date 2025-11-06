"""
tofUI - Beautiful Infrastructure Plans

A Python package for generating beautiful, interactive HTML reports from openTofu and terraform JSON plans.
"""

__version__ = "0.8.7"
__author__ = "tofUI"
__description__ = "Beautiful OpenTofu and Terraform Infrastructure Plans"

from .parser import TerraformPlanParser
from .generator import HTMLGenerator
from .analyzer import PlanAnalyzer

__all__ = ['TerraformPlanParser', 'HTMLGenerator', 'PlanAnalyzer']
