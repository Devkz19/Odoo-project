from odoo import models, fields

class PosOrder(models.Model):
    _inherit = 'pos.order'

    sales_person_id = fields.Many2one(
        comodel_name='res.users',
        string='Sales Person',
        help="The user (sales person) who handled this Point of Sale order."
    )
    
   