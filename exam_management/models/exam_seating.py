from odoo import models, fields, api
from odoo.exceptions import ValidationError

class ExamSeating(models.Model):
    _name = 'exam.seating'
    _description = 'Exam Seating'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'student_id'

    exam_id = fields.Many2one('exam.planning', string="Exam", required=True)
    hall_id = fields.Many2one('exam.hall', string="Hall", required=True)
    student_id = fields.Many2one('student.registration', string="Student", required=True)
    seat_number = fields.Integer("Seat Number", required=True)
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

    @api.constrains('exam_id', 'hall_id', 'seat_number')
    def _check_unique_seat(self):
        for rec in self:
            existing = self.search([
                ('exam_id', '=', rec.exam_id.id),
                ('hall_id', '=', rec.hall_id.id),
                ('seat_number', '=', rec.seat_number),
                ('id', '!=', rec.id)
            ], limit=1)
            if existing:
                raise ValidationError(
                    f"Seat {rec.seat_number} already exists in hall {rec.hall_id.name} for exam {rec.exam_id.name}."
                )

    def name_get(self):
        result = []
        for record in self:
            student_name = record.student_id.name or "Unknown"
            seat = f"{record.seat_number:03d}" if record.seat_number else "?"
            display_name = f"{student_name} - Seat {seat}"
            result.append((record.id, display_name))
        return result
