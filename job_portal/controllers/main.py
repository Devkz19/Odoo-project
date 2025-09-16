from odoo import http
from odoo.http import request
import base64


class JobPortalController(http.Controller):

    @http.route(['/jobs'], type='http', auth="public", website=True)
    def job_list(self, **kw):
        """ Show list of job positions """
        jobs = request.env['job.position'].sudo().search([('active', '=', True)])
        return request.render("job_portal.job_list_template", {"jobs": jobs})

    @http.route(['/jobs/apply/<int:job_id>'], type='http', auth="public", website=True)
    def job_apply_form(self, job_id, **kw):
        """ Job application form for a specific job """
        job = request.env['job.position'].sudo().browse(job_id)
        return request.render("job_portal.job_application_form_template", {"job": job})

    @http.route(['/jobs/submit'], type='http', auth="public", methods=["POST"], website=True, csrf=False)
    def job_submit(self, **post):
        """ Handle form submission and create job application """

        file = post.get("cv_attachment")
        cv_attachment = False
        cv_filename = False

        if file and hasattr(file, 'filename') and hasattr(file, 'read'):
            cv_attachment = base64.b64encode(file.read())
            cv_filename = file.filename
        vals = {
            "applicant_name": post.get("applicant_name"),
            "email": post.get("email"),
            "phone": post.get("phone"),
            "cv_attachment": cv_attachment,
            "cv_filename": cv_filename,
            "job_id": int(post.get("job_id")),
        }

        #  Create application once
        application = request.env['job.application'].sudo().create(vals)

        #  Send Thank You email
        template = request.env.ref('job_portal.mail_template_job_application_thankyou', raise_if_not_found=False)
        if template:
            template.sudo().send_mail(application.id, force_send=True)

        return request.render("job_portal.job_application_thankyou_template", {"application": application})
