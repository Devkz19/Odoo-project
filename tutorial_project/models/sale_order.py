from odoo import fields, models

class SaleOrder(models.Model):
    _inherit ='sale.order'
    
    test = fields.Char(string="Test Field")
    staff_id = fields.Many2one('rest.staff',string="Staff")