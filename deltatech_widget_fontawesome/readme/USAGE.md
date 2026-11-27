The module adds no menu. Add the widget to a `char`, `text` or `selection` field that stores a
Font Awesome class name:

```xml
<field name="icon" widget="fontawesome"/>
```

The examples below put the widget on the **Icon** field of the activity types, in developer mode:
**Settings → Technical → Activities → Activity Types**.

1. **Icons in a list.** The **Icon** column shows the icon of each activity type instead of its class
   name. A record with no value has an empty cell.

   ![Activity Types list with six types: the highlighted Icon column shows a check mark for To-Do, an envelope for Email and a phone for Call, while the Customer visit row has an empty cell](static/description/en/01_lista_tipuri_pictograme.png)

2. **Icon in a form.** On the **Call** activity type, the **Icon** field shows the phone icon instead
   of the text `fa-phone`. Hovering the icon shows the class name as tooltip. The widget only displays
   the value: the field cannot be edited in a view that uses it.

   ![Call activity type form with the Phonecall action: the Icon label is highlighted and the phone icon is shown next to it instead of the text fa-phone](static/description/en/02_formular_pictograma.png)

3. **Empty field.** A record with no icon, such as **Customer visit**, opens normally and the field
   stays empty, with no icon and no tooltip.

   ![Customer visit activity type form with the None action: the Icon label is highlighted, the field next to it is empty and the form is displayed without any error](static/description/en/03_formular_fara_pictograma.png)
