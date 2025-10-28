{
    'name': 'Training Management System ',
    'version': '18.0.10.0',
    'summary': 'Teacher Trainig Management',
    'sequence': -101,
    'description': """Through this module teacher can manage their student trainig.""",
    'category': 'Human Resources',
    'website': 'https://www.odoo.com',
    'depends': ['base', 'mail', 'web', ],
    'data': [
        'security/ir.model.access.csv',
        'security/training_security.xml',
        'views/teacher.xml',
        'views/student.xml',
        'data/teacher_data.xml',
        'data/student_data.xml',

    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'images': ['static/description/icon.png']
}
