from odoo import http
from odoo.http import request
from odoo.exceptions import ValidationError, AccessDenied
import logging

_logger = logging.getLogger(__name__)

class StudentPortalController(http.Controller):

    def _odoo18_authenticate(self, email, password):
        """
        Odoo 18 specific authentication method
        """
        try:
            # Get current database name properly
            db_name = request.env.cr.dbname
            
            # Method 1: Use Odoo 18 session authenticate
            uid = request.session.authenticate(email, password)
            if uid:
                _logger.info(f"Authentication successful for user: {email}")
                return True
                
        except Exception as e:
            _logger.warning(f"Session authenticate failed: {e}")
            
            # Method 2: Manual authentication for Odoo 18
            try:
                # Find user
                user = request.env['res.users'].sudo().search([
                    ('login', '=', email),
                    ('active', '=', True)
                ], limit=1)
                
                if not user:
                    _logger.warning(f"User not found: {email}")
                    return False
                
                # Verify credentials
                user.sudo().check_credentials(password)
                
                # Manually setup session if credentials are valid
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

    def _create_partner_from_student_data(self, student_data):
        """
        Create a partner (contact) record from student registration data
        """
        try:
            # Map course selections to readable format
            course_mapping = {
                'IT': 'Information Technology',
                'CS': 'Computer Science',
                'EC': 'Electronics',
                'ME': 'Mechanical',
                'CE': 'Civil',
                'EE': 'Electrical',
                'BT': 'Biotechnology',
                'CH': 'Chemical',
            }
            
            # Map semester selections to readable format
            semester_mapping = {
                'fy_sem1': 'First Year - Semester 1',
                'fy_sem2': 'First Year - Semester 2',
                'sy_sem3': 'Second Year - Semester 3',
                'sy_sem4': 'Second Year - Semester 4',
                'ty_sem5': 'Third Year - Semester 5',
                'ty_sem6': 'Third Year - Semester 6',
                'ly_sem7': 'Fourth Year - Semester 7',
                'ly_sem8': 'Fourth Year - Semester 8',
            }

            # Check if partner already exists
            existing_partner = request.env['res.partner'].sudo().search([
                ('email', '=', student_data['email'])
            ], limit=1)
            
            if existing_partner:
                _logger.info(f"Partner already exists for email: {student_data['email']}")
                return existing_partner

            # Create partner record
            partner_vals = {
                'name': student_data['name'],
                'email': student_data['email'],
                'phone': student_data['phone'],
                'is_company': False,  # Individual contact
                'customer_rank': 1,   # Mark as customer
                'category_id': [(4, self._get_or_create_student_category().id)],  # Add student category
                'comment': f"Course: {course_mapping.get(student_data['course'], student_data['course'])}\n"
                          f"Semester: {semester_mapping.get(student_data['semester'], student_data['semester'])}\n"
                          f"Registration Source: Website Portal"
            }
            
            partner = request.env['res.partner'].sudo().create(partner_vals)
            _logger.info(f"Partner created successfully for student: {student_data['name']}")
            return partner
            
        except Exception as e:
            _logger.error(f"Error creating partner: {e}")
            return False

    def _get_or_create_student_category(self):
        """
        Get or create 'Student' category for contacts
        """
        try:
            # Check if student category exists
            student_category = request.env['res.partner.category'].sudo().search([
                ('name', '=', 'Student')
            ], limit=1)
            
            if not student_category:
                # Create student category
                student_category = request.env['res.partner.category'].sudo().create({
                    'name': 'Student',
                    'color': 3,  # Blue color
                })
                _logger.info("Student category created")
            
            return student_category
            
        except Exception as e:
            _logger.error(f"Error creating student category: {e}")
            return False

    # Student Registration Page
    @http.route('/student/register', type='http', auth='public', website=True)
    def student_registration_form(self, **kw):
        exams = request.env['exam.planning'].sudo().search([])
        return request.render('exam_management.student_registration_template', {
            'exams': exams
        })

    @http.route('/student/register/submit', type='http', auth='public', website=True, methods=['POST'], csrf=True)
    def student_registration_submit(self, **post):
        name = post.get('name')
        email = post.get('email')
        phone = post.get('phone')
        password = post.get('password')
        course = post.get('course')
        semester = post.get('class_semester')

        exams = request.env['exam.planning'].sudo().search([])

        # Basic Validation
        if not all([name, email, phone, password, course, semester]):
            return request.render('exam_management.student_registration_template', {
                'error': 'All fields are required.',
                'exams': exams
            })

        # Check if user already exists
        existing_user = request.env['res.users'].sudo().search([('login', '=', email)], limit=1)
        if existing_user:
            return request.render('exam_management.student_registration_template', {
                'error': 'This email is already registered. Please login instead.',
                'exams': exams
            })

        try:
            # Prepare student data for both models
            student_data = {
                'name': name,
                'email': email,
                'phone': phone,
                'course': course,
                'semester': semester
            }

            # Create partner (contact) record first
            partner = self._create_partner_from_student_data(student_data)
            if not partner:
                _logger.warning("Partner creation failed, but continuing with student registration")

            # Create user with portal access
            portal_group = request.env.ref('base.group_portal')
            user = request.env['res.users'].sudo().create({
                'name': name,
                'login': email,
                'email': email,
                'password': password,  
                'groups_id': [(6, 0, [portal_group.id])],
                'partner_id': partner.id if partner else False,  # Link user to partner
            })

            # Create Student Profile
            student = request.env['student.registration'].sudo().create({
                'student_name': name,
                'email': email,
                'phone': phone,
                'course': course,
                'class_semester': semester,
                'status': 'assigned',
                'user_id': user.id,
            })

            # Link student to partner if partner was created successfully
            if partner and hasattr(partner, 'write'):
                try:
                    # Add reference to student registration in partner
                    partner.sudo().write({
                        'comment': (partner.comment or '') + f"\nStudent Registration ID: {student.student_id}"
                    })
                except Exception as e:
                    _logger.warning(f"Could not update partner with student ID: {e}")

            # Commit the transaction to ensure all records are created
            request.env.cr.commit()
            
            _logger.info(f"Student registration completed successfully for {name}")
            _logger.info(f"Created records - User: {user.id}, Student: {student.id}, Partner: {partner.id if partner else 'None'}")
            
            # Auto-login new student
            if self._odoo18_authenticate(email, password):
                return request.redirect('/student/profile')
            else:
                # Auto-login failed, redirect to login page
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

    # Student Profile Page
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

    # Student Login
    @http.route('/student/login', type='http', auth='public', website=True)
    def student_login_form(self, **kw):
        message = kw.get('message')
        context = {}
        
        if message == 'please_login':
            context['info'] = 'Registration successful! Please login with your credentials.'
            
        return request.render('exam_management.student_login_template', context)

    @http.route(['/student/login/submit'], type='http', auth='public', website=True, methods=['POST'])
    def student_login_submit(self, **post):
        email = post.get('email')
        password = post.get('password')

        if not email or not password:
            return request.render('exam_management.student_login_template', {
                'error': 'Email and password are required'
            })

        # Use Odoo 18 authentication
        if self._odoo18_authenticate(email, password):
            return request.redirect('/student/profile')

        return request.render('exam_management.student_login_template', {
            'error': 'Invalid Email ID or Password'
        })

    # Logout
    @http.route('/student/logout', type='http', auth='user', website=True)
    def student_logout(self):
        request.session.logout(keep_db=True)
        return request.redirect('/student/login')