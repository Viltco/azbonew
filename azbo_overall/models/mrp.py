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


class StockMoveInh(models.Model):
    _inherit = 'stock.move'

    so_id = fields.Many2one('sale.order', string='Sale Ref')


class MRPProdInh(models.Model):
    _inherit = 'mrp.production'

    so_id = fields.Many2one('sale.order', string='Sale Ref')

    picking_count = fields.Integer(compute='get_picking_count')
    move_entry_count = fields.Integer(compute='get_move_entry_count')

    def get_picking_count(self):
        for rec in self:
            count = self.env['stock.picking'].search_count([('mo_id', '=', self.id)])
            rec.picking_count = count

    def action_transfer_view(self):
        return {
            'name': _('Transfers'),
            'domain': [('mo_id', '=', self.id)],
            'view_type': 'form',
            'res_model': 'stock.picking',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
        }

    def get_move_entry_count(self):
        for rec in self:
            count = self.env['account.move'].search_count([('mo_id', '=', self.id)])
            rec.move_entry_count = count

    def action_move_entry_view(self):
        return {
            'name': _('Journal Entries'),
            'domain': [('mo_id', '=', self.id)],
            'view_type': 'form',
            'res_model': 'account.move',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
        }

    def button_mark_done(self):
        res = super(MRPProdInh, self).button_mark_done()
        if self.workorder_ids:
            self.action_general_entry()
        return res

    def action_general_entry(self):
        line_ids = []
        debit_sum = 0.0
        credit_sum = 0.0
        total = 0
        # journal = self.env['account.journal'].search([('type', '=', 'general')])
        for rec in self:
            for ln in rec.workorder_ids:
                journal = ln.workcenter_id.journal_id.id
                print(journal)
            move_dict = {
                'ref': rec.name,
                'journal_id': journal,
                'mo_id': self.id,
                'currency_id': 2,
                'date': datetime.today(),
                'move_type': 'entry',
                'state': 'draft',
            }
            # d_acc = self.env['account.account'].search([('name', '=', 'Finished Goods')])
            # c_acc = self.env['account.account'].search([('name', '=', 'Work In Process')])
            for line in rec.workorder_ids:
                total = total + (line.workcenter_id.costs_hour * (line.duration/60))
            debit_line = (0, 0, {
                'name': 'Outstanding',
                'debit': abs(total),
                'credit': 0.0,
                # 'partner_id': partner.id,
                'currency_id': 2,
                'account_id': line.workcenter_id.account_outstanding_id.id,
            })
            line_ids.append(debit_line)
            debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']
            credit_line = (0, 0, {
                'name': 'Intermediary',
                'debit': 0.0,
                'credit': abs(total),
                # 'partner_id': partner.id,
                'currency_id': 2,
                'account_id': line.workcenter_id.account_intermediary_id.id,
            })
            line_ids.append(credit_line)
            credit_sum += credit_line[2]['credit'] - credit_line[2]['debit']
        if line_ids:
            move_dict['line_ids'] = line_ids
            move = self.env['account.move'].create(move_dict)
            line_ids = []
            # move.button_approved()
            print("General entry created")


class BOMInh(models.Model):
    _inherit = 'mrp.bom'

    lead_id = fields.Many2one('crm.lead', 'Inquiry Ref')


class WorkCenterInh(models.Model):
    _inherit = 'mrp.workcenter'

    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')

    is_outsource = fields.Boolean('Out Source')

    picking_type_id = fields.Many2one('stock.picking.type', 'Operation Type')
    location_src_id = fields.Many2one('stock.location', 'Source Location')
    location_dest_id = fields.Many2one('stock.location', 'Destination Location')

    account_outstanding_id = fields.Many2one('account.account', 'Outstanding Account')
    account_intermediary_id = fields.Many2one('account.account', 'Intermediary Account')

    journal_id = fields.Many2one('account.journal', 'Journal')


class WorkOrderInh(models.Model):
    _inherit = 'mrp.workorder'

    def button_start(self):
        res = super(WorkOrderInh, self).button_start()
        self.action_create_internal_transfer(True)
        self.action_create_internal_transfer(False)
        return res

    def action_create_internal_transfer(self, check):
        vals = {
            'location_id': self.workcenter_id.location_src_id.id if check else self.workcenter_id.location_dest_id.id,
            'location_dest_id': self.workcenter_id.location_dest_id.id if check else self.workcenter_id.location_src_id.id,
            'picking_type_id': self.workcenter_id.picking_type_id.id,
            'mo_id': self.production_id.id,
        }
        picking = self.env['stock.picking'].create(vals)
        lines = {
            'picking_id': picking.id,
            'product_id': self.production_id.product_id.id,
            'name': self.production_id.product_id.name,
            'product_uom': self.production_id.product_uom_id.id,
            'location_id': self.workcenter_id.location_src_id.id if check else self.workcenter_id.location_dest_id.id,
            'location_dest_id': self.workcenter_id.location_dest_id.id if check else self.workcenter_id.location_src_id.id,
            'product_uom_qty': self.production_id.product_qty,
        }
        stock_move = self.env['stock.move'].create(lines)

