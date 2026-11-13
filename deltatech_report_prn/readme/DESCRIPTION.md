Zebra label printers read ZPL text commands, not PDF. This technical module adds a *PRN* report type, so a QWeb template that outputs plain text can be printed from a report action as a `.prn` file.

- **PRN report type**: Report actions of type *PRN* render their template as plain text, not PDF.
- **File download**: The action downloads a `.prn` file named after the report or, for one record, after its `print_report_name` expression.
- **Extension point**: The module exports `buildPrnUrl`, so a companion module can intercept the action and print another way.

The module depends only on `web` and ships no reports or label templates. The workstation must send the downloaded file to the printer. On uninstall, PRN reports return to the default type.
