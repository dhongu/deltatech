from odoo import _, models
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = "account.move"

    def action_post(self):
        res = super().action_post()
        is_validation_enabled = self.env.company.analytic_distribution_validation_enabled
        if is_validation_enabled and self.move_type in ["in_invoice", "in_refund"]:
            for line in self.invoice_line_ids:
                if not line.analytic_distribution:
                    raise ValidationError(_("Analytic distribution is required for all invoice lines."))
                analytic_distribution = line.analytic_distribution
                total_percentage = 0.0

                for key, value in analytic_distribution.items():
                    # Validate the key has exactly three numbers
                    numbers = key.split(",")
                    if len(numbers) != 3:
                        raise ValidationError(
                            _(
                                "Invalid distribution, all distribution lines need to have: Location, Department and Line of Business."
                            )
                        )

                    try:
                        percentage = float(value)
                        total_percentage += percentage
                    except ValueError as err:
                        raise ValidationError(
                            _("Invalid value in analytic distribution: %s. It must be a number.") % value
                        ) from err

                # Check if the total percentage adds up to 100
                if total_percentage != 100.0:  # Allowing small floating-point errors
                    raise ValidationError(
                        _("The total percentage in analytic distribution must add up to 100. Found: %s.")
                        % total_percentage
                    )

        return res
