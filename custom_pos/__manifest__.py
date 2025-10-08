{
    'name': 'Custom POS',
    'version': '18.0.10.0',
    'summary': 'Custom POS',
    'sequence': -100,
    'description': """Custom pos to add button.""",
    'category': 'for study purpose',
    'website': 'https://www.odoo.com',
    'depends': ['base', 'point_of_sale'],
    'data': [],
    'assets': {
        'point_of_sale._assets_pos': [
            'custom_pos/static/src/**/*',
        ],
    },
  
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}