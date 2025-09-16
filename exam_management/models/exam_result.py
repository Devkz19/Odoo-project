from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

import logging
_logger = logging.getLogger(__name__)


class ExamResult(models.Model):
    _name = "exam.result"
    _description = "Exam Result"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'display_name'

    exam_id = fields.Many2one(
        "exam.planning", string="Exam", required=True, tracking=True
    )
    student_id = fields.Many2one(
        "student.registration", string="Student", required=True, tracking=True
    )

    subject_line_ids = fields.One2many(
        "exam.result.line", "result_id", string="Subjects"
    )

    marks_obtained = fields.Float(
        string="Marks Obtained",
        compute='_compute_totals_from_lines',
        store=True, tracking=True
    )
    total_marks = fields.Float(
        string="Total Marks",
        compute='_compute_totals_from_lines',
        store=True, tracking=True
    )

    percentage = fields.Float(
        string="Percentage",
        compute="_compute_percentage_and_grade",
        store=True, readonly=True
    )
    grade = fields.Selection(
        [("A", "A"), ("B", "B"), ("C", "C"), ("D", "D"), ("F", "Fail")],
        string="Grade", compute="_compute_percentage_and_grade",
        store=True, readonly=True, tracking=True
    )
    result_status = fields.Selection(
        [("pass", "Pass"), ("fail", "Fail")],
        string="Result", compute="_compute_percentage_and_grade",
        store=True, readonly=True, tracking=True
    )

    display_name = fields.Char(
        string="Display Name", compute="_compute_display_name", store=True
    )
    category = fields.Selection(
    [
        ("distinction", "Distinction"),
        ("first_class", "First Class (First Division)"),
        ("second_class", "Second Class (Second Division)"),
        ("pass_class", "Pass Class (Third Division)"),
        ("fail", "Fail"),
    ],
    string="Result Category",
    compute="_compute_percentage_and_grade",
    store=True,
    readonly=True,
    tracking=True,
    help="Academic classification based on percentage"
)

    @api.depends("student_id.student_name", "exam_id.exam_name")
    def _compute_display_name(self):
        for rec in self:
            if rec.student_id and rec.exam_id:
                rec.display_name = f"{rec.student_id.student_name} - {rec.exam_id.exam_name}"
            else:
                rec.display_name = "New Result"

    @api.depends('subject_line_ids.marks_obtained', 'subject_line_ids.total_marks')
    def _compute_totals_from_lines(self):
        for rec in self:
            rec.total_marks = sum(line.total_marks for line in rec.subject_line_ids)
            rec.marks_obtained = sum(line.marks_obtained for line in rec.subject_line_ids)

    @api.depends("marks_obtained", "total_marks", "subject_line_ids.attendance")
    def _compute_percentage_and_grade(self):
        for rec in self:
            # Rule: if absent in any subject → auto fail
            if any(line.attendance == "absent" for line in rec.subject_line_ids):
                rec.marks_obtained = 0.0
                rec.total_marks = 0.0
                rec.percentage = 0.0
                rec.result_status = "fail"
                rec.grade = "F"
                rec.category = "fail"  
                continue

            if rec.total_marks > 0:
                rec.percentage = (rec.marks_obtained / rec.total_marks) * 100.0
                passing = all(line.grade != 'F' for line in rec.subject_line_ids)

                if rec.percentage < 33 or not passing:
                    rec.result_status = "fail"
                    rec.grade = "F"
                    rec.category = "fail"   
                else:
                    rec.result_status = "pass"
                    # Grade calculation
                    if rec.percentage >= 85:
                        rec.grade = "A"
                    elif rec.percentage >= 70:
                        rec.grade = "B"
                    elif rec.percentage >= 55:
                        rec.grade = "C"
                    else:
                        rec.grade = "D"

                    # Category classification
                    if rec.percentage >= 75:
                        rec.category = "distinction"
                    elif rec.percentage >= 60:
                        rec.category = "first_class"
                    elif rec.percentage >= 50:
                        rec.category = "second_class"
                    elif rec.percentage >= 40:
                        rec.category = "pass_class"
                    else:
                        rec.category = "fail"  
            else:
                rec.percentage = 0.0
                rec.grade = 'F'
                rec.result_status = 'fail'
                rec.category = 'fail' 

    @api.onchange("exam_id", "student_id")
    def _onchange_exam_id_student_id(self):
        """
        Populates subject lines based on the selected exam and student.
        It fetches the attendance status from the exam conducting records.
        """
        if self.exam_id and self.student_id:
            # Clear existing lines to prevent duplicates
            self.subject_line_ids = [(5, 0, 0)]
            
            lines_vals = []
            assignments = self.env['student.exam.assignment'].search([
                ('exam_id', '=', self.exam_id.id),
                ('student_id', '=', self.student_id.id)
            ])

            for assign in assignments:
                conducting_line = self.env['exam.conducting.line'].search([
                    ('conducting_id.exam_id', '=', self.exam_id.id),
                    ('student_id', '=', self.student_id.id),
                    ('subject_id', '=', assign.subject_id.id),
                ], limit=1)

                # Debug logging
                _logger.info(f"Subject: {assign.subject_id.name}")
                _logger.info(f"Conducting line found: {bool(conducting_line)}")
                if conducting_line:
                    _logger.info(f"Conducting line attendance: {conducting_line.attendance}")
                _logger.info(f"Assignment attendance: {assign.attendance}")

                # Fix: Properly handle the attendance status priority
                if conducting_line and conducting_line.attendance:
                    attendance_status = conducting_line.attendance
                    _logger.info(f"Using conducting line attendance: {attendance_status}")
                    print(f"attendance_status (from conducting line): {attendance_status}")
                elif assign.attendance:
                    attendance_status = assign.attendance
                    _logger.info(f"Using assignment attendance: {attendance_status}")
                    print(f"attendance_status check (from assignment): {attendance_status}")
                else:
                    attendance_status = 'present'
                    _logger.info(f"Using default attendance: {attendance_status}")
                    print(f"attendance_status default: {attendance_status}")

                vals = {
                    'subject_id': assign.subject_id.id,
                    'attendance': attendance_status,
                }

                if attendance_status == 'absent':
                    vals['marks_obtained'] = 0.0

                lines_vals.append((0, 0, vals))

            self.subject_line_ids = lines_vals
        else:
            self.subject_line_ids = [(5, 0, 0)]


class ExamResultLine(models.Model):
    _name = "exam.result.line"
    _description = "Exam Result Subject Line"
    _rec_name = 'subject_id'

    result_id = fields.Many2one("exam.result", string="Result", ondelete="cascade", required=True)
    subject_id = fields.Many2one("exam.subject", string="Subject", required=True)

    attendance = fields.Selection(
        [("present", "Present"), ("absent", "Absent")],
        string="Attendance",
        default="present"
    )

    total_marks = fields.Integer(
        string="Total Marks",
        related="subject_id.total_marks",
        store=True,
        readonly=True
    )
    marks_obtained = fields.Float("Marks Obtained", default=0.0)

    percentage = fields.Float(
        string="Percentage",
        compute="_compute_percentage_and_grade",
        store=True,
        readonly=True
    )
    grade = fields.Selection(
        [("A", "A"), ("B", "B"), ("C", "C"), ("D", "D"), ("F", "Fail")],
        string="Grade",
        compute="_compute_percentage_and_grade",
        store=True,
        readonly=True
    )

    @api.depends("marks_obtained", "total_marks", "attendance")
    def _compute_percentage_and_grade(self):
        for line in self:
            if line.attendance == 'absent' or line.total_marks == 0:
                line.percentage = 0.0
                line.grade = 'F'
            else:
                line.percentage = (line.marks_obtained / line.total_marks) * 100.0
                if line.percentage < 33:
                    line.grade = "F"
                elif line.percentage >= 85:
                    line.grade = "A"
                elif line.percentage >= 70:
                    line.grade = "B"
                elif line.percentage >= 55:
                    line.grade = "C"
                else:
                    line.grade = "D"

    # @api.onchange('attendance')
    # def _onchange_attendance(self):
    #     """Auto reset marks if absent"""
    #     if self.attendance == 'absent':
    #         self.marks_obtained = 0.0
    
    @api.onchange("marks_obtained", "attendance")
    def _onchange_absent_marks(self):
        if self.attendance == "absent" and self.marks_obtained > 0:
            # reset value
            self.marks_obtained = 0.0
            # show popup to user
            raise UserError(
                f"You cannot enter marks for '{self.subject_id.name}' "
                f"as the student was absent."
            )        

    # @api.constrains('marks_obtained', 'attendance')
    # def _check_absent_marks(self):
    #     for line in self:
    #         if line.attendance == 'absent' and line.marks_obtained > 0:
    #             raise ValidationError(
    #                 f"You cannot enter marks for '{line.subject_id.name}' "
    #                 f"as the student was absent."
    #             )
    #         print(f"line.attendance (constraint): {line.attendance}")
