from odoo import models, fields, api


class ConfigSettingsInherit(models.TransientModel):
    _inherit = 'res.config.settings'

    is_po_approval = fields.Boolean('QTY PO Approval', config_parameter='azbo_overall.is_po_approval')

    min_qty = fields.Float(string='Minimum Quantity',
                           config_parameter='azbo_overall.min_qty')

    max_qty = fields.Float(string='Maximum Quantity',
                           config_parameter='azbo_overall.max_qty')

    min_price = fields.Float(string='Minimum Price',
                           config_parameter='azbo_overall.min_price')


