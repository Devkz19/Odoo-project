from odoo import http
from odoo.http import request, route

class RingoverController(http.Controller):
    @route('/ringover/webhook', type='json', auth='public', methods=['POST'], csrf=False)
    def ringover_webhook(self, **kwargs):
        data = request.jsonrequest
        phone_number = data.get('phone_number')
        if phone_number:
            request.env['mail.activity'].sudo()._ringover_mark_as_done(phone_number)
        return {'status': 'success'}
