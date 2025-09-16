from odoo import models, fields, api

class ExamConducting(models.Model):
    _name = 'exam.conducting'
    _description = 'Exam Conducting'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'exam_id'

    _sql_constraints = [
        ('unique_exam_hall_conducting', 'unique(exam_id, hall_id)',
         'This exam is already being conducted in the selected hall.')
    ]

    exam_id = fields.Many2one('exam.planning', string="Exam", required=True, tracking=True)
    hall_id = fields.Many2one('exam.hall', string="Hall", required=True, tracking=True)
    invigilator_id = fields.Many2one('res.users', string="Invigilator", required=True, tracking=True)

    status = fields.Selection([
        ('not_started', 'Not Started'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
    ], string="Exam Status", default="not_started", tracking=True)

    student_line_ids = fields.One2many('exam.conducting.line', 'conducting_id', string="Students")

    exam_start_date = fields.Date(
        'Exam Start Date', related='exam_id.exam_start_date',
        store=True, tracking=True
    )
    exam_end_date = fields.Date(
        'Exam End Date', related='exam_id.exam_end_date',
        store=True, tracking=True
    )

    start_time = fields.Datetime(string="Start Time", tracking=True)
    end_time = fields.Datetime(string="End Time", tracking=True)
    
    state = fields.Selection([
        ('start', 'Not Started'),
        ('ongoing', 'Ongoing'),
        ('end', 'End'),
    ], string="Exam Status", default='start', tracking=True)

    def action_start(self):
        """Move exam to Ongoing"""
        for rec in self:
            rec.state = 'ongoing'

    def action_end(self):
        """Move exam to End"""
        for rec in self:
            rec.state = 'end'     
            if rec.exam_id:
                rec.exam_id.state = 'confirm'

    @api.onchange('exam_id')
    def _onchange_exam_id(self):
        """ Auto-populate hall, exam dates, and student lines when exam is selected """
        if self.exam_id:
            exam = self.exam_id

            # Default hall (first hall from exam planning halls)
            self.hall_id = exam.hall_ids and exam.hall_ids[0].id or False

            # Clear old lines & refill with students + subjects
            assignments = self.env['student.exam.assignment'].search([('exam_id', '=', exam.id)])
            lines = [(5, 0, 0)]
            for assign in assignments:
                lines.append((0, 0, {
                    'assignment_id': assign.id,
                    'student_id': assign.student_id.id,
                    'subject_id': assign.subject_id.id if assign.subject_id else False,
                    'attendance': 'absent',
                }))
            self.student_line_ids = lines
            
    def _get_report_base_filename(self):
        return "Exam Report"

# Expose helper to QWeb
    def format_float_time(self, float_time):
        return self.env['exam.planning'].format_float_time(float_time)


    def action_start_exam(self):
        self.write({
            'status': 'ongoing',
            'start_time': fields.Datetime.now()
        })
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def action_end_exam(self):
        self.write({
            'status': 'completed',
            'end_time': fields.Datetime.now()
        })
        return {'type': 'ir.actions.client', 'tag': 'reload'}
    
    def action_send_invigilator_email(self):
        """Send email to assigned invigilator"""
        template = self.env.ref("exam_management.mail_template_invigilator_assignment")
        for record in self:
            if template and record.invigilator_id and record.invigilator_id.email:
                template.send_mail(record.id, force_send=True)


class ExamConductingLine(models.Model):
    _name = 'exam.conducting.line'
    _description = 'Exam Conducting Student Line'
    _rec_name = 'student_id'

    conducting_id = fields.Many2one('exam.conducting', string="Exam Conducting", required=True, ondelete='cascade')

    assignment_id = fields.Many2one('student.exam.assignment', string="Exam Assignment", required=True, ondelete="cascade")

    student_id = fields.Many2one(
        related="assignment_id.student_id",
        string="Student",
        store=True,
        readonly=True
    )

    subject_id = fields.Many2one(
        "exam.subject",
        string="Subject",
        store=True,
        readonly=True,
        related="assignment_id.subject_id" 
    )

    enrollment_id = fields.Char(
        related="assignment_id.student_id.student_id",
        string="Enrollment ID",
        store=True,
        readonly=True
    )

    attendance = fields.Selection([
        ('present', 'Present'),
        ('absent', 'Absent'),
    ], string="Attendance", default="absent")
