from odoo import models, fields, api
import random

class ExamSeatingWizard(models.TransientModel):
    _name = 'exam.seating.wizard'
    _description = 'Exam Seating Wizard'

    exam_id = fields.Many2one('exam.planning', string="Exam", readonly=True, tracking=True)
    hall_id = fields.Many2one('exam.hall', string="Hall", readonly=True, tracking=True)
    hall_capacity = fields.Integer(string="Hall Capacity", related="hall_id.capacity", readonly=True, tracking=True)
    student_ids = fields.Many2many('student.registration', string="Assigned Students", readonly=True, tracking=True)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        hall = self.env['exam.hall'].browse(self._context.get('active_id'))
        if hall:
            exam = hall.exam_id
            res.update({
                'exam_id': exam.id,
                'hall_id': hall.id,
                'student_ids': [(6, 0, exam.assignment_ids.mapped('student_id').ids)]
            })
        return res

    def action_generate_seating(self):
        Seating = self.env['exam.seating']

        # assigned students
        existing_seats = Seating.search([
            ('exam_id', '=', self.exam_id.id),
            ('hall_id', '=', self.hall_id.id)
        ])
        already_assigned_students = existing_seats.mapped('student_id')

        new_students = self.student_ids - already_assigned_students

        if not new_students:
            return  # already seats exist

        if len(existing_seats) + len(new_students) > self.hall_capacity:
            raise ValueError("Not enough seats available in this hall")

        # seat number allocation (next available seat)
        used_seats = set(existing_seats.mapped('seat_number'))
        seat_no = 1
        for student in new_students:
            while seat_no in used_seats:
                seat_no += 1

            Seating.create({
                'exam_id': self.exam_id.id,
                'hall_id': self.hall_id.id,
                'student_id': student.id,
                'seat_number': seat_no,
            })

            used_seats.add(seat_no)
            seat_no += 1
