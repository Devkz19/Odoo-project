from odoo import models, fields, api
import io
import base64
import xlsxwriter

class JobApplication(models.Model):
    _name = 'job.application'
    _description = 'Job Application'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'applicant_name'

    applicant_name = fields.Char(string="Applicant Name", required=True, tracking=True)
    email = fields.Char(string="Email", required=True, tracking=True)
    phone = fields.Char(string="Phone", tracking=True)
    cv_attachment = fields.Binary(string="CV / Resume", required=True,)
    cv_filename = fields.Char(string="CV Filename")
    job_id = fields.Many2one('job.position', string="Applied Job", required=True, tracking=True)
    active = fields.Boolean(default=True)
    status = fields.Selection([
    ('draft', 'Draft'),
    ('submitted', 'Submitted'),
    ('shortlisted', 'Shortlisted'),
    ('rejected', 'Rejected'),
    ('hired', 'Hired'),
    ('canceled', 'Canceled'),
], string="Status", default='draft', tracking=True)

    def action_cancel(self):
        self.write({'status': 'canceled'})
    
    def action_submit(self):
        self.write({'status': 'submitted'})

    def action_shortlist(self):
        self.write({'status': 'shortlisted'})

    def action_reject(self):
        self.write({'status': 'rejected'})

    def action_hire(self):
        self.write({'status': 'hired'})

    def action_reset_draft(self):
        self.write({'status': 'draft'})
    
        #email functions 
    def action_send_thankyou_email(self):
        """Send thank you email to candidate"""
        template = self.env.ref('job_portal.mail_template_job_application_thankyou')
        for record in self:
            if record.email:
                template.sudo().send_mail(record.id, force_send=True)    
    
    def _send_status_email(self, template_xmlid):
        """Helper to send emails based on template"""
        template = self.env.ref(template_xmlid, raise_if_not_found=False)
        if template:
            for record in self:
                if record.email:
                    template.sudo().send_mail(record.id, force_send=True)

    @api.model
    def create(self, vals):
        record = super().create(vals)
        if vals.get("status") == "submitted":
            record._send_status_email("job_portal.mail_template_job_application_thankyou")
        return record

    def write(self, vals):
        res = super().write(vals)

        for record in self:
            if "status" in vals:
                if record.status == "submitted":
                    record._send_status_email("job_portal.mail_template_job_application_thankyou")
                elif record.status == "shortlisted":
                    record._send_status_email("job_portal.mail_template_job_application_shortlisted")
                elif record.status == "hired":
                    record._send_status_email("job_portal.mail_template_job_application_hired")
                elif record.status == "rejected":
                    record._send_status_email("job_portal.mail_template_job_application_rejected")

        return res   
    
    def action_export_excel(self):
        """Export the current job application record to Excel (row-wise table)"""
        self.ensure_one()
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Job Application')

        # Define formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#D3D3D3',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter'
        })
        text_format = workbook.add_format({'border': 1})

        # Data mapping (field order matters here)
        headers = [
            'Applicant Name', 'Email', 'Phone',
            'Applied Job', 'CV Filename', 'Status', 'Active'
        ]
        values = [
            self.applicant_name or '',
            self.email or '',
            self.phone or '',
            self.job_id.name or '',
            self.cv_filename or '',
            self.status or '',
            'Yes' if self.active else 'No'
        ]

        # Write headers in row 0
        for col, header in enumerate(headers):
            sheet.write(0, col, header, header_format)

        # Write values in row 1
        for col, value in enumerate(values):
            sheet.write(1, col, value, text_format)

        # Auto adjust column widths based on header length
        for col, header in enumerate(headers):
            column_width = max(len(str(header)), len(str(values[col]))) + 5
            sheet.set_column(col, col, column_width)

        workbook.close()
        output.seek(0)
        excel_data = output.read()
        output.close()

        # Create attachment
        attachment = self.env['ir.attachment'].create({
            'name': f'{self.applicant_name}_application.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(excel_data),
            'res_model': 'job.application',
            'res_id': self.id,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })

        # Return as downloadable file
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'new',
        }
       
   