from odoo import models, fields, api

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
], string="Status", default='draft', tracking=True, clickable=True)

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
   