#!/usr/bin/env python3
"""Fix DiagnosticIssue instances to include confidence parameter."""

import re
from pathlib import Path


def fix_diagnostic_issues():
    """Add confidence parameter to all DiagnosticIssue instances."""
    diagnostics_file = Path("testing/framework/diagnostics.py")

    # Read content
    with open(diagnostics_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Find and replace patterns
    fixes = [
        # Auto-fixable=True -> High confidence
        (
            r"auto_fixable=True\s*(?!\n.*confidence)",
            "auto_fixable=True,\n                    confidence=DiagnosticConfidence.HIGH",
        ),
        # Auto-fixable=False, severity="warning" -> Medium confidence
        (
            r'auto_fixable=False\s*(?=.*severity="warning")(?!\n.*confidence)',
            "auto_fixable=False,\n                    confidence=DiagnosticConfidence.MEDIUM",
        ),
        # Auto-fixable=False, severity="critical" -> Low confidence (requires manual intervention)
        (
            r'auto_fixable=False\s*(?=.*severity="critical")(?!\n.*confidence)',
            "auto_fixable=False,\n                    confidence=DiagnosticConfidence.LOW",
        ),
        # Any remaining auto_fixable=False -> Medium confidence
        (
            r"auto_fixable=False\s*(?!\n.*confidence)",
            "auto_fixable=False,\n                    confidence=DiagnosticConfidence.MEDIUM",
        ),
    ]

    # Apply fixes
    for pattern, replacement in fixes:
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE | re.DOTALL)

    # Write back
    with open(diagnostics_file, "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ Fixed DiagnosticIssue instances with confidence parameters")


if __name__ == "__main__":
    fix_diagnostic_issues()
