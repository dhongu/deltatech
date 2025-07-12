
# Deltatech Price Categories

## Overview

The Deltatech Price Categories module enhances Odoo's pricing system by introducing advanced product price categorization capabilities. This module is designed to provide businesses with more flexibility and control over how prices are managed and applied to different customers and products.

## Key Features

### Tiered Pricing System
The module implements a comprehensive tiered pricing system with predefined price levels:
1. **Bronze Price** - Entry-level pricing tier
2. **Silver Price** - Mid-level pricing tier
3. **Gold Price** - Premium pricing tier
4. **Platinum Price** - Top-tier pricing for VIP customers

### Direct Product Price Editing
- All pricing tiers are available directly in the product form, allowing for quick and easy editing
- Each price tier is calculated based on configurable percentage markups from a base price
- Prices can be automatically calculated or manually adjusted as needed

### Base Price Configuration
- Select your preferred base price calculation method:
  - Standard cost price
  - Last purchase price
  - Custom list price
- Define percentage markups for each tier (Bronze, Silver, Gold, Platinum)
- System automatically calculates all tier prices when the base price or percentages change

### Price Category Management
- Create and manage custom price categories that can be assigned to both products and customers
- Organize products into logical pricing groups for easier bulk price updates
- Apply custom pricing rules based on category combinations

### Enhanced Partner Pricelist Handling
- Improved search functionality for partner pricelists
- Custom domain filters for partner-specific pricing
- Advanced partner-to-pricelist mapping capabilities

### Flexible Pricing Rules
- Define pricing rules that apply to entire categories of products
- Set up automated price adjustments based on product categories
- Configure multi-level pricing hierarchies for complex business requirements

### Business Benefits
- Reduce time spent on price management with category-based updates
- Improve pricing consistency across similar products
- Simplify price adjustments during sales campaigns or seasonal changes
- Enhance customer segmentation with category-based pricing

### Technical Improvements
- Optimized database queries for price searches
- Extended Odoo's standard pricelist model with additional functionality
- Compatible with standard Odoo pricelist features

## How Price Tiers Are Edited

Prices for all tiers can be managed directly on the product form:

1. **Configuration**: Set your base price method (list price, cost price, or last purchase price)
2. **Define Markups**: Set percentage markups for each tier (Bronze, Silver, Gold, Platinum)
3. **Automatic Calculation**: The system automatically calculates all tier prices based on your settings
4. **Manual Override**: You can manually adjust calculated prices if needed
5. **Visual Indicators**: The system provides visual warnings if pricing tiers are not properly aligned (e.g., if Bronze price is higher than Silver)

All price changes are tracked in the system, providing a complete audit trail of price modifications.

## Integration Capabilities
The module seamlessly integrates with Odoo's core pricing and product management systems, as well as other Deltatech modules like:
- Deltatech Product Category
- Deltatech Price Change
- Deltatech Pricelist Add Category

## Use Cases
- Retail businesses with complex product hierarchies
- Wholesale companies managing customer-specific pricing
- Manufacturing companies with component-based pricing structures
- E-commerce businesses requiring category-based promotional pricing

## Additional Information
This module is part of the Deltatech suite, developed by Terrabit to extend Odoo's standard functionality with enterprise-grade features.
