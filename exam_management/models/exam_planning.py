from odoo import models, fields, api
from odoo.exceptions import ValidationError

class ExamPlanning(models.Model):
    _name = 'exam.planning'
    _description = 'Exam Planning'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'exam_name'

    exam_name = fields.Char('Exam Name', required=True, tracking=True)
    exam_code = fields.Char('Exam Code', required=True, tracking=True)
    exam_start_date = fields.Date('Exam Start Date', tracking=True)
    exam_end_date = fields.Date('Exam End Date', tracking=True)

    exam_datetime = fields.Datetime('Exam Schedule', compute="_compute_exam_datetime", store=False)

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

    class_semester = fields.Selection([
        ('fy_sem1', 'First Year - Semester 1'),
        ('fy_sem2', 'First Year - Semester 2'),
        ('sy_sem3', 'Second Year - Semester 3'),
        ('sy_sem4', 'Second Year - Semester 4'),
        ('ty_sem5', 'Third Year - Semester 5'),
        ('ty_sem6', 'Third Year - Semester 6'),
        ('ly_sem7', 'Fourth Year - Semester 7'),
        ('ly_sem8', 'Fourth Year - Semester 8'),
    ], string='Class & Semester', required=True, tracking=True)

    exam_time = fields.Float('Exam Time', required=True, help="Time in 24-hour format (e.g., 14.5 for 2:30 PM)", tracking=True)
    duration = fields.Float('Duration (Hours)', required=True, tracking=True)
    total_marks = fields.Integer('Total Marks', required=True, tracking=True)

    # subject with One2many
    subject_ids = fields.One2many(
        'exam.subject',
        'exam_id',
        string="Subjects",
        tracking=True
    )

    assignment_ids = fields.One2many(
        'student.exam.assignment',
        'exam_id',
        string="Exam Assignments",
        tracking=True
    )
    hall_ids = fields.One2many(
        'exam.hall',
        'exam_id',
        string="Halls",
        tracking=True
    )
    instructions = fields.Text('Instructions', tracking=True)
    registration_deadline = fields.Date('Registration Deadline', required=True, tracking=True)
    active = fields.Boolean('Active', default=True, tracking=True)
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

    # Validation for correct date order
    @api.constrains('exam_start_date', 'exam_end_date', 'registration_deadline')
    def _check_dates(self):
        for record in self:
            if record.exam_end_date < record.exam_start_date:
                raise ValidationError("Exam End Date cannot be earlier than Start Date.")
            if record.registration_deadline >= record.exam_start_date:
                raise ValidationError("Registration deadline must be before Exam Start Date.")
            
    @api.model
    def format_float_time(self, float_time):
        """Convert float time (14.5) -> string (14:30)"""
        if float_time is False:
            return ""
        hours = int(float_time)
        minutes = int(round((float_time - hours) * 60))
        return f"{hours:02d}:{minutes:02d}"        

    # Example: compute datetime from start date
    @api.depends('exam_start_date', 'exam_time')
    def _compute_exam_datetime(self):
        for rec in self:
            if rec.exam_start_date:
                hours = int(rec.exam_time)
                minutes = int((rec.exam_time - hours) * 60)
                rec.exam_datetime = fields.Datetime.to_datetime(
                    f"{rec.exam_start_date} {hours:02d}:{minutes:02d}:00"
                )
            else:
                rec.exam_datetime = False