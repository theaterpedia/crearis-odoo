# -*- coding: utf-8 -*-
# Copyright 2025 Hans Dönitz - Theaterpedia.org
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, tools


class DemoDataMixin(models.AbstractModel):
    """Mixin to detect and mark demo data"""
    
    _name = 'demo.data.mixin'
    _description = 'Demo Data Detection Mixin'

    is_demo = fields.Boolean(
        string='Is Demo Data',
        compute='_compute_is_demo',
        store=False,
        help='True if this record is demo data (XML ID starts with _demo)'
    )

    def _compute_is_demo(self):
        """Check if record has XML ID starting with _demo"""
        # Check config parameter to see if we should even bother checking
        ICP = self.env['ir.config_parameter'].sudo()
        include_demo = ICP.get_param('crearis.graphql.include_demo', 'True')
        
        # If demo is disabled globally, we still need to compute it for UI
        # but GraphQL can skip outputting these records
        
        for record in self:
            record.is_demo = False
            
            if not record.id:
                continue
                
            # Get XML ID for this record
            xml_ids = record.get_external_id()
            if xml_ids and xml_ids.get(record.id):
                xml_id = xml_ids[record.id]
                # Check if XML ID starts with _demo (after the module prefix)
                # Format is usually: module_name._demo_record_name
                xml_id_parts = xml_id.split('.')
                if len(xml_id_parts) > 1:
                    record.is_demo = xml_id_parts[-1].startswith('_demo')