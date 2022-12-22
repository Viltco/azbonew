


from datetime import datetime

from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError


class MRPWizard(models.TransientModel):
    _name = 'mrp.wizard'

    quantity = fields.Float(string='Quantity')
    uom_id = fields.Many2one('uom.uom', string='Unit of Measure')
    bom_id = fields.Many2one('mrp.bom', string='BOM')

    def action_create_mo(self):
        line_vals = []
        # bom_id = self.env['mrp.bom'].search([('product_id', '=', line.product_id.id)])
        # print(bom_id)
        # for bom_line in self.bom_id.bom_line_ids:
        #     line_vals.append((0, 0, {
        #         'product_id': bom_line.product_id.id,
        #         'name': bom_line.product_id.name,
        #         'location_id': self.bom_id.picking_type_id.default_location_src_id.id,
        #         'location_dest_id': 105,
        #         # 'product_uom_qty':  bom_line.product_qty * self.quantity,
        #         'product_uom_qty':  bom_line.product_qty * self.quantity,
        #         'product_uom': bom_line.product_uom_id.id,
        #     }))
        #     line_vals.append(line_vals)
        vals = {
            # 'picking_for_id': self.id,
            # 'product_id': self.bom_id.product_id.id,
            'product_id': self.bom_id.product_id.id,
            'company_id': self.env.user.company_id.id,
            'date_planned_start': fields.Date.today(),
            # 'move_raw_ids': line_vals,
            # 'location_src_id': 108,
            'location_src_id': self.bom_id.picking_type_id.default_location_src_id.id,
            # 'location_dest_id': 105,
            'location_dest_id': self.bom_id.picking_type_id.default_location_dest_id.id,
            # 'origin': self.name,
            'product_qty': self.quantity,
            'product_uom_id': self.uom_id.id,
        }
        mrp = self.env['mrp.production'].create(vals)
        # mrp.onchange_product_id()
        # mrp._onchange_bom_id()
        # mrp._onchange_product_qty()
        mrp._onchange_move_raw()
        mrp._onchange_move_finished()
        mrp._onchange_location_dest()
        mrp._onchange_producing()
        # mrp._onchange_workorder_ids()
        # self.show_create_mo = False
        self.bom_id.is_press_sample = True

    # def action_create_mo(self):
    #     line_val = []
    #     for line in self.bom_id.bom_line_ids:
    #         line_val.append((0, 0, {
    #             'product_id': line.product_id.id,
    #             'name': line.product_id.name,
    #             'location_id': self.bom_id.picking_type_id.default_location_src_id.id,
    #             'location_dest_id': 105,
    #             'product_uom_qty': line.product_qty,
    #             'product_uom': line.product_uom_id.id,
    #         }))
    #     record = self.env['mrp.production'].create({
    #         'date_planned_start': datetime.today(),
    #         'company_id': self.env.company.id,
    #         'user_id': self.env.user.id,
    #         'location_src_id': self.bom_id.picking_type_id.default_location_src_id.id,
    #         'location_dest_id': self.bom_id.picking_type_id.default_location_dest_id.id,
    #         'product_uom_id': self.uom_id.id,
    #         'bom_id': self.bom_id.id,
    #         'product_id': self.bom_id.product_tmpl_id.product_variant_id.id,
    #         'product_qty': self.quantity,
    #         # 'product_qty': 5,
    #         # 'qty_producing': self.quantity,
    #         'move_raw_ids': line_val,
    #         # 'state': 'to_close',
    #     })
        # record.onchange_product_id()
        # record.action_confirm()
        # if not record.product_id:
        #     record.bom_id = False
        # elif not record.bom_id or record.bom_id.product_tmpl_id != record.product_tmpl_id or (record.bom_id.product_id and record.bom_id.product_id != record.product_id):
        #     bom = self.env['mrp.bom']._bom_find(product=record.product_id, picking_type=record.picking_type_id, company_id=record.company_id.id, bom_type='normal')
        #     if bom:
        #         record.bom_id = bom.id
        #         record.product_qty = record.bom_id.product_qty
        #         record.product_uom_id = record.bom_id.product_uom_id.id
        #     else:
        #         record.bom_id = False
        #         record.product_uom_id = record.product_id.uom_id.id