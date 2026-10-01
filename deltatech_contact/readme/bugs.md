# Identified bugs

Reviewed: 2026-10-01
Target version: Odoo 20.0
Scope: Source review and isolated method validation. Integration-test results are reported separately below when available.

## [P2] Nonnumeric CNP input raises an unhandled conversion error

**Status:** Open — documented, not fixed.

**Location:** `models/res_partner.py:46–65`. Line numbers refer to the reviewed source and may change.

### Cause

check_single_cnp() checks length but does not verify that all characters are digits before checksum and final-digit int conversions.

### Impact

A malformed 13-character CNP can raise ValueError instead of returning false and letting the constraint display the intended CNP validation error.

### Reproduction

Call check_single_cnp with 123456789012X. The final digit conversion raises ValueError. A nondigit among the first 12 positions fails in the checksum helper.

### Recommended correction

Validate the permitted numeric character format before converting digits and return false for malformed input.

### Validation

The actual check_single_cnp and checksum methods were executed in isolation with 123456789012X; ValueError was raised.

## [P2] The contact-name-only setting no longer affects Odoo 20 display names

**Status:** Open — documented, not fixed.

**Location:** `models/res_partner.py:104–110`. Line numbers refer to the reviewed source and may change.

### Cause

The parameter contact.get_name_only is read only in _get_contact_name(). Odoo 20 builds contact names through _get_complete_name(); the old helper is neither implemented nor called by the current core.

### Impact

Enabling the documented parameter no longer hides the parent company from contact display names. Directly calling the helper in its fallback branch also reaches a nonexistent super method.

### Reproduction

Enable contact.get_name_only and read the display name of a contact with a parent company. Core name construction still includes the company unless the supported partner_display_name_hide_company context is set.

### Recommended correction

Implement the setting through the supported Odoo 20 complete/display-name path, preserving existing context-dependent display behavior.

### Validation

The documented setting, custom parameter reader and Odoo 20 _get_complete_name/_compute_display_name call paths were inspected.
