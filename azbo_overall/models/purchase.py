# -*- coding: utf-8 -*-

from collections import defaultdict
from datetime import datetime
from itertools import groupby
from operator import itemgetter
from re import findall as regex_findall
from re import split as regex_split

from dateutil import relativedelta

from odoo import SUPERUSER_ID, _, api, fields, models
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools.float_utils import float_compare, float_is_zero, float_repr, float_round
from odoo.tools.misc import format_date, OrderedSet
from odoo.exceptions import AccessError, UserError


class PurchaseOrderInherit(models.Model):
    _inherit = 'purchase.order'

    total_quantity = fields.Float(string='Total Quantity', compute='compute_total_quantity')

    state = fields.Selection([
        ('draft', 'RFQ'),
        ('sent', 'RFQ Sent'),
        ('approve', 'Waiting For Approval'),
        ('to approve', 'To Approve'),
        ('purchase', 'Purchase Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
        ('rejected', 'Rejected'),
    ], string='Status', readonly=True, index=True, copy=False, default='draft', tracking=True)

    def compute_total_quantity(self):
        t = 0
        for rec in self.order_line:
            t = t + rec.product_qty
        self.total_quantity = t

    def button_confirm(self):
        is_approve = self.env['ir.config_parameter'].get_param('azbo_overall.is_po_approval')
        min_qty = self.env['ir.config_parameter'].get_param('azbo_overall.min_qty')
        max_qty = self.env['ir.config_parameter'].get_param('azbo_overall.max_qty')
        min_price = self.env['ir.config_parameter'].get_param('azbo_overall.min_price')
        flag = False
        for line in self.order_line:
            if line.product_qty < float(min_qty) or line.product_qty > float(max_qty) or self.amount_total > float(min_price):
                flag = True
        if is_approve:
            if flag == True:
                self.write({
                    'state': 'approve'
                })
            # if self.total_quantity < float(min_qty) or self.total_quantity > float(max_qty):
            #     self.write({
            #         'state': 'approve'
            #     })
            else:
                for order in self:
                    if order.state not in ['draft', 'sent']:
                        continue
                    order._add_supplier_to_product()
                    # Deal with double validation process
                    if order.company_id.po_double_validation == 'one_step' \
                            or (order.company_id.po_double_validation == 'two_step' \
                                and order.amount_total < self.env.company.currency_id._convert(
                                order.company_id.po_double_validation_amount, order.currency_id, order.company_id,
                                order.date_order or fields.Date.today())) \
                            or order.user_has_groups('purchase.group_purchase_manager'):
                        order.button_approve()
                    else:
                        order.write({'state': 'to approve'})
                    if order.partner_id not in order.message_partner_ids:
                        order.message_subscribe([order.partner_id.id])
                # for line in self.order_line:
                #     line.move_ids.description = line.name
                #     for rec_line in line.move_ids.move_line_ids:
                #         rec_line.description = line.name
                return True
        else:
            for order in self:
                if order.state not in ['draft', 'sent']:
                    continue
                order._add_supplier_to_product()
                # Deal with double validation process
                if order.company_id.po_double_validation == 'one_step' \
                        or (order.company_id.po_double_validation == 'two_step' \
                            and order.amount_total < self.env.company.currency_id._convert(
                            order.company_id.po_double_validation_amount, order.currency_id, order.company_id,
                            order.date_order or fields.Date.today())) \
                        or order.user_has_groups('purchase.group_purchase_manager'):
                    order.button_approve()
                else:
                    order.write({'state': 'to approve'})
                if order.partner_id not in order.message_partner_ids:
                    order.message_subscribe([order.partner_id.id])
            for line in self.order_line:
                line.move_ids.description = line.name
                for rec_line in line.move_ids.move_line_ids:
                    rec_line.description = line.name
            return True

    def action_reset(self):
        self.write({
            'state': 'draft'
        })

    def button_approved(self):
        for order in self:
            if order.state not in ['draft', 'sent', 'approve']:
                continue
            order._add_supplier_to_product()
            # Deal with double validation process
            if order.company_id.po_double_validation == 'one_step' \
                    or (order.company_id.po_double_validation == 'two_step' \
                        and order.amount_total < self.env.company.currency_id._convert(
                        order.company_id.po_double_validation_amount, order.currency_id, order.company_id,
                        order.date_order or fields.Date.today())) \
                    or order.user_has_groups('purchase.group_purchase_manager'):
                order.button_approve()
            else:
                order.write({'state': 'to approve'})
            if order.partner_id not in order.message_partner_ids:
                order.message_subscribe([order.partner_id.id])
        # for line in self.order_line:
        #     line.move_ids.description = line.name
        #     for rec_line in line.move_ids.move_line_ids:
        #         rec_line.description = line.name
        return True

    def button_reject(self):
        self.write({
            'state': 'rejected'
        })