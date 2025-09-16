from odoo import models, fields, api, _

class RestDepartment(models.Model):
    _name = 'rest.department'
    _description = 'This model will store data of our departments'
    _rec_name = 'seq_num'
    
    @api.model
    def create(self, vals):
        if vals.get("seq_num") in [None, 'New']:
            vals["seq_num"] = self.env['ir.sequence'].next_by_code('rest.seq.staff') or 'New'
        res = super(RestDepartment, self).create(vals)
        return res

    name = fields.Char(string="Name")
    seq_num = fields.Char(string="Sequence Number", required=True, copy=False, readonly=True, default='New')
    sequence = fields.Integer(string ="Seq")
    
    def name_get(self):
        result = []
        for rec in self:
            name = rec.seq_num + '- ['+ rec.name + ']'
            result.append((rec.id, name))
            
        return result