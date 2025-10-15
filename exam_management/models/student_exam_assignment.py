from odoo import models, fields, api
from datetime import date, timedelta
from odoo.exceptions import ValidationError, UserError
import logging

_logger = logging.getLogger(__name__)

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
    
    
    @api.model
    def send_exam_reminder_email(self):
        """Send reminder email to students one day before the exam"""
        tomorrow = date.today() + timedelta(days=1)
        
        _logger.info(f"Running exam reminder for date: {tomorrow}")

        # Find all exams scheduled for tomorrow
        exam_planning = self.env['exam.planning'].search([
            ('exam_start_date', '=', tomorrow)
        ])
        
        if not exam_planning:
            _logger.info("No exams scheduled for tomorrow")
            return True
        
        _logger.info(f"Found {len(exam_planning)} exams for tomorrow: {exam_planning.mapped('exam_name')}")
        
        # Find all exam assignments for those exams
        assignments = self.search([
            ('exam_id', 'in', exam_planning.ids)
        ])
        
        if not assignments:
            _logger.info("No exam assignments found for tomorrow's exams")
            return True
        
        _logger.info(f"Found {len(assignments)} exam assignments for tomorrow's exams")
        
        # Group assignments by student to send one email per student
        students_exams = {}
        for assignment in assignments:
            student = assignment.student_id
            if student and student.email:
                students_exams.setdefault(student.id, {
                    'student': student,
                    'assignments': []
                })['assignments'].append(assignment)
        
        _logger.info(f"Sending reminders to {len(students_exams)} unique students")
        
        # --- Send Email ---
        template = self.env.ref('exam_management.mail_template_exam_reminder_assignment', raise_if_not_found=False)

        if not template:
            _logger.warning("Email template 'exam_management.mail_template_exam_reminder_assignment' not found.")
            return True

        for data in students_exams.values():
            student = data['student']
            assignments = data['assignments']
            example_assignment = assignments[0]  # template needs a record

            # Send the mail using the template
            mail_id = template.send_mail(example_assignment.id, force_send=True)
            _logger.info(f"Reminder email sent to {student.student_name} ({student.email})")

            # Log in chatter
            example_assignment.message_post(
                body=f"Exam reminder email sent to <b>{student.student_name}</b> ({student.email}) for tomorrow's exam(s).",
                subject="Exam Reminder",
                message_type="notification",
                subtype_xmlid="mail.mt_comment",
            )

        return True
