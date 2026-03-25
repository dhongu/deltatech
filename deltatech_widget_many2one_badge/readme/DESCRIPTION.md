
A custom widget  that displays Many2one fields as colored badges, similar to `many2many_tags`.

## Features

- ✅ Displays as a colored badge in readonly mode
- ✅ Click on badge to change color via color picker popover (edit mode)
- ✅ Remove button (`×`) appears on hover over the badge
- ✅ Autocomplete input for selecting a new value when field is empty
- ✅ Supports customizable `color_field` option
- ✅ Compatible with all standard Odoo colors (0–11)
- ✅ Modern rounded badge design

## Installation

1. Copy the `deltatech_widget_many2one_badge` folder into your Odoo `addons` directory
2. Restart the Odoo server
3. Enable Developer Mode
4. Go to Apps → Update Apps List
5. Search for "Many2one Badge Widget"
6. Click Install

## Usage

### 1. Make sure the related model has a `color` field

```python
class MyCategory(models.Model):
    _name = 'my.category'
    _description = 'My Category'

    name = fields.Char(string='Name', required=True)
    color = fields.Integer(string='Color', default=0)
```

### 2. Use the widget in your view

```xml
<field name="category_id"
       widget="many2one_badge"
       options="{'color_field': 'color'}"/>
```

### 3. Available options

| Option | Description | Default |
|---|---|---|
| `color_field` | Name of the integer field on the related model that stores the color index | `'color'` |

```xml
<!-- Example with a custom color field -->
<field name="status_id"
       widget="many2one_badge"
       options="{'color_field': 'badge_color'}"/>
```

## Full Example

### Python model

```python
# models/task.py
from odoo import models, fields

class Task(models.Model):
    _name = 'my.task'
    _description = 'My Task'

    name = fields.Char(string='Name', required=True)
    category_id = fields.Many2one('my.category', string='Category')
    priority_id = fields.Many2one('my.priority', string='Priority')

class Category(models.Model):
    _name = 'my.category'
    _description = 'Task Category'

    name = fields.Char(string='Name', required=True)
    color = fields.Integer(string='Color', default=0)

class Priority(models.Model):
    _name = 'my.priority'
    _description = 'Task Priority'

    name = fields.Char(string='Name', required=True)
    color = fields.Integer(string='Badge Color', default=0)
```

### XML view

```xml
<record id="view_task_form" model="ir.ui.view">
    <field name="name">my.task.form</field>
    <field name="model">my.task</field>
    <field name="arch" type="xml">
        <form>
            <sheet>
                <group>
                    <field name="name"/>
                    <field name="category_id"
                           widget="many2one_badge"
                           options="{'color_field': 'color'}"/>
                    <field name="priority_id"
                           widget="many2one_badge"
                           options="{'color_field': 'color'}"/>
                </group>
            </sheet>
        </form>
    </field>
</record>

<record id="view_task_tree" model="ir.ui.view">
    <field name="name">my.task.tree</field>
    <field name="model">my.task</field>
    <field name="arch" type="xml">
        <tree>
            <field name="name"/>
            <field name="category_id" widget="many2one_badge"
                   options="{'color_field': 'color'}"/>
            <field name="priority_id" widget="many2one_badge"
                   options="{'color_field': 'color'}"/>
        </tree>
    </field>
</record>
```

## Available Colors

Odoo provides 12 predefined colors (indices 0–11):

| Index | Color |
|---|---|
| 0 | Grey (no color) |
| 1 | Red |
| 2 | Orange |
| 3 | Yellow |
| 4 | Light green |
| 5 | Green |
| 6 | Cyan |
| 7 | Light blue |
| 8 | Blue |
| 9 | Purple |
| 10 | Pink |
| 11 | Brown |

## Troubleshooting

### Badge is not colored

**Problem**: The badge appears but without color.

**Solution**: Make sure the related model has the `color` field (or the field specified in `color_field`) and that it contains a non-zero integer value.

### Widget not working after install

**Problem**: Module is installed but the widget has no effect.

**Solution**:
1. Clear browser cache (Ctrl+Shift+R)
2. Restart the Odoo server
3. Check the browser console for JavaScript errors

### Color not saved after clicking

**Solution**: Ensure the user has write access to the related model (e.g. `my.category`), since the color is saved directly on the related record via `orm.write`.

## Contributing

Contributions are welcome! Please open an issue or pull request on the project repository.
