from . import data
import odoo.tests.common as common
import mock
from odoo.addons.fleet_fpz.foaie_de_parcurs import foaie_de_parcurs
from odoo.addons.fleet.vehicle import fleet.vehicle
import datetime
class test_foaie_de_parcurs(common.TransactionCase):
    def test_compute_cn(self):
        brand_id = self.env['fleet.vehicle.model.brand'].create({'name': 'BrandX'}).id
        model_id = self.env['fleet.vehicle.model'].create({'brand_id': brand_id, 'name': 'ModelX'}).id
        vehicle_id = self.env['fleet.vehicle'].create({'model_id': model_id, 'cm': 8.3})
        record = self.env['fleet_fpz.foaie_de_parcurs'].create({'vehicle_id': vehicle_id, 'date': datetime.datetime.today()})
        #record.some_action()
        self.assertEqual(
            record.consum_comb,
            10)
