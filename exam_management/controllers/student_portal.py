from odoo import http
from odoo.http import request

class StudentPortal(http.Controller):

    @http.route(['/my/student_list'], type='http', auth='user', website=True)
    def portal_student_list(self, **kwargs):
        Student = request.env['student.registration'].sudo()

        # Get filter values
        search = kwargs.get('search', '')
        course = kwargs.get('course', '')
        semester = kwargs.get('semester', '')
        status = kwargs.get('status', '')
        result = kwargs.get('result', '')

        domain = []

        # Search filter
        if search:
            domain += ['|', '|',
                ('student_name', 'ilike', search),
                ('email', 'ilike', search),
                ('student_id', 'ilike', search),
            ]

        # Course filter
        if course:
            domain.append(('course', '=', course))

        # Semester filter
        if semester:
            domain.append(('class_semester', '=', semester))

        # Status filter
        if status:
            domain.append(('state', '=', status))


        students = Student.search(domain)

        return request.render("exam_management.student_portal_list", {
            'students': students,
            'search': search,
            'course': course,
            'semester': semester,
            'status': status,
            'result': result,
        })
