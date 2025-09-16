from odoo import http
from odoo.http import request
from odoo.exceptions import ValidationError, AccessDenied
import base64
import logging

_logger = logging.getLogger(__name__)


class StudentPortalController(http.Controller):

    # -------------------------
    # Utility: Authentication
    # -------------------------
    def _odoo18_authenticate(self, email, password):
        try:
            uid = request.session.authenticate(email, password)
            if uid:
                _logger.info(f"Authentication successful for user: {email}")
                return True
        except Exception as e:
            _logger.warning(f"Session authenticate failed: {e}")

            try:
                user = request.env['res.users'].sudo().search([
                    ('login', '=', email),
                    ('active', '=', True)
                ], limit=1)
                if not user:
                    _logger.warning(f"User not found: {email}")
                    return False

                user.sudo().check_credentials(password)

                request.session.uid = user.id
                request.session.login = email
                request.session.session_token = user._compute_session_token(request.session.sid)
                request.session.context = user.context_get()

                _logger.info(f"Manual authentication successful for: {email}")
                return True

            except AccessDenied:
                _logger.warning(f"Invalid credentials for: {email}")
                return False
            except Exception as e:
                _logger.error(f"Manual authentication error: {e}")
                return False

        return False

    # -------------------------
    # Student Registration Form
    # -------------------------
    @http.route('/student/register', type='http', auth='public', website=True)
    def student_registration_form(self, **kw):
        exams = request.env['exam.planning'].sudo().search([])
        return request.render('exam_management.student_registration_template', {
            'exams': exams
        })

    @http.route('/student/register/submit', type='http', auth='public',
                website=True, methods=['POST'], csrf=True)
    def student_registration_submit(self, **post):
        name = post.get('name')
        email = post.get('email')
        phone = post.get('phone')
        password = post.get('password')
        course = post.get('course')
        semester = post.get('class_semester')

        # Handle uploaded image
        image_file = post.get('image_1920')
        image_data = False
        if image_file and hasattr(image_file, 'read'):
            try:
                raw_bytes = image_file.read()
                print(">>> [DEBUG] Image file received, size (bytes):", len(raw_bytes))
                if len(raw_bytes) > 0:
                    image_data = base64.b64encode(raw_bytes)
                    print(">>> [DEBUG] Image successfully encoded to base64, size:", len(image_data))
                else:
                    print(">>> [DEBUG] Empty image file received")
            except Exception as e:
                print(">>> [DEBUG] Error reading uploaded image:", e)
                _logger.error(f"Error reading uploaded image: {e}")
        else:
            print(">>> [DEBUG] No image file received in form submission")

        exams = request.env['exam.planning'].sudo().search([])

        # Validation
        if not all([name, email, phone, password, course, semester]):
            return request.render('exam_management.student_registration_template', {
                'error': 'All fields are required.',
                'exams': exams
            })

        existing_user = request.env['res.users'].sudo().search([('login', '=', email)], limit=1)
        if existing_user:
            return request.render('exam_management.student_registration_template', {
                'error': 'This email is already registered. Please login instead.',
                'exams': exams
            })

        try:
            # Create Partner
            partner_vals = {
                'name': name,
                'email': email,
                'phone': phone,
                'is_company': False,
                'customer_rank': 1,
            }
            if image_data:
                partner_vals['image_1920'] = image_data
            partner = request.env['res.partner'].sudo().create(partner_vals)

            # Create User
            portal_group = request.env.ref('base.group_portal')
            user_vals = {
                'name': name,
                'login': email,
                'email': email,
                'password': password,
                'groups_id': [(6, 0, [portal_group.id])],
                'partner_id': partner.id,
            }
            if image_data:
                user_vals['image_1920'] = image_data
            user = request.env['res.users'].sudo().create(user_vals)
            print(">>> [DEBUG] User created with ID:", user.id)

            # Create Student Registration
            student_vals = {
                'student_name': name,
                'email': email,
                'phone': phone,
                'course': course,
                'class_semester': semester,
                'status': 'assigned',
                'user_id': user.id,
            }
            if image_data:
                student_vals['image_1920'] = image_data
            student = request.env['student.registration'].sudo().create(student_vals)
            print(">>> [DEBUG] Student record created with ID:", student.id)

            request.env.cr.commit()
            _logger.info(f"Student registered: {name}, User ID: {user.id}, Student ID: {student.id}")

            # Auto-login
            if self._odoo18_authenticate(email, password):
                return request.redirect('/student/profile')
            else:
                return request.redirect('/web/login')

        except ValidationError as ve:
            _logger.error(f"Validation error during registration: {ve}")
            return request.render('exam_management.student_registration_template', {
                'error': str(ve),
                'exams': exams
            })
        except Exception as e:
            _logger.error(f"Registration error: {e}")
            return request.render('exam_management.student_registration_template', {
                'error': 'Registration failed. Please try again.',
                'exams': exams
            })

    # -------------------------
    # Student Profile Page
    # -------------------------
    @http.route(['/student/profile'], type='http', auth='user', website=True)
    def student_profile(self, **kwargs):
        student = request.env['student.registration'].sudo().search([
            ('user_id', '=', request.env.user.id)
        ], limit=1)

        if not student:
            return request.render('exam_management.portal_no_student')

        return request.render('exam_management.student_profile_template', {
            'student': student
        })

    # -------------------------
    # Login & Logout
    # -------------------------
    @http.route('/student/login', type='http', auth='public', website=True)
    def student_login_form(self, **kw):
        message = kw.get('message')
        context = {}
        if message == 'please_login':
            context['info'] = 'Registration successful! Please login with your credentials.'
        return request.render('exam_management.student_login_template', context)

    @http.route(['/student/login/submit'], type='http', auth='public',
                website=True, methods=['POST'])
    def student_login_submit(self, **post):
        email = post.get('email')
        password = post.get('password')

        if not email or not password:
            return request.render('exam_management.student_login_template', {
                'error': 'Email and password are required'
            })

        if self._odoo18_authenticate(email, password):
            return request.redirect('/student/profile')

        return request.render('exam_management.student_login_template', {
            'error': 'Invalid Email ID or Password'
        })

    @http.route('/student/logout', type='http', auth='user', website=True)
    def student_logout(self):
        request.session.logout(keep_db=True)
        return request.redirect('/student/login')
