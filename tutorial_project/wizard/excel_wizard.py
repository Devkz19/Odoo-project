from odoo import models, fields, api, _
import xlwt
import base64
from io import BytesIO

class CustomExcelwizard(models.TransientModel):
    _name = 'custom.excel.wizard'
    _description = 'This is a wizard model which will print excel report'
    
    gender= fields.Selection(string='Gender',
      selection=[('male', 'Male'), ('female', 'female')]
  )
  
    def print_excel(self):
        active_id = self._context.get('active_id')
        print('active_id',active_id)
        self = self.env['rest.staff'].browse(active_id)
        filename = (self.name or 'staff_excel_report') + '.xls'  
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
    
    def print_excel_report_by_menu(self):
        filename = 'staff-report.xls'  
        workbook = xlwt.Workbook(encoding='utf-8')
        sheet1 = workbook.add_sheet('staff', cell_overwrite_ok=True)

        date_format = xlwt.XFStyle() 
        date_format.num_format_str = 'DD/MM/YY'

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
        
        
        domain=[]
        if self.gender:
            domain.append(('gender','=',self.gender))  
        print("domain-----",domain)    
                
        order = self.env['rest.staff'].search(domain)

        # Set column widths
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

        # Header row
        headers = ["Name", "Email", "Mobile", "Age", "DOB", "Country", "Gender", "Ref. Countries", "Name(o2m)", "Product(o2m)"]
        for col, header in enumerate(headers):
            sheet1.write(0, col, header, format1)

        j = 1  # Start from second row
        for rec in order:
          
            countries = ", ".join([rec2.name for rec2 in rec.country_ids])

            sheet1.write(j, 0, rec.name, format2)
            sheet1.write(j, 1, rec.email, format2)
            sheet1.write(j, 2, rec.mobile, format2)
            sheet1.write(j, 3, rec.age, format2)
            sheet1.write(j, 4, rec.dob, date_format)
            sheet1.write(j, 5, rec.country_id.name, format2)
            sheet1.write(j, 6, rec.gender, format2)
            sheet1.write(j, 7, countries, format2)

            i = j
            for rec2 in rec.staff_line_ids:
                sheet1.write(i, 8, rec2.name, format2)
                sheet1.write(i, 9, rec2.product_id.name, format2)
                i += 1
            j = max(i, j + 1)

        # Print footer message
        sheet1.row(j).height = 200    
        sheet1.write_merge(j, j + 1, 0, 9, 'Report is Printed', format1)

        # Save to BytesIO
        stream = BytesIO()
        workbook.save(stream)
        out = base64.encodebytes(stream.getvalue())

        # Create download record
        excel_id = self.env['custom.excel.class'].create({
            "datas_frame": filename, 
            "file_name": out.decode('utf-8') 
        })

        # Return action to download
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'custom.excel.class',
            'res_id': excel_id.id,
            'view_mode': 'form',
            'target': 'new', 
        }  
            