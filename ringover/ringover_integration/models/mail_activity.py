from odoo import models, api

class MailActivity(models.Model):
    _inherit = 'mail.activity'

    @api.model
    def _ringover_mark_as_done(self, phone_number):
        # Find the partner with the given phone number
        partner = self.env['res.partner'].search([('phone', '=', phone_number)], limit=1)
        if partner:
            # Find the open call activity for this partner
            activity = self.search([
                ('res_model', '=', 'res.partner'),
                ('res_id', '=', partner.id),
                ('activity_type_id.name', '=', 'Call'),
                ('state', '!=', 'done')
            ], limit=1)
            if activity:
                # Mark the activity as done
                activity.action_feedback(feedback='Call completed via Ringover in odoo')
                return True
        return False
