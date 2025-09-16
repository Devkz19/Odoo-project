from odoo import models, fields, api, _

class Reststaffwizard(models.TransientModel):
    _name = 'rest.staff.wizard'
    _description = 'This is a wizard model which will update information of our staff'
    
    name = fields.Char(string="Name", size=50)
    age = fields.Integer(string="Age")
    dob = fields.Date(string="DOB")
    mobile = fields.Char(string="Mobile", help="Enter 10 digit mobile number", required=True)
    email = fields.Char(string="Email")
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female')
    ], string="Gender")
    country_id = fields.Many2one('res.country', string="Country")
    country_ids = fields.Many2many('res.country', string="Countries")
    country_code = fields.Char(string="Country Code", related='country_id.code', store=True)
    staff_line_ids = fields.One2many('rest.staff.wizard.lines', 'connecting_field', string="Staff Lines")
    image = fields.Image(string="Image", max_width=150, max_height=150)
    hand_salary = fields.Float(string="In hand Salary")
    epf_esi = fields.Float(string="EPF+ESI")
    ctc_salary = fields.Float(string="CTC Salary")
    
    def update_info_fun(self):
        pass
        active_id = self._context.get('active_id')
        upd_var = self.env['rest.staff'].browse(active_id)
    
    # upd_var.staff_line.ids = [(5, 0, 0)]  # Clear existing lines
        vals = {
            'name': self.name,
            'age': self.age,
            'dob': self.dob,
            'mobile': self.mobile,
            'email': self.email,
        }
        
        upd_var.write(vals)
    
    @api.model
    def default_get(self, fields):
            res = super(Reststaffwizard, self).default_get(fields)
            
            active_id = self._context.get('active_id')  # Get active_id from context

            if active_id:
                brw_id = self.env['rest.staff'].browse(int(active_id))

                list = []
                list2 = []

                for rec in brw_id.country_ids:
                    list.append(rec.id)

                for rec in brw_id.staff_line_ids:
                    list2.append((0, 0, {
                        'name': rec.name,
                        'product_id': rec.product_id.id
                    }))

                # Populate default values
                res.update({
                    'name': brw_id.name,
                    'age': brw_id.age,
                    'email': brw_id.email,
                    'mobile': brw_id.mobile,
                    'dob': brw_id.dob,
                    'gender': brw_id.gender,
                    'country_ids': [(6, 0, list)],
                    'staff_line_ids': list2,
                })

            return res
 
    
    def create_new_staff(self):
        list = []
        list2 = []
        for rec in self.country_ids:
            list.append(rec.id)
            
        for rec in self.staff_line_ids:
            list2.append((0,0,{'name':rec.name, 'product_id':rec.product_id.id}))        
        staff_id = self.env['rest.staff'].create({
            'name':self.name,
            'age':self.age,
            'email':self.email,
            'mobile':self.mobile,
            'dob':self.dob,
            'gender':self.gender,
            'country_ids': [(6,0,list)],
            'staff_line_ids': list2
        })
        
        for rec in self.staff_line_ids:
            self.env['rest.staff.lines'].create({
                'connecting_field':staff_id.id,
                'name':rec.name,
                'product_id':rec.product_id.id
             })
        context = dict(self.env.context)
        context['form_view_initial_mode'] = 'edit'
        return {
            'name':_('New Created Staff'),
            'context':context,
            'view_mode':'form',
            'res_model':'rest.staff',
            'res_id':staff_id.id,
            'view_type':'form',
            'type':'ir.actions.act_window',
        }

class RestStaffwizardLine(models.TransientModel):
    _name = 'rest.staff.wizard.lines'
    _description = 'Staff wizard line details'

    connecting_field = fields.Many2one('rest.staff.wizard', string="Staff ID")
    name = fields.Char(string="Name", required=True)
    product_id = fields.Many2one('product.product', string="Product")
    sequence = fields.Integer(string="Seq.")
