{
    'name': 'Custom Sale',
    'version': '18.0.10.0',
    'summary': 'Custom Sale',
    'sequence': -100,
    'description': """Custom Sale Module for handling custom sales processes and workflows.""",
    'category': 'for study purpose',
    'website': 'https://www.odoo.com',
    'depends': ['sale', 'account'],
    'data': [
        'data/user_details_mail.xml',
        'views/sale_order_view.xml',
        'views/account_move_view.xml',
        'views/invoice_report.xml',
        'reports/report_file.xml'
        
],
    'demo': [ ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
   
}
