from odoo import http
from odoo.http import request
from odoo.exceptions import AccessError


class StudentPortal(http.Controller):

    @http.route(['/my/student_dashboard'], type='http', auth='user', website=True)
    def student_dashboard(self, **kw):
        # Fetch student profile
        student = request.env['student.registration'].sudo().search([
            ('user_id', '=', request.env.user.id)
        ], limit=1)

        if not student:
            return request.redirect('/my')

        # Fetch assigned exams
        assigned_exams = request.env['student.exam.assignment'].sudo().search([
            ('student_id', '=', student.id)
        ])

        results = []
        if assigned_exams:
            assigned_exam_ids = assigned_exams.mapped('exam_id.id')
            results = request.env['exam.result'].sudo().search([
                ('student_id', '=', student.id),
                ('exam_id', 'in', assigned_exam_ids)
            ])

        return request.render('exam_management.student_portal_profile', {
            'student': student,
            'assigned_exams': assigned_exams,
            'results': results,
        })

    # Result Download
    @http.route(['/my/result/<int:result_id>/download'], type='http', auth='user', website=True)
    def download_result(self, result_id, **kw):
        """Allow student to download their own result PDF."""
        result = request.env['exam.result'].sudo().browse(result_id)
        if not result.exists():
            return request.not_found()

        user = request.env.user
        is_admin = user.has_group('base.group_system') or user.has_group('exam_management.group_college_admin')

        if not is_admin:
            student = request.env['student.registration'].sudo().search([
                ('user_id', '=', user.id)
            ], limit=1)
            if not student or result.student_id.id != student.id:
                raise AccessError("You are not allowed to download this result.")

        pdf_content, _ = request.env['ir.actions.report'].sudo()._render_qweb_pdf(
            'exam_management.action_report_exam_result',
            [result.id]
        )

        pdf_http_headers = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf_content)),
            ('Content-Disposition', 'attachment; filename="Result-%s.pdf"' % result.display_name.replace('/', '-')),
        ]

        return request.make_response(pdf_content, headers=pdf_http_headers)

    # Admit Card Download
    @http.route(['/my/admit_card/<int:exam_id>/download'], type='http', auth='user', website=True)
    def download_admit_card(self, exam_id, **kw):
        """Allow student to download their own admit card PDF."""
        user = request.env.user

        # Student record
        student = request.env['student.registration'].sudo().search([
            ('user_id', '=', user.id)
        ], limit=1)

        if not student:
            return request.not_found()

        # Find the student's seating for this exam
        seating = request.env['exam.seating'].sudo().search([
            ('exam_id', '=', exam_id),
            ('student_id', '=', student.id)
        ], limit=1)

        if not seating:
            return request.not_found()

        # Access check: admins can download anyone’s admit card
        is_admin = user.has_group('base.group_system') or user.has_group('exam_management.group_college_admin')

        if not is_admin and seating.student_id.id != student.id:
            raise AccessError("You are not allowed to download this admit card.")

        # Correct way to generate PDF
        pdf_content, _ = request.env['ir.actions.report'].sudo()._render_qweb_pdf(
            'exam_management.action_report_exam_admit_card',
            [seating.id]
        )

        pdf_http_headers = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf_content)),
            ('Content-Disposition', 'attachment; filename="Admit_Card-%s.pdf"' % student.student_name.replace('/', '-'))
        ]
        return request.make_response(pdf_content, headers=pdf_http_headers)

    