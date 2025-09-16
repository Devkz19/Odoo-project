from odoo import models, fields

class ExamHall(models.Model):
    _name = 'exam.hall'
    _description = 'Exam Hall'
    _order = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    
    name = fields.Char(string="Hall Name", required=True, tracking=True)
    code = fields.Char(string='Code', help='Short code like H1, A-101', tracking=True)
    capacity = fields.Integer(required=True, default=30, tracking=True)
    location = fields.Char(tracking=True)
    note = fields.Text(tracking=True)
    hall_id = fields.Char(string='Hall ID', help='Unique identifier for the hall', tracking=True)
    active = fields.Boolean(default=True, tracking=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    course = fields.Selection([
        ('IT', 'Information Technology'),
        ('CS', 'Computer Science'),
        ('EC', 'Electronics'),
        ('ME', 'Mechanical'),
        ('CE', 'Civil'),
        ('EE', 'Electrical'),
        ('BT', 'Biotechnology'),
        ('CH', 'Chemical'),
    ], string='Course', required=True, tracking=True)

    # Link to Exam Planning (Many2one, because one hall is assigned to one exam at a time)
    exam_id = fields.Many2one(
        'exam.planning',
        string="Exam",
        required=True,
        help="Select the exam for which this hall is assigned",
        tracking=True,
        ondelete='cascade'
    )

    _sql_constraints = [
        ('capacity_positive', 'CHECK(capacity > 0)', 'Capacity must be greater than zero.'),
    ]