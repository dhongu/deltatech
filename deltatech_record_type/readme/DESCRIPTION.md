# Deltatech Record Type

## Overview

The Deltatech Record Type module provides an enhanced way to manage multiple record types for various Odoo documents
including sales orders, purchase orders, and invoices. This module allows businesses to create and maintain different
types of records with specific default values and routing configurations.

## Key Features

- Define custom record types for sale orders, purchase orders, and invoices
- Assign specific users to each record type for access control
- Set default values for fields when creating new records of a specific type
- Configure stock routes for each record type
- Only displays type field in models that have types defined

## Technical Implementation

The module implements a flexible framework through two main models:

- : Defines the type configuration including allowed users and routing `record.type`
- `record.type.default.values`: Manages default field values for each record type with dynamic field selection

## Integration Points

- Integrates with core Odoo modules: Sale, Purchase, and Accounting
- Extends the standard views of sale orders, purchase orders, and invoices
- Supports custom security roles for type management

## Business Benefits

- Streamlines document creation with predefined templates
- Enhances user experience by showing only relevant record types to specific users
- Improves business workflow with customized routing per record type
- Reduces data entry errors with automatic default values

## Usage

Record types can be configured in the system settings. Each type can have specific default values for fields, which will
be automatically applied when creating new records of that type. User access to record types can be restricted, ensuring
that users only see and use the appropriate record types for their role. This module is maintained by Terrabit and is
available for Odoo 17.0.
