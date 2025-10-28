from odoo import models, fields, api

class TrainingTeacher(models.Model):
    _name = "training.teacher"
    _description = "Training Teacher"
    _rec_name = "name"
    
    name = fields.Char(string='Name', required=True)
    email = fields.Char(String='Email', required =True)
    expertise = fields.Char(String='Expertise')

    student_ids = fields.Many2many('training.student','teacher_id', string='Students')

    # Computed field for number of applications
    student_count = fields.Integer(
        string="Students",
        compute="_compute_application_count",
        store=True
    )

    @api.depends('student_ids')
    def _compute_application_count(self):
        """Compute number of applications for each student"""
        for record in self:
            record.student_count = len(record.student_ids)

    def action_view_applications(self):
        """Open applications related to this student"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Students',
            'res_model': 'training.student',
            'view_mode': 'list,form',
            'domain': [('teacher_id', '=', self.id)],
            'context': {'default_teacher_id': self.id},
        }
     