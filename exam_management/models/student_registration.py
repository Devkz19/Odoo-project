from odoo import models, fields, api
from datetime import date, timedelta
from odoo.exceptions import ValidationError, UserError
import logging
import base64

_logger = logging.getLogger(__name__)

class StudentRegistration(models.Model):
    _name = 'student.registration'
    _description = 'Student Registration'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'student_name'
   

    student_name = fields.Char(string='Student Name', required=True, tracking=True)
    student_id = fields.Char(
        string='Enrollment ID',
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default='New'
    )
    exam_id = fields.Many2one('exam.planning', string="Exam", required=False, tracking=True)
    student_count = fields.Integer(string="Total Students", compute="_compute_student_count", store=False)
    student_count_confirmed = fields.Integer(string="Confirmed Students", compute="_compute_student_count")
    student_count_cancelled = fields.Integer(string="Cancelled Students", compute="_compute_student_count")
    image_1920 = fields.Image("Profile Picture", max_width=1920, max_height=1920)
  
    
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
    
    status = fields.Selection([
        ('assigned', 'Assigned'),
        ('completed', 'Completed'),
    ], default='assigned', tracking=True)
    
    state = fields.Selection([
    ('confirm', 'Confirmed'),
    ('cancel', 'Cancelled'),
], string="Registration Status", default='confirm', tracking=True)

    marks_obtained = fields.Float()
    pass_fail = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'Not Attempted'),
    ], string="Result", compute="_compute_pass_fail", store=True)

    @api.depends('marks_obtained', 'status')
    def _compute_pass_fail(self):
        for rec in self:
            if rec.status != 'completed':
                rec.pass_fail = 'na'
            elif rec.marks_obtained >= 33:  
                rec.pass_fail = 'pass'
            else:
                rec.pass_fail = 'fail'
    
    email = fields.Char(string='Email', required=True, tracking=True)
    phone = fields.Char(string='Phone Number', tracking=True)
    user_id = fields.Many2one(
    'res.users',
    string="Related User",
    ondelete="cascade"
)

    assignment_ids = fields.One2many(
        'student.exam.assignment',
        'student_id',
        string="Exam Assignments"
    )

    _sql_constraints = [
        ('unique_student_email', 'unique(email)', 'This email is already registered.'),
        ('unique_student_id', 'unique(student_id)', 'Enrollment ID must be unique.'),
    ]

    @api.depends_context('uid')
    def _compute_student_count(self):
        # Count confirmed and cancelled students separately
        confirmed_count = self.env['student.registration'].search_count([('state', '=', 'confirm')])
        cancelled_count = self.env['student.registration'].search_count([('state', '=', 'cancel')])
        for rec in self:
            rec.student_count_confirmed = confirmed_count
            rec.student_count_cancelled = cancelled_count
            # Optional: keep total as before
            rec.student_count = confirmed_count + cancelled_count

    def action_count_students(self, state=None):
        """Open student registrations filtered by state"""
        domain = []
        if state in ['confirm', 'cancel']:
            domain = [('state', '=', state)]
        return {
            'type': 'ir.actions.act_window',
            'name': 'Student Registrations',
            'res_model': 'student.registration',
            'view_mode': 'list,form',
            'domain': domain,
        }    
    
    def action_confirm(self):
        for rec in self:
            rec.state = 'confirm'

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancel'
    
    def action_send_test_email(self):
            """Manual trigger to test email sending"""
            template = self.env.ref(
                'exam_management.mail_template_student_registration_success',
                raise_if_not_found=False
            )
            if not template:
                raise UserError("Email template not found. Please check XML ID.")
            for record in self:
                template.send_mail(record.id, force_send=True)
                
    def action_view_total_students(self):
        return self.env.ref('exam_management.action_student_registration').read()[0]

    def action_view_confirmed_students(self):
        return self.env.ref('exam_management.action_student_registration_confirmed').read()[0]

    def action_view_cancelled_students(self):
        return self.env.ref('exam_management.action_student_registration_cancelled').read()[0]


    @api.model
    def create(self, vals):
        # Always use sequence for student_id
        if vals.get('student_id', 'New') == 'New':
            vals['student_id'] = self.env['ir.sequence'].next_by_code('student.registration') or 'New'

        # Create student record
        record = super(StudentRegistration, self).create(vals)

        # Auto-create or link portal user
        if vals.get('email'):
            existing_user = self.env['res.users'].sudo().search([('login', '=', vals['email'])], limit=1)
            if not existing_user:
                portal_group = self.env.ref('base.group_portal')
                user_vals = {
                    'name': record.student_name,
                    'login': vals['email'],
                    'email': vals['email'],
                    'groups_id': [(6, 0, [portal_group.id])]
                }
                new_user = self.env['res.users'].sudo().create(user_vals)
                record.user_id = new_user.id
                # Send password reset invite
                new_user.sudo().action_reset_password()
            else:
                record.user_id = existing_user.id

        # Try sending registration email + log in chatter
        try:
            template = self.env.ref(
                'exam_management.mail_template_student_registration_success',
                raise_if_not_found=False
            )
            if template:
                template.send_mail(record.id, force_send=True)
                record.message_post_with_template(template.id)
                _logger.info("Registration email sent to %s and logged in chatter", record.email)
            else:
                _logger.warning("Email template not found for student registration")
        except Exception as e:
            _logger.error("Failed to send registration email: %s", e)

        return record

