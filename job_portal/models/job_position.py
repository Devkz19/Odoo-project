from odoo import models, fields, api

class JobDepartment(models.Model):
    _name = 'job.department'
    _description = 'Job Department'
    _rec_name = 'name'

    name = fields.Char(string="Department Name", required=True)


class JobPosition(models.Model):
    _name = 'job.position'
    _description = 'Job Position'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(string='Title', required=True, tracking=True)
    description = fields.Html(string='Job Description', tracking=True)
    department_id = fields.Many2one('job.department', string='Department', tracking=True)
    total_openings = fields.Integer(string='Total Openings', default=1, tracking=True)
    active = fields.Boolean(string='Active', default=True)
    application_ids = fields.One2many(
        'job.application', 'job_id', string="Applications"
    )

    # Computed field for number of applications
    application_count = fields.Integer(
        string="Applications",
        compute="_compute_application_count",
        store=True
    )

    @api.depends('application_ids')
    def _compute_application_count(self):
        """Compute number of applications for each job"""
        for record in self:
            record.application_count = len(record.application_ids)

    def action_view_applications(self):
        """Open applications related to this job position"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Applications',
            'res_model': 'job.application',
            'view_mode': 'list,form',
            'domain': [('job_id', '=', self.id)],
            'context': {'default_job_id': self.id},
        }