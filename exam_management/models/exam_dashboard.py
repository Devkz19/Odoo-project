from odoo import models, fields, api
from datetime import date
import logging

_logger = logging.getLogger(__name__)

class ExamDashboard(models.TransientModel):
    _name = 'exam.dashboard'
    _description = 'Exam Dashboard'
    _rec_name = 'display_name'

    # KPI fields
    total_exams = fields.Integer(string='Total Exams', readonly=True)
    total_students = fields.Integer(string='Total Students', readonly=True)
    total_halls = fields.Integer(string='Total Halls', readonly=True)
    total_seatings = fields.Integer(string='Total Seatings', readonly=True)

    # HTML table fields for display
    upcoming_exams_table = fields.Html(string="Upcoming Exams Table", readonly=True)
    exams_today_table = fields.Html(string="Exams Today Table", readonly=True)
    unassigned_students_table = fields.Html(string="Unassigned Students Table", readonly=True)

    display_name = fields.Char(
        string="Dashboard Name",
        compute='_compute_display_name',
        store=False
    )

    @api.depends('create_date')
    def _compute_display_name(self):
        for record in self:
            record.display_name = f"Exam Dashboard - {fields.Date.context_today(record)}"

    def _get_exam_planning_url(self, exam_id):
        """Generate URL for exam planning record"""
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        return f"{base_url}/web#id={exam_id}&model=exam.planning&view_type=form"

    def _get_student_registration_url(self, student_id):
        """Generate URL for student registration record"""
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        return f"{base_url}/web#id={student_id}&model=student.registration&view_type=form"

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        today = date.today()

        try:
            # KPI counts
            res['total_exams'] = self.env['exam.planning'].search_count([])
            res['total_students'] = self.env['student.registration'].search_count([])
            res['total_halls'] = self.env['exam.hall'].search_count([])
            res['total_seatings'] = self.env['exam.seating'].search_count([])

            # Get selection mappings
            course_mapping = dict(self.env['exam.planning'].fields_get(allfields=['course'])['course']['selection'])
            semester_mapping = dict(self.env['exam.planning'].fields_get(allfields=['class_semester'])['class_semester']['selection'])

            # ========== UPCOMING EXAMS TABLE ==========
            upcoming = self.env['exam.planning'].search(
                [('exam_start_date', '>', today), ('active', '=', True)],
                order='exam_start_date asc',
                limit=10
            )

            upcoming_html_rows = []
            for rec in upcoming:
                try:
                    time_str = 'No Time'
                    if hasattr(rec, 'exam_time') and rec.exam_time:
                        hours = int(rec.exam_time)
                        minutes = int((rec.exam_time - hours) * 60)
                        time_str = f"{hours:02d}:{minutes:02d}"

                    course_full_name = course_mapping.get(rec.course, "No Course")
                    semester_full_name = semester_mapping.get(rec.class_semester, "No Semester")
                    exam_date = rec.exam_start_date.strftime('%d-%m-%Y') if rec.exam_start_date else 'No Date'
                    
                    # Generate proper URL for the record
                    exam_url = self._get_exam_planning_url(rec.id)

                    upcoming_html_rows.append(f"""
                        <tr class="exam-row">
                            <td>{rec.exam_name or 'No Name'}<br><small class='text-muted'>{rec.exam_code or 'No Code'}</small></td>
                            <td>{exam_date}<br><small class='text-muted'>{time_str}</small></td>
                            <td>{course_full_name}<br><small>{semester_full_name}</small></td>
                            <td>
                                <a href="{exam_url}" role="button" class="btn btn-primary btn-sm exam-detail-btn" data-exam-id="{rec.id}">
                                    <i class="fa fa-eye"></i> Course Info
                                </a>
                            </td>
                        </tr>
                    """)
                except Exception as e:
                    _logger.warning(f"Error processing upcoming exam {rec.id}: {e}")
                    continue

            if upcoming_html_rows:
                res['upcoming_exams_table'] = f"""
                <div class="table-responsive">
                    <table class="table table-striped table-hover mb-0">
                        <thead class="table-light">
                            <tr>
                                <th>Exam Details</th>
                                <th>Date &amp; Time</th>
                                <th>Course Info</th>
                                <th>Action</th>
                            </tr>
                        </thead>
                        <tbody>{"".join(upcoming_html_rows)}</tbody>
                    </table>
                </div>"""
            else:
                res['upcoming_exams_table'] = """<div class="text-center py-4"><p>No Upcoming Exams</p></div>"""

            # ========== EXAMS TODAY TABLE ==========
            exams_today_recs = self.env['exam.planning'].search([('exam_start_date', '=', today), ('active', '=', True)])
            
            exams_today_html_rows = []
            for rec in exams_today_recs:
                try:
                    hall_names = ", ".join(rec.hall_ids.mapped('name')) if hasattr(rec, 'hall_ids') and rec.hall_ids else "No Hall Assigned"
                    time_str = f"{int(rec.exam_time):02d}:{int((rec.exam_time - int(rec.exam_time)) * 60):02d}" if hasattr(rec, 'exam_time') and rec.exam_time else 'No Time'
                    course_full_name = course_mapping.get(rec.course, rec.course or 'No Course')
                    semester_full_name = semester_mapping.get(rec.class_semester, rec.class_semester or 'No Semester')
                    
                    exam_url = self._get_exam_planning_url(rec.id)

                    exams_today_html_rows.append(f"""
                        <tr class="exam-row">
                            <td>
                                <a href="{exam_url}" role="button" class="btn btn-sm btn-outline-primary exam-detail-btn" data-exam-id="{rec.id}">
                                    <i class="fa fa-eye"></i> {rec.exam_name or 'No Name'}
                                </a>
                                <br><small class='text-muted'>{rec.exam_code or 'No Code'}</small>
                            </td>
                            <td>{time_str}</td>
                            <td>{hall_names}</td>
                            <td><small>{course_full_name}<br>{semester_full_name}</small></td>
                        </tr>
                    """)
                except Exception as e:
                    _logger.warning(f"Error processing today's exam {rec.id}: {e}")
                    continue

            if exams_today_html_rows:
                res['exams_today_table'] = f"""
                <div class="table-responsive">
                    <table class="table table-striped mb-0">
                        <thead class="table-light">
                            <tr>
                                <th>Exam Details</th>
                                <th>Time</th>
                                <th>Hall</th>
                                <th>Course Info</th>
                            </tr>
                        </thead>
                        <tbody>{"".join(exams_today_html_rows)}</tbody>
                    </table>
                </div>"""
            else:
                res['exams_today_table'] = """<div class="text-center py-4"><p>No Exams Scheduled Today</p></div>"""

            # ========== UNASSIGNED STUDENTS (Confirmed & Cancelled Separate) ==========
            confirmed_html_rows = []
            cancelled_html_rows = []

            students = self.env['student.registration'].search([], limit=50)
            for student in students:
                try:
                    if hasattr(student, 'course') and hasattr(student, 'class_semester'):
                        exams = self.env['exam.planning'].search([
                            ('course', '=', student.course), 
                            ('class_semester', '=', student.class_semester)
                        ], limit=1)

                        course_full_name = course_mapping.get(student.course, student.course or 'No Course')
                        semester_full_name = semester_mapping.get(student.class_semester, student.class_semester or 'No Semester')

                        # Registration Badge
                        if student.state == 'confirm':
                            registration_status_html = "<td><span class='badge bg-success'>Confirmed</span></td>"
                        elif student.state == 'cancel':
                            registration_status_html = "<td><span class='badge bg-danger'>Cancelled</span></td>"
                        else:
                            registration_status_html = "<td><span class='badge bg-secondary'>Unknown</span></td>"

                        status_html = ""
                        action_html = ""

                        if not exams:
                            status_html = "<td><span class='badge rounded-pill bg-warning'>No Exam Available</span></td>"
                            student_url = self._get_student_registration_url(student.id)
                            action_html = f"""<td><a href="{student_url}" role="button" class="btn btn-primary btn-sm view-profile-btn"><i class="fa fa-user"></i> View Profile</a></td>"""
                        elif 'student.exam.assignment' in self.env:
                            assigned = self.env['student.exam.assignment'].search_count([
                                ('student_id', '=', student.id),
                                ('exam_id', 'in', exams.ids)
                            ])
                            if not assigned:
                                status_html = "<td><span class='badge bg-danger'>Not Assigned</span></td>"
                                student_url = self._get_student_registration_url(student.id)
                                action_html = f"""<td><a href="{student_url}" role="button" class="btn btn-primary btn-sm view-profile-btn"><i class="fa fa-user"></i> View Profile</a></td>"""

                        if action_html:
                            row_html = f"""
                                <tr class="student-row">
                                    <td>{student.student_name or 'No Name'}</td>
                                    <td>{course_full_name}</td>
                                    <td>{semester_full_name}</td>
                                    {registration_status_html}
                                    {status_html}
                                    {action_html}
                                </tr>
                            """
                            if student.state == 'confirm':
                                confirmed_html_rows.append(row_html)
                            elif student.state == 'cancel':
                                cancelled_html_rows.append(row_html)
                except Exception as e:
                    _logger.warning(f"Error processing student {student.id}: {e}")
                    continue

            tables_html = ""
            if confirmed_html_rows:
                tables_html += f"""
            <div class="card border-success mb-3">
                <div class="card-header bg-success text-white fw-bold">
                    Confirmed Registrations
                </div>
                <div class="table-responsive">
                    <table class="table table-striped mb-0">
                        <thead class="table-light">
                            <tr>
                                <th>Student Name</th>
                                <th>Course</th>
                                <th>Semester</th>
                                <th>Registration Status</th>
                                <th>Status</th>
                                <th>Action</th>
                            </tr>
                        </thead>
                        <tbody>{"".join(confirmed_html_rows)}</tbody>
                    </table>
                </div>
            </div>"""

            if cancelled_html_rows:
                tables_html += f"""
            <div class="card border-danger mb-3">
                <div class="card-header bg-danger text-white fw-bold">
                    Cancelled Registrations
                </div>
                <div class="table-responsive">
                    <table class="table table-striped mb-0">
                        <thead class="table-light">
                            <tr>
                                <th>Student Name</th>
                                <th>Course</th>
                                <th>Semester</th>
                                <th>Registration Status</th>
                                <th>Status</th>
                                <th>Action</th>
                            </tr>
                        </thead>
                        <tbody>{"".join(cancelled_html_rows)}</tbody>
                    </table>
                </div>
            </div>"""

            if not confirmed_html_rows and not cancelled_html_rows:
                tables_html = """<div class="text-center py-4"><p>All Students Assigned!</p></div>"""

            res['unassigned_students_table'] = tables_html

        except Exception as e:
            _logger.error(f"Error in dashboard generation: {e}")
            res.update({
                'upcoming_exams_table': '<div class="alert alert-danger">Error loading data</div>',
                'exams_today_table': '<div class="alert alert-danger">Error loading data</div>',
                'unassigned_students_table': '<div class="alert alert-danger">Error loading data</div>',
            })
        return res                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     

    @api.model
    def open_dashboard(self):
        dashboard = self.create({})
        return {'type': 'ir.actions.act_window','name': 'Exam Dashboard','res_model': 'exam.dashboard','view_mode': 'form','res_id': dashboard.id,'target': 'current','context': self.env.context,}
    def action_view_exam_planning(self):
        return {'type': 'ir.actions.act_window','name': 'Exam Planning','res_model': 'exam.planning','view_mode': 'list,form','target': 'current',}
    def action_view_student_registration(self):
        return {'type': 'ir.actions.act_window','name': 'Student Registration','res_model': 'student.registration','view_mode': 'list,form','target': 'current',}
    def action_view_exam_hall(self):
        return {'type': 'ir.actions.act_window','name': 'Exam Halls','res_model': 'exam.hall','view_mode': 'list,form','target': 'current',}
    def action_view_exam_seating(self):
        return {'type': 'ir.actions.act_window','name': 'Exam Seating','res_model': 'exam.seating','view_mode': 'list,form','target': 'current',}

    