from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime,date
import pytz
import xlwt
import base64
from io import BytesIO

class CustomExcel(models.TransientModel):
    _name = 'custom.excel.class'
    _rec_name = 'datas_frame'
    
    file_name = fields.Binary(string="Report")
    datas_frame = fields.Char(string="Filename")

class Reststaff(models.Model):
    _name = 'rest.staff'
    _description = 'This model will store data of our staff'
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'age asc'
    
    name = fields.Char()
    email = fields.Char()
    age = fields.Integer()
    lang = fields.Selection(
        selection=[
            ('en_US', 'English'),
            ('fr_FR', 'French'),
            ('hi_IN', 'Hindi'),
        ],
        string="Language",
        default='en_US'
    )
    
    def print_excel(self):
        filename = self.name + '.xls'  # Added file extension
        workbook = xlwt.Workbook(encoding='utf-8')
        sheet1 = workbook.add_sheet('staff', cell_overwrite_ok=True)
        date_formate = xlwt.XFStyle() 
        date_formate.num_format_str = 'DD/MM/YY'
        format1 = xlwt.easyxf(
            'align:horiz center;'
            'font:color black,bold True;'
            'borders:top_color black, bottom_color black, right_color black, left_color black,'
            'left thin, right thin, top thin, bottom thin;'
            'pattern:pattern solid, fore_color aqua'
        )
        format2 = xlwt.easyxf(
            'align:horiz center;'
            'font:color black;'
            'borders:top_color black, bottom_color black, right_color black, left_color black,'
            'left thin, right thin, top thin, bottom thin;'
            'pattern:pattern solid, fore_color white'
        )
        
        countries = []
        for rec in self.country_ids:
            countries.append(rec.name)
        countries = ", ".join(countries)    
            
        
        sheet1.col(0).width = 7000
        sheet1.col(1).width = 7000
        sheet1.col(2).width = 7000
        sheet1.col(3).width = 4000
        sheet1.col(4).width = 5000
        sheet1.col(5).width = 7000
        sheet1.col(6).width = 7000
        sheet1.col(7).width = 10000
        sheet1.col(8).width = 10000
        sheet1.col(9).width = 12000
        
        sheet1.write(0,0,"Name",format1)
        sheet1.write(0,1,"Email",format1)
        sheet1.write(0,2,"Mobile",format1)
        sheet1.write(0,3,"Age",format1)
        sheet1.write(0,4,"DOB",format1)
        sheet1.write(0,5,"Country",format1)
        sheet1.write(0,6,"Gender",format1)
        sheet1.write(0,7,"Ref. Countries",format1)
        sheet1.write(0,8,"Name(o2m)",format1)
        sheet1.write(0,9,"Product(o2m)",format1)
        
        sheet1.write(1,0,self.name,format2)
        sheet1.write(1,1,self.email,format2)
        sheet1.write(1,2,self.mobile,format2)
        sheet1.write(1,3,self.age,format2)
        sheet1.write(1,4,self.dob,date_formate)
        sheet1.write(1,5,self.country_id.name,format2)
        sheet1.write(1,6,self.gender,format2)
        sheet1.write(1,7,countries,format2)
        i = 1
        for rec in self.staff_line_ids:
            sheet1.write(i,8,rec.name,format2)
            sheet1.write(i,9,rec.product_id.name,format2)
            i+=1
        sheet1.write_merge(i,i+1,0,9,'Report is Printed',format1)
        
        stream=BytesIO()
        workbook.save(stream)
        out = base64.encodebytes(stream.getvalue())
        
        excel_id = self.env['custom.excel.class'].create({
        "datas_frame": filename, 
        "file_name": out.decode('utf-8') 
    })
        
        return {
        'type': 'ir.actions.act_window',
        'res_model': 'custom.excel.class',
        'res_id': excel_id.id,
        'view_mode': 'form',
        'target': 'new', 
          }
    
    def new_fun(self):
        print("Executing new function in staff model by object button...")   
        
    def call_by_menu(self):
        print("called by menu item")  
        
    def report_print_button(self):      
        return self.env.ref('tutorial_project.action_report_rest_staff').report_action(self)

    def delete_one2many(self):
        for record in self:
            if record.staff_line_ids:
                record.staff_line_ids = [(5, 0, 0)]
                return {
                    'effect': {
                        'fadeout': 'slow',
                        'type': 'rainbow_man',
                        'message': 'All lines deleted successfully!'
                    }
                }
    
    def get_values_in_report(self):
        ist = pytz.timezone('Asia/Kolkata')
        current_date = date.today()
        current_datetime = datetime.now(ist)  # Convert to IST
        return {
           'current_date': current_date,
           'current_datetime': current_datetime
        }
    
    def unlink(self):
        for rec in self:
            if rec.status == 'active':
                raise UserError(_("Cannot delete a record with active status."))
        return super(Reststaff, self).unlink()
    
    @api.model
    def create(self, vals):
        if vals.get("seq_num") in [None, 'New']:
            vals["seq_num"] = self.env['ir.sequence'].next_by_code('rest.seq.staff') or 'New'
        if not vals.get('staff_line_ids'):
            raise ValidationError(_("please provide at least one staff line (one2many line)"))    
        res = super(Reststaff, self).create(vals)
        return res
    
    def send_email(self):
        temp_id = self.env.ref('tutorial_project.mail_template_staff_for_email').id
        print("temp_id----",temp_id)
        template = self.env['mail.template'].browse(temp_id)
        template.with_context(lang=None).send_mail(self.id, force_send=True)

        

    def write(self, vals):
        res = super(Reststaff, self).write(vals)
        print("res:", res, "| self:", self, "| vals:", vals)
        print("name---",self.name,"age---",self.age,'email----',self.email)
        return res

    def check_orm(self):        
        record = self.env['rest.staff'].browse(30)
        print("Record 30 exists:", bool(record.exists()))

    def do_resign(self):
        for rec in self:
            rec.status = 'resigned'
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }        
    
    def do_rejoin(self):
        for rec in self:
            rec.status = 'active'
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }
        
    @api.depends('dob')
    def _compute_age(self):
        for record in self:
            if record.dob:
                today = date.today()
                record.age = today.year - record.dob.year - (
                    (today.month, today.day) < (record.dob.month, record.dob.day)
                )
            else:
                record.age = 0
                  
    @api.constrains('age')
    def val_age(self):
        for record in self:
            if record.age < 18:
                raise ValidationError(_("Age must be greater than or equal to 18"))
             
    name = fields.Char(string="Name", size=50, track_visibility='always')
    age = fields.Integer(string="Age", compute="_compute_age", store=True, readonly=True)
    dob = fields.Date(string="DOB")
    mobile = fields.Char(string="Mobile", help="Enter 10 digit mobile number", required=True,)
    email = fields.Char(string="Email")
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female')
    ], string="Gender")
    country_id = fields.Many2one('res.country', string="Country")
    country_ids = fields.Many2many('res.country', string="Countries")
    country_code = fields.Char(string="Country Code", related='country_id.code', store=True)
    staff_line_ids = fields.One2many('rest.staff.lines', 'connecting_field', string="Staff Lines")
    sequence = fields.Integer(string="Seq.")
    status = fields.Selection([
        ('active', 'Active'),
        ('resigned', 'Resigned')
    ], string="Status", default='active')
    image = fields.Image(string="Image", max_width=150, max_height=150)
    hand_salary = fields.Float(string="In hand Salary")
    epf_esi = fields.Float(string="EPF+ESI")
    ctc_salary = fields.Float(string="CTC Salary", compute="calc_ctc")
    seq_num = fields.Char(string="Seq no.", readonly=True, copy=False, index =True, default=lambda self: _('New'))
    rating = fields.Selection([('0','Very Low'),('1','Low'),('2','Normal'),('3','High'),('4','Very High'),('5','Excellent')], string="Rate me" )
    active = fields.Boolean(string="Active", default=True)
    
    default_date =fields.Date(string="Default Date", default=lambda self: date.today())
    default_datetime =fields.Datetime(string="Default Datetime", default=lambda self: datetime.now())   
    login_user =fields.Many2one('res.users' ,string="User",default=lambda self: self.env.user.id)
    user_company =fields.Many2one('res.company' ,string="Company", default=lambda self: self.env.user.company_id.id)
    button_integer = fields.Integer(String="Button Integer")
    department = fields.Many2one('rest.department', string="Department")
    
    
    @api.depends('hand_salary', 'epf_esi')
    def calc_ctc(self):
        for record in self:
            hand_salary = record.hand_salary or 0
            epf_esi = record.epf_esi or 0
            record.ctc_salary = hand_salary + epf_esi
    
    @api.model
    def default_get(self, fields):
        res = super(Reststaff, self).default_get(fields)
        list = [ ]
        countries = self.env['res.country'].search([('name','=','India')],limit=1)
        for rec in countries:
            list.append(rec.id)

        res['name'] = 'New'
        res['age'] = 19
        res['email'] = 'test@gmail.com'
        res['mobile'] = '1234567890'
        res['dob'] = date.today()
        res['gender'] = 'male'
        res['country_ids'] = [(6,0,list)]
        res['staff_line_ids'] = [(0, 0, {'name': 'First Record', 'product_id': 2}), (0, 0, {'name': 'Second Record', 'product_id': 1})]
        print("default_get res:", res)
        return res        

class RestStaffLine(models.Model):
    _name = 'rest.staff.lines'
    _description = 'Staff Line for each Staff member'

    connecting_field = fields.Many2one('rest.staff', string="Staff", required=True, ondelete='cascade')
    name = fields.Char(string="Name", required=True)
    product_id = fields.Many2one('product.product', string="Product")
    sequence = fields.Integer(string="Seq.")

