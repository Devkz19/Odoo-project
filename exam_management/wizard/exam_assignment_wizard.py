from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import date

class ExamAssignmentWizard(models.TransientModel):
    _name = 'exam.assignment.wizard'
    _description = 'Exam Assignment Wizard'

    class_semester = fields.Selection([
        ('fy_sem1', 'First Year - Semester 1'),
        ('fy_sem2', 'First Year - Semester 2'),
        ('sy_sem3', 'Second Year - Semester 3'),
        ('sy_sem4', 'Second Year - Semester 4'),
        ('ty_sem5', 'Third Year - Semester 5'),
        ('ty_sem6', 'Third Year - Semester 6'),
        ('ly_sem7', 'Fourth Year - Semester 7'),
        ('ly_sem8', 'Fourth Year - Semester 8'),
    ], string='Class & Semester', required=True)
    
    exam_id = fields.Many2one(
    'exam.planning',
    string="Exam",
    required=True
    )
    # exam_name = fields.Char(string="Exam Name", related="exam_id.exam_planning", store=False, readonly=True)
   
    
    course = fields.Selection([
        ('IT', 'Information Technology'),
        ('CS', 'Computer Science'),
        ('EC', 'Electronics'),
        ('ME', 'Mechanical'),
        ('CE', 'Civil'),
        ('EE', 'Electrical'),
        ('BT', 'Biotechnology'),
        ('CH', 'Chemical'),
    ], string='Course', required=True)

    @api.model
    def default_get(self, fields_list):
        """Set default values if required."""
        res = super(ExamAssignmentWizard, self).default_get(fields_list)
        active_id = self.env.context.get('active_id')
        if active_id:
            exam = self.env['exam.planning'].browse(active_id)
            res.update({
                'class_semester': exam.class_semester,
                'exam_id': exam.id,
                'course': exam.course,
            })
        return res

    def assign_exam(self):
        """Assign the clicked exam (with all its subjects) to all matching students."""
        students = self.env['student.registration'].search([
            ('class_semester', '=', self.class_semester),
            ('course', '=', self.course)
        ])

        if not students:
            raise UserError("No students found for this Class/Semester and Course.")

        assignment_model = self.env['student.exam.assignment']
        created_count = 0

        for student in students:
            for subject in self.exam_id.subject_ids:
                exists = assignment_model.search([
                    ('student_id', '=', student.id),
                    ('exam_id', '=', self.exam_id.id),
                    ('subject_id', '=', subject.id)
                ], limit=1)

                if not exists:
                    assignment_model.create({
                        'student_id': student.id,
                        'exam_id': self.exam_id.id,
                        'subject_id': subject.id,
                        'class_semester': self.class_semester,
                        'course': self.course,
                        'assignment_date': date.today()
                    })
                    created_count += 1

        if created_count == 0:
            raise UserError("All selected students already have this exam (with subjects) assigned.")

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Exam Assignment Completed',
                'message': f'{created_count} subject assignments created.',
                'type': 'success',
                'sticky': False,
            }
        }
        
    _sql_constraints = [
    ('unique_assignment', 'unique(student_id, exam_id, subject_id)',
     'Student already assigned to this subject in exam!')
]

