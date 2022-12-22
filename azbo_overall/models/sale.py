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


class SaleInh(models.Model):
    _inherit = 'sale.order'

    mo_count = fields.Integer(compute='get_mo_count')

    req_count = fields.Integer(compute='get_req_count')

    bom_id = fields.Many2one('mrp.bom', 'BOM Ref')

    def button_create_mo(self):
        bom_line_val = []
        for line in self.order_line:
            for bom_line in self.bom_id.bom_line_ids:
                bom_line_val.append((0, 0, {
                    'product_id': bom_line.product_id.id,
                    'name': bom_line.product_id.name,
                    'location_id': 2,
                    'location_dest_id': 1,
                    'product_uom_qty': bom_line.product_qty,
                    'product_uom': bom_line.product_uom_id.id,
                }))
            # line_val.append((0, 0, {
            #     'product_id': line.product_id.id,
            #     'name': line.product_id.name,
            #     'location_id': 2,
            #     'location_dest_id': 1,
            #     'product_uom_qty': line.product_uom_qty,
            #     'product_uom': line.product_uom.id,
            # }))
            record = self.env['mrp.production'].create({
                'date_planned_start': datetime.today(),
                'company_id': self.env.company.id,
                'user_id': self.env.user.id,
                'location_src_id': self.bom_id.picking_type_id.default_location_src_id.id,
                'location_dest_id': self.bom_id.picking_type_id.default_location_dest_id.id,
                'product_uom_id': line.product_uom.id,
                # 'product_uom_id': self.uom_id.id,
                'so_id': self.id,
                'bom_id': self.bom_id.id,
                # 'product_id': self.bom_id.product_tmpl_id.product_variant_id.id,
                'product_id': line.product_id.id,
                'product_qty': line.product_uom_qty,
                'move_raw_ids': bom_line_val,
            })
            record.action_confirm()

    def get_mo_count(self):
        for rec in self:
            count = self.env['mrp.production'].search_count([('so_id', '=', self.id)])
            rec.mo_count = count

    def action_mo_order_view(self):
        return {
            'name': _('Manufacturing Orders'),
            'domain': [('so_id', '=', self.id)],
            'view_type': 'form',
            'res_model': 'mrp.production',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
        }

    def get_req_count(self):
        for rec in self:
            count = self.env['material.purchase.requisition'].search_count([('so_id', '=', self.id)])
            rec.req_count = count

    def action_req_view(self):
        return {
            'name': _('Requisitions'),
            'domain': [('so_id', '=', self.id)],
            'view_type': 'form',
            'res_model': 'material.purchase.requisition',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
        }

    def button_create_requisition(self):
        bom_line_val = []
        # for line in self.order_line:
        for bom_line in self.bom_id.bom_line_ids:
            bom_line_val.append((0, 0, {
                'product_id': bom_line.product_id.id,
                'description': bom_line.product_id.name,
                # 'location_id': 2,
                # 'location_dest_id': 1,
                'qty': bom_line.product_qty,
                'uom': bom_line.product_uom_id.id,
                'requisition_type': 'internal',
            }))
        # line_val.append((0, 0, {
        #     'product_id': line.product_id.id,
        #     'name': line.product_id.name,
        #     'location_id': 2,
        #     'location_dest_id': 1,
        #     'product_uom_qty': line.product_uom_qty,
        #     'product_uom': line.product_uom.id,
        # }))
        record = self.env['material.purchase.requisition'].create({
            'request_date': datetime.today(),
            'company_id': self.env.company.id,
            'employee_id': self.env.user.employee_id.id,
            'department_id': self.env.user.employee_id.department_id.id,
            # 'location_src_id': self.bom_id.picking_type_id.default_location_src_id.id,
            # 'location_dest_id': self.bom_id.picking_type_id.default_location_dest_id.id,
            # 'product_uom_id': line.product_uom.id,
            # 'product_uom_id': self.uom_id.id,
            'so_id': self.id,
            # 'bom_id': self.bom_id.id,
            # 'product_id': self.bom_id.product_tmpl_id.product_variant_id.id,
            # 'product_id': line.product_id.id,
            # 'product_qty': line.product_uom_qty,
            'requisition_line_ids': bom_line_val,
        })
        record.requisition_confirm()

