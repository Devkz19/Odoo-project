from odoo import models, fields, api
from odoo.exceptions import ValidationError

class StudentExamAssignment(models.Model):
    _name = 'student.exam.assignment'
    _description = 'Student Exam Assignment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'exam_id'

    student_id = fields.Many2one('student.registration', string="Student", ondelete='cascade', tracking=True, required=True)
    exam_id = fields.Many2one('exam.planning', string="Exam",tracking=True, required=True)
    subject_id = fields.Many2one('exam.subject', string="Subject", tracking=True)

    course = fields.Selection(
        related='student_id.course',
        store=True,
        string="Course",tracking=True
    )
    class_semester = fields.Selection(
        related='student_id.class_semester',
        store=True,
        string="Class & Semester",tracking=True
    )

    status = fields.Selection([
        ('assigned', 'Assigned'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], default='assigned', string="Status")

    assignment_date = fields.Date(
        string="Assigned On",
        default=fields.Date.today
    )
    attendance = fields.Selection(
        [("present", "Present"), ("absent", "Absent")],
        string="Attendance",
      
    )

    _sql_constraints = [
        ('unique_student_exam_subject', 'unique(student_id, exam_id, subject_id)', 
         'Student already assigned to this subject in exam!')
    ]
