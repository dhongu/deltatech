# Overview
The Deltatech Sale Order Stage Route module extends Odoo's sales and inventory workflows by introducing a structured path for sale orders and their associated pickings. It allows businesses to define a sequence of stages (phases) that an order must go through, ensuring a controlled and visible progression from initial sale to final delivery.

# Key Features

## Stage Route Definition
- **Custom Routes**: Define specific routes containing at least two stages.
- **Validation Rules**: Ensures a stage cannot appear twice in the same route.
- **Sales Integration**: Assign a stage route directly on the sale order.

## Inventory & Barcode Enhancements
- **Picking Synchronization**: Pickings automatically inherit the stage route from their parent sale order.
- **Barcode Interface Visibility**:
    - Current and next phases are prominently displayed in the Barcode app header.
    - Phases are color-coded for quick visual identification.
    - Large, clear badges show the progress directly in the scanning view.
- **Automated Workflow**:
    - Validating a picking in an intermediate stage advances the sale order to the next phase instead of completing the picking.
    - Automatically resets scanned quantities and "picked" status for the next operator in the route.
    - Re-checks stock availability (reservation) upon phase transition.
    - Automatically returns to the picking list after a phase change to signal completion of the current task.

## Kanban & Pipeline Management
- **Visual Grouping**: Dedicated Kanban views for Sale Orders and Pickings, grouped by their current phase.
- **Full Pipeline Visibility**: All phase columns are visible even if they contain no orders, providing a complete overview of the workflow.
- **Drag-and-Drop**: Supports moving orders and pickings between stages directly in the Kanban view (restricted by security rules).

## Security & Access Control
- **Phase Admin Group**: A dedicated security group for users who need full control over stage transitions.
- **Transition Restrictions**: Regular users can only advance pickings to the immediate next stage, while Phase Admins can move them to any stage or skip steps.
- **Field Protection**: The phase selection on sale orders is readonly for regular users and editable only by Phase Admins.

# Technical Details

## Module Dependencies
- deltatech_sale_stage

## Models Extended
- **sale.order.stage.route**: Defines the routes and their sequence of stages.
- **sale.order**: Integrates routes and handles the initial phase assignment.
- **stock.picking**: Manages the progression of stages during warehouse operations and integrates with the Barcode app.

## Included Data Files
1. **Views**:
    - `views/sale_phase_view.xml`: Configuration for stage routes.
    - `views/sale_view.xml`: Sale order form and kanban enhancements.
    - `views/stock_picking_view.xml`: Picking form, list, and kanban enhancements, including barcode views.
2. **Security**:
    - `security/security.xml`: Definition of the Phase Admin group.
    - `security/ir.model.access.csv`: Access rights for route configurations.

## Benefits
1. **Process Standardization**: Ensures all sales follow a predefined sequence of operational steps.
2. **Enhanced Transparency**: Real-time visibility of order progress in both sales and warehouse departments.
3. **Reduced Errors**: Prevents skipping critical stages and ensures clean data for each operator in the chain.
4. **Optimized Warehouse Flow**: Tailored barcode interface for multi-stage processing.
