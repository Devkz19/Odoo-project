from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime
import io
import base64
import xlsxwriter


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
            
    def action_export_excel(self):
        """Export multiple selected exam details into one Excel file."""
        if not self:
            raise ValidationError("Please select at least one exam record to export.")

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Exam Details')

        # ==============================
        #   FORMATS
        # ==============================
        title_format = workbook.add_format({
            'bold': True, 'font_size': 14,
            'font_color': 'white',
            'bg_color': '#4F81BD',
            'align': 'center', 'valign': 'vcenter'
        })
        address_header_format = workbook.add_format({
            'bold': True,
            'font_color': 'white',
            'bg_color': '#808080',
            'align': 'left',
            'valign': 'vcenter'
        })
        text_format = workbook.add_format({
            'border': 1,
            'align': 'left',
            'valign': 'vcenter',
            'text_wrap': True
        })
        header_format = workbook.add_format({
            'bold': True,
            'font_color': 'white',
            'bg_color': '#4F81BD',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter'
        })
        section_header_format = workbook.add_format({
            'bold': True,
            'font_color': 'white',
            'bg_color': '#808080',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter'
        })
        date_format = workbook.add_format({
            'border': 1,
            'num_format': 'dd/mm/yyyy',
            'align': 'center',
            'valign': 'vcenter'
        })
        company_name_below_logo_format = workbook.add_format({
            'bold': True,
            'font_size': 12,
            'align': 'center',
            'valign': 'vcenter'
        })

        # ==============================
        #   COMPANY INFO (ONCE AT TOP)
        # ==============================
        company = self.env.user.company_id
        row = 0

        # --- 1️⃣ COMPANY NAME AT THE VERY TOP ---
        sheet.merge_range(row, 0, row, 9, f"{company.name or ''} ({company.city or ''})", title_format)
        row += 2
        
        # --- 2️⃣ ADDRESS HEADER (MERGED ACROSS A3:J4) ---
        sheet.merge_range(row, 0, row + 1, 9, "Address", address_header_format)
        row += 2

        # --- 3 LOGO SECTION (MERGED CELL A3:A6) ---
        logo_start_row = row
        sheet.merge_range(logo_start_row, 0, logo_start_row + 5, 0, '', text_format)

        # Set row heights
        for r in range(logo_start_row, logo_start_row + 6):
            sheet.set_row(r, 25)

        # Insert company logo
        if company.logo:
            logo_data = io.BytesIO(base64.b64decode(company.logo))
        else:
            with open('/mnt/data/5e22f43d-160d-4adc-8060-e0fcc30ea190.png', 'rb') as f:
                logo_data = io.BytesIO(f.read())

        sheet.insert_image(logo_start_row, 0, 'logo.png', {
            'image_data': logo_data,
            'x_scale': 0.45,
            'y_scale': 0.5,
            'x_offset': 8,
            'y_offset': 8,
            'positioning': 1
        })
        
        # --- ADDRESS SECTION (RIGHT SIDE - STARTING FROM B3) ---
        address_fields = [
            ('Company', company.name or 'N/A'),
            ('Street', company.street or 'N/A'),
            ('City', company.city or 'N/A'),
            ('State', company.state_id.name if company.state_id else 'N/A'),
            ('ZIP', company.zip or 'N/A'),
            ('Country', company.country_id.name if company.country_id else 'N/A')
        ]
        current_row = logo_start_row
        for label, value in address_fields:
            sheet.write(current_row, 1, f"{label}:", header_format)
            sheet.merge_range(current_row, 2, current_row, 9, value, text_format)
            current_row += 1

        row = current_row + 2

        # ==============================
        #   LOOP THROUGH SELECTED EXAMS
        # ==============================
        for exam in self:
            # --- Exam Title ---
            sheet.merge_range(row, 0, row, 9, f"Exam Details - {exam.exam_name or ''}", title_format)
            row += 2

            # --- General Info ---
            main_headers = [
                'Exam Name', 'Exam Code', 'Class & Semester', 'Course',
                'Exam Start Date', 'Exam End Date', 'Exam Time',
                'Duration (Hours)', 'Total Marks', 'Registration Deadline'
            ]
            main_values = [
                exam.exam_name or '',
                exam.exam_code or '',
                exam.class_semester or '',
                exam.course or '',
                exam.exam_start_date or '',
                exam.exam_end_date or '',
                exam.exam_time or '',
                exam.duration or '',
                exam.total_marks or '',
                exam.registration_deadline or ''
            ]

            sheet.merge_range(row, 0, row, len(main_headers) - 1, "General Information", section_header_format)
            row += 1

            for col, header in enumerate(main_headers):
                sheet.write(row, col, header, header_format)
            row += 1

            # Create center-aligned text format for general info
            text_format_center = workbook.add_format({
                'border': 1,
                'align': 'center',
                'valign': 'vcenter',
                'text_wrap': True
            })
            
            date_format_center = workbook.add_format({
                'border': 1,
                'num_format': 'dd/mm/yyyy',
                'align': 'center',
                'valign': 'vcenter'
            })

            for col, value in enumerate(main_values):
                if isinstance(value, datetime) or 'Date' in main_headers[col]:
                    try:
                        date_obj = value if isinstance(value, datetime) else datetime.strptime(str(value), "%Y-%m-%d")
                        sheet.write_datetime(row, col, date_obj, date_format_center)
                    except Exception:
                        sheet.write(row, col, str(value), text_format_center)
                else:
                    sheet.write(row, col, str(value), text_format_center)
            row += 3

            # --- Subject List ---
            sheet.merge_range(row, 0, row, 2, "Subjects", section_header_format)
            row += 1
            subject_headers = ['Subject Name', 'Exam Date', 'Total Marks']
            for col, header in enumerate(subject_headers):
                sheet.write(row, col, header, header_format)
            row += 1

            if exam.subject_ids:
                total_marks_sum = 0
                for subject in exam.subject_ids:
                    sheet.write(row, 0, subject.name or '', text_format_center)
                    
                    # Exam Date in column 1
                    if subject.exam_date:
                        try:
                            date_obj = subject.exam_date if isinstance(subject.exam_date, datetime) else datetime.strptime(str(subject.exam_date), "%Y-%m-%d")
                            sheet.write_datetime(row, 1, date_obj, date_format_center)
                        except Exception:
                            sheet.write(row, 1, str(subject.exam_date), text_format_center)
                    else:
                        sheet.write(row, 1, '', text_format_center)
                    
                    # Total Marks in column 2
                    marks = subject.total_marks or 0
                    sheet.write(row, 2, marks, text_format_center)
                    total_marks_sum += marks
                    row += 1
                
                # Add Total row
                sheet.write(row, 0, 'Total', header_format)
                sheet.write(row, 1, '', header_format)
                sheet.write(row, 2, total_marks_sum, header_format)
                row += 1
            else:
                sheet.merge_range(row, 0, row, 2, "No subjects found", text_format_center)
                row += 1

            row += 3  # spacing before next exam
        
        # Auto-fit columns
        sheet.set_column(0, 0, 15)
        sheet.set_column(1, 1, 15)
        for col in range(2, 11):
            sheet.set_column(col, col, 20)

        # ==============================
        #   FINALIZE FILE
        # ==============================
        workbook.close()
        output.seek(0)
        excel_data = output.read()
        output.close()

        # Create attachment
        attachment = self.env['ir.attachment'].create({
            'name': 'Exam_Planning_Details.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(excel_data),
            'res_model': 'exam.planning',
            'res_id': self[0].id,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'new',
        }
        

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
