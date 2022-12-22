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


class BOMInh(models.Model):
    _inherit = 'mrp.bom'

    lead_id = fields.Many2one('crm.lead', 'Inquiry Ref')