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


class CRMLeadInh(models.Model):
    _inherit = 'crm.lead'

    x_css = fields.Html(string='CSS', sanitize=False, compute='_compute_css')
    y_css = fields.Html(string='CSS', sanitize=False, compute='_compute_y_css')

    bom_count = fields.Integer(compute='get_bom_count')

    def action_order_cost_sheet(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Bill of Material',
            'view_id': self.env.ref('mrp.mrp_bom_form_view', False).id,
            'target': 'current',
            'context': {'default_lead_id': self.id},
            'res_model': 'mrp.bom',
            'view_mode': 'form',
        }

    def action_pre_order_cost_sheet(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Bill of Material',
            # 'view_id': self.env.ref('mrp.mrp_bom_form_view', False).id,
            'target': 'current',
            'domain': [('lead_id', '=', self.id)],
            'res_model': 'mrp.bom',
            'view_mode': 'tree,form',
        }

    def get_bom_count(self):
        for rec in self:
            count = self.env['mrp.bom'].search_count([('lead_id', '=', self.id)])
            rec.bom_count = count

    def _compute_css(self):
        for application in self:
            # Modify below condition
            application.x_css = '<style>.o_button_generate_leads {display: none !important;}</style>'

    def _compute_y_css(self):
        for application in self:
            application.y_css = '<style>.o_ChatterTopbar_buttonSendMessage {display: none !important;}</style>'