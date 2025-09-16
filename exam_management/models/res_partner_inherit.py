from odoo import models, fields

class ResPartner(models.Model):
    _inherit = "res.partner"

    is_student = fields.Boolean(string="Is Student")
    student_id = fields.Char(string="Student ID")
    class_semester = fields.Char(string="Class/Semester")
    course = fields.Char(string="Course")