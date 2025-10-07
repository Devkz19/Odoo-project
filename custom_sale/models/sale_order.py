from odoo import models, fields, api
import base64
import io
from openpyxl import Workbook


class SaleOrder(models.Model):
    _inherit = "sale.order"

    payment_method = fields.Char(string="Payment Method")
    payment_info = fields.Char(string="Payment Information")
    
    def action_done_custom(self):
        """ Confirm Sale Orders and send email notification """
        for order in self:
            # Confirm the sale order if it's in draft or sent state
            if order.state in ['draft', 'sent']:
                order.action_confirm()

            # Find the mail template
            template = self.env.ref('custom_sale.mail_template_sale_summary', raise_if_not_found=False)
            if template:
                template.send_mail(order.id, force_send=True)
        return True
    
    @api.model
    def create(self, vals):
        # If no custom name is provided, use our custom sequence
        if vals.get('name', 'New') == 'New':
            seq = self.env['ir.sequence'].next_by_code('sale.order') or '/'
            vals['name'] = seq.replace("S", "SO-2025-")  
        return super(SaleOrder, self).create(vals)
  
    def _prepare_invoice(self):
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        invoice_vals['payment_method'] = self.payment_method
        invoice_vals['payment_info'] = self.payment_info
        return invoice_vals
    
    def action_export_excel(self):
        """Export current sale order details to Excel"""
        for order in self:
            wb = Workbook()
            ws = wb.active
            ws.title = "Sales Order"

            # Header
            headers = ["Order", "Customer", "Product", "Quantity", "Unit Price", "Subtotal"]
            ws.append(headers)

            # Add order lines
            for line in order.order_line:
                ws.append([
                    order.name,
                    order.partner_id.name,
                    line.product_id.display_name,
                    line.product_uom_qty,
                    line.price_unit,
                    line.price_subtotal
                ])

            # Adjust column widths
            column_widths = {
                "A": 15, "B": 25, "C": 40, "D": 12, "E": 15, "F": 15,
            }
            for col, width in column_widths.items():
                ws.column_dimensions[col].width = width

            fp = io.BytesIO()
            wb.save(fp)
            excel_file = base64.b64encode(fp.getvalue())
            fp.close()

            attachment = self.env['ir.attachment'].create({
                'name': f'{order.name}.xlsx',
                'type': 'binary',
                'datas': excel_file,
                'res_model': 'sale.order',
                'res_id': order.id,
                'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            })

            return {
                'type': 'ir.actions.act_url',
                'url': f'/web/content/{attachment.id}?download=true',
                'target': 'self',
            }

    def action_quotation_send(self):
        """
        Override Sale Quotation Send by Email to replace the default attachment
        with custom ones (Odoo 18).
        """
        action = super().action_quotation_send()
        ctx = dict(action.get("context", {}))
        custom_attachments = self._generate_custom_attachments()

        if custom_attachments:
            ctx.update({
                "default_attachment_ids": [(6, 0, [att.id for att in custom_attachments])]
            })
        else:
            ctx.update({
                "default_attachment_ids": []
            })

        action["context"] = ctx
        return action

    def _generate_custom_attachments(self):
        """Generates multiple custom PDF reports for Sales Order (Odoo 18)."""
        if not self:
            return []
            
        record = self[0] 
        attachments = []

        # Report 1: Custom Quotation Report
        att1 = self._generate_single_report(
            record, 
            "custom_sale.action_report_custom_quotation",
            "Custom Quotation Report"
        )
        if att1:
            attachments.append(att1)

        return attachments

    def _generate_single_report(self, record, report_ref, report_prefix):
        """Helper method to generate a single report attachment (Odoo 18)."""
        try:
            report = self.env.ref(report_ref, raise_if_not_found=False)
            if not report:
                return None

            pdf_content, _ = report._render_qweb_pdf(
                report.report_name, 
                res_ids=[record.id]
            )

            attachment = self.env["ir.attachment"].create({
                "name": f"{report_prefix} - {record.name}.pdf",
                "type": "binary",
                "datas": base64.b64encode(pdf_content),
                "res_model": "sale.order",
                "res_id": record.id,
                "mimetype": "application/pdf",
            })
            return attachment

        except Exception:
            return None
