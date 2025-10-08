from odoo import models, fields

class PosOrder(models.Model):
    _inherit = 'pos.order'

    select_user = fields.Char(string="Selected User")
