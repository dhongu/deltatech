1. Make sure the related model has a `color` field

```python
class MyCategory(models.Model):
    _name = 'my.category'
    _description = 'My Category'

    name = fields.Char(string='Name', required=True)
    color = fields.Integer(string='Color', default=0)
```

2. Use the widget in your view

```xml
<field name="category_id"
       widget="many2one_badge"
       options="{'color_field': 'color'}"/>
```

3. Available options

| Option | Description | Default |
|---|---|---|
| `color_field` | Name of the integer field on the related model that stores the color index | `'color'` |

```xml
<!-- Example with a custom color field -->
<field name="status_id"
       widget="many2one_badge"
       options="{'color_field': 'badge_color'}"/>
```

In readonly mode the field is displayed as a colored badge. In edit mode, clicking the badge opens a color picker popover, a remove button (`×`) appears on hover, and an autocomplete input lets you pick a new value when the field is empty.

Full Example
============

Python model

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

XML view

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

Available Colors
=================

Odoo provides 12 predefined colors (indices 0-11): 0 Grey (no color), 1 Red, 2 Orange, 3 Yellow, 4 Light green, 5 Green, 6 Cyan, 7 Light blue, 8 Blue, 9 Purple, 10 Pink, 11 Brown.

Troubleshooting
================

**Badge is not colored** — make sure the related model has the `color` field (or the field specified in `color_field`) and that it contains a non-zero integer value.

**Widget not working after install** — clear the browser cache (Ctrl+Shift+R), restart the Odoo server, and check the browser console for JavaScript errors.

**Color not saved after clicking** — ensure the user has write access to the related model (e.g. `my.category`), since the color is saved directly on the related record via `orm.write`.
