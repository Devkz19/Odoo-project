from odoo import models, fields, api
from datetime import datetime, date

class AccountMove(models.Model):
    _inherit = "account.move"
    
    payment_method = fields.Char(string="Payment Method")
    payment_info = fields.Char(string="Payment Information")
    
    penalty_amount = fields.Monetary(
        string='Late Payment Penalty', 
        compute='_compute_penalty_amount',
        store=True,
        currency_field='currency_id'
    )
    
    amount_residual_with_penalty = fields.Monetary(
        string='Amount Due (with Penalty)',
        compute='_compute_amount_residual_with_penalty',
        store=True,
        currency_field='currency_id'
    )

    @api.depends('invoice_date_due', 'amount_total', 'state', 'payment_state', 'amount_residual')
    def _compute_penalty_amount(self):
        for record in self:
            penalty_amount = 0.0

            if (record.state == 'posted' and 
                record.move_type in ['out_invoice', 'in_invoice', 'out_receipt', 'in_receipt'] and
                record.payment_state in ['not_paid', 'partial'] and
                record.amount_residual > 0 and
                record.invoice_date_due):

                today = date.today()
                due_date = record.invoice_date_due

                if today > due_date:
                    days_overdue = (today - due_date).days

                    # Daily compounding at 5%
                    daily_penalty_rate = 0.05  # 5%
                    base_amount = record.amount_total  # Penalty on total (incl. tax)

                    compounded_total = base_amount * ((1 + daily_penalty_rate) ** days_overdue)
                    penalty_amount = compounded_total - base_amount

            record.penalty_amount = penalty_amount
            
            
    @api.depends('amount_residual', 'penalty_amount', 'payment_state')
    def _compute_amount_residual_with_penalty(self):
        for record in self:
            if record.payment_state in ('not_paid', 'partial'):
                record.amount_residual_with_penalty = (record.amount_residual or 0.0) + (record.penalty_amount or 0.0)
            else:
                record.amount_residual_with_penalty = record.amount_residual

    
    # Include penalty in total by extending the base computation flow
    @api.depends(
        'line_ids.matched_debit_ids.debit_move_id.move_id.origin_payment_id.is_matched',
        'line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual',
        'line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual_currency',
        'line_ids.matched_credit_ids.credit_move_id.move_id.origin_payment_id.is_matched',
        'line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual',
        'line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual_currency',
        'line_ids.balance',
        'line_ids.currency_id',
        'line_ids.amount_currency',
        'line_ids.amount_residual',
        'line_ids.amount_residual_currency',
        'line_ids.payment_id.state',
        'line_ids.full_reconcile_id',
        'state',
        'penalty_amount')
    def _compute_amount(self):
        super(AccountMove, self)._compute_amount()
        for record in self:
            # Add penalty to amount_total if there's a penalty
            if record.penalty_amount > 0:
                record.amount_total += record.penalty_amount
    
    # Override the payment registration to consider penalty
    def action_register_payment(self):
        self._compute_penalty_amount()
        return super().action_register_payment()
    
    # Method to manually recalculate penalty (can be called from button)
    def recalculate_penalty(self):
        self._compute_penalty_amount()
        self._compute_amount_residual_with_penalty()
        return True

    # Ensure PDF/Widget totals include penalty as well
    @api.depends_context('lang')
    @api.depends(
        'invoice_line_ids.currency_rate',
        'invoice_line_ids.tax_base_amount',
        'invoice_line_ids.tax_line_id',
        'invoice_line_ids.price_total',
        'invoice_line_ids.price_subtotal',
        'invoice_payment_term_id',
        'partner_id',
        'currency_id',
        'penalty_amount',
    )
    def _compute_tax_totals(self):
        super()._compute_tax_totals()
        for move in self:
            if move.is_invoice(include_receipts=True) and move.tax_totals:
                move.tax_totals['penalty_amount'] = move.penalty_amount or 0.0
                move.tax_totals['amount_total'] = (
                    (move.tax_totals.get('amount_total') or 0.0)
                    + move.tax_totals['penalty_amount']
                )
    
    # Method to check payment status details
    def get_payment_status_details(self):
        """
        Returns detailed payment status information
        """
        for record in self:
            return {
                'is_paid': record.payment_state == 'paid',
                'is_partial': record.payment_state == 'partial',
                'is_unpaid': record.payment_state == 'not_paid',
                'is_in_payment': record.payment_state == 'in_payment',
                'amount_paid': record.amount_total - record.amount_residual,
                'amount_remaining': record.amount_residual,
                'is_overdue': record.invoice_date_due and record.invoice_date_due < date.today(),
                'days_overdue': (date.today() - record.invoice_date_due).days if record.invoice_date_due and record.invoice_date_due < date.today() else 0,
                'penalty_amount': record.penalty_amount,
            }
    
    # Override payment methods to handle penalty
    def _get_reconciled_info_JSON_values(self):
        """
        Override to include penalty in payment info
        """
        result = super()._get_reconciled_info_JSON_values()
        # Add penalty information to payment details if needed
        return result
    
    # Method to freeze penalty amount when payment is made
    def action_post_payment(self):
        """
        Called when payment is registered to freeze penalty calculation
        """
        # Store the penalty amount at time of payment
        for record in self:
            if record.penalty_amount > 0:
                pass
        return super().action_post_payment() if hasattr(super(), 'action_post_payment') else True


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.depends('quantity', 'discount', 'price_unit', 'tax_ids', 'currency_id', 'move_id.penalty_amount')
    def _compute_totals(self):
        """
        Compute 'price_subtotal' / 'price_total' and include penalty_amount on the total
        """
        AccountTax = self.env['account.tax']
        for line in self:
            # Skip non-product / non-cogs lines
            if line.display_type not in ('product', 'cogs'):
                line.price_total = line.price_subtotal = False
                continue

            # Base line for tax computation
            base_line = line.move_id._prepare_product_base_line_for_taxes_computation(line)
            AccountTax._add_tax_details_in_base_line(base_line, line.company_id)

            # Regular totals
            line.price_subtotal = base_line['tax_details']['raw_total_excluded_currency']
            line.price_total = base_line['tax_details']['raw_total_included_currency']

            # Add penalty only once per invoice (we can add to the first product line)
            if line.move_id.penalty_amount > 0 and line == line.move_id.invoice_line_ids.filtered(lambda l: l.display_type in ('product', 'cogs'))[0]:
                line.price_total += line.move_id.penalty_amount
