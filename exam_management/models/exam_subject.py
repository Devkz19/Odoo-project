from odoo import models, fields

class ExamSubject(models.Model):
    _name = "exam.subject"
    _description = "Exam Subject"

    name = fields.Char("Subject Name", required=True)
    exam_id = fields.Many2one(
        'exam.planning',
        string="Exam",
        ondelete='cascade'
    )
    total_marks = fields.Integer("Total Marks", required=True)
    exam_date = fields.Date("Exam Date")   
    exam_time = fields.Float("Exam Time")  
    state = fields.Selection(
        [
            ("new", "New"),
            ("confirm", "Confirmed"),
        ],
        string="Status",
        default="new",  
        tracking=True
    )
    
    def action_new(self):
        """ Reset back to New state """
        for rec in self:
            rec.state = "new"

    def action_confirm(self):
        """ Move to Confirmed state """
        for rec in self:
            rec.state = "confirm"