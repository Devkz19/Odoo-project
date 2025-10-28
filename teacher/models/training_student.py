from odoo import models, fields, api
# Add a new model students showing: name, age, course.

class TrainingStudent(models.Model):
    _name = "training.student"
    _description = "Training Student"
    _rec_name = "name"
    
    name = fields.Char(string='Name', required=True)
    age = fields.Integer(string='Age', required=True)
    course = fields.Char(string='Course', required=True)
    teacher_id = fields.Many2many('training.teacher', string='Teachers')

# Add a state field to training.student (draft, confirmed, alumni).
    status = fields.Selection([
    ('draft', 'Draft'),
    ('confirm', 'Confirmed'),
    ('alumni', 'Alumni'),
], string="Status", default='draft', tracking=True)
    
    def action_confirm(self):
        self.write({'status': 'confirm'})
    
    def action_set_alumni(self):
        self.write({'status': 'alumni'})
    
    def action_reset_draft(self):
        self.write({'status': 'draft'})