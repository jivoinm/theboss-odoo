# -*- coding: utf-8 -*-
from odoo import models, fields, api
from urllib2 import Request, urlopen
from dateutil import tz
import requests, json, logging, datetime, os.path
import sys, traceback
from math import cos, asin, sqrt
from dateutil.parser import parse as parse_date

_logger = logging.getLogger(__name__)

reload(sys)
sys.setdefaultencoding('utf-8')
class car_import(models.AbstractModel):
    _name = "fleet_fpz.car_import"

    website = 'www22.alarma.ro'
    username = 'frasinuldwn'
    password = '12345'

    api_key = "40789C4685884267B0265B6379F595D9"
    api_base_url = "https://fms.vodafone.ro/_layouts/15/S2/WebApi/StandardApi/";

    from_zone = tz.tzutc()
    to_zone = tz.tzlocal()
    basepath = os.path.dirname(__file__)
    filepath = os.path.abspath(os.path.join(basepath, "judete_orase.json"))

    with open(filepath, "r") as data_file:
        judete_orase = json.load(data_file)

    def get_alarme_cars(self, token):
        headers = {
          'Content-Type': 'application/json',
          'Token': token
        }
        url = "https://%s/SASFleetService/api/info" % self.website
        response_body = requests.get(url, params={'api-version': '1.0'}, headers=headers)
        return Payload(response_body.content)
    @api.model
    def import_cars_alarme(self):
        token = self.alarme_login()
        payload = self.get_alarme_cars(token)
        #create company
        companies = {}
        gps_tag = 'alarme'
        alarme_tag_id = self.env['fleet.vehicle.tag'].search([['name', '=', gps_tag]], limit=1).id or self.env['fleet.vehicle.tag'].create({'name': gps_tag}).id

        for company in payload.companies:
            odoo_company = self.env['res.company'].search([['name', '=ilike', company['name']]], limit=1)
            if not company['companyId'] in companies:
                companies[company['companyId']] = odoo_company.id or self.env['res.company'].create({'name': company['name']}).id

        for car in payload.cars:
            br = [branch['name'] for branch in payload.branches if branch['branchId'] == car['branchId']]
            wp = [workpoint['name'] for workpoint in payload.workPoints if workpoint['branchId'] == car['branchId'] and workpoint['workPointId'] == car['workPointId']]
            car_details = self.alarme_load_car_details(token, car['carId'])
            brand_id = self.env['fleet.vehicle.model.brand'].search([['name', '=', car_details.makeName]], limit=1).id or self.env['fleet.vehicle.model.brand'].create({'name': car_details.makeName}).id
            model = self.env['fleet.vehicle.model'].search([['name', '=', car_details.modelName], ['brand_id', '=', brand_id]], limit=1) or self.env['fleet.vehicle.model'].create({'name': car_details.modelName, 'brand_id': brand_id})
            #create or update cars
            self.import_cars(car['driver'], car['licensePlate'], model, car_details.currentKmIndex, car_details.tankCapacity, companies[car['companyId']], car_details.vin, wp[0], datetime.datetime(year=car_details.year, month=1, day=1), [(4,[alarme_tag_id])], car['carId'])



    def alarme_load_car_details(self, token, carId):
        url = "https://%s/SASFleetService/api/car/carDetails" % self.website
        headers = {
          'Content-Type': 'application/json',
          'Token': token
        }
        response_body = requests.post(url, params={'api-version': '1.0'}, headers=headers, data=str(carId))
        car_details = Payload(response_body.content)
        return car_details

    def alarme_login(self):
        values = {
            "user": self.username,
            "password": self.password,
            "culture": "ro-RO"
          }

        headers = {
          'Content-Type': 'application/json'
        }
        url = "https://%s/SASFleetService/api/login" % self.website
        values = json.dumps(values, sort_keys=True, indent=4, separators=(',', ': '))
        response_body = requests.post(url, params={'api-version': '1.0'}, headers=headers, data=values)
        return response_body.headers['Token']

    @api.model
    def import_cars_fms(self):
        url = self.api_base_url + "GetVehicles.ashx"
        response_body = requests.post(url, params={'accessToken': self.api_key, 'format':'json'})
        cars = json.loads(response_body.content)
        gps_tag = 'fms vodafone'
        fms_tag_id = self.env['fleet.vehicle.tag'].search([['name', '=', gps_tag]], limit=1).id or self.env['fleet.vehicle.tag'].create({'name': gps_tag}).id
        for car in cars:
            company_id = self.env['res.company'].search([['name', '=ilike', car['Group']]], limit=1).id or self.env['res.company'].create({'name': car['Group']}).id
            brand_id = self.env['fleet.vehicle.model.brand'].search([['name', '=', car['Mark']]], limit=1).id or self.env['fleet.vehicle.model.brand'].create({'name': car['Mark']}).id
            model = self.env['fleet.vehicle.model'].search([['name', '=', car['Model']], ['brand_id', '=', brand_id]], limit=1) or self.env['fleet.vehicle.model'].create({'name': car['Model'], 'brand_id': brand_id})
            self.import_cars(None, car['VehiclePlate'], model, None, None, company_id, None, None, None, [(4,[fms_tag_id])])
        #import drivers
        url = self.api_base_url + "GetDrivers.ashx"
        response_body = requests.post(url, params={'accessToken': self.api_key, 'format':'json'})
        drivers = json.loads(response_body.content)
        for driver in drivers:
            self.create_driver_employee(driver['DriverName'])

    def import_cars(self, driver_name, license_plate, model, current_km, tank_capacity, company_id, vin, location, acquisition_date, tags, car_id=None):
        vehicle = self.env['fleet.vehicle'].search([['license_plate', '=', license_plate]], limit=1)
        if not vehicle.id:
            #create driver
            driver_id = None
            if driver_name:
                self.create_driver_employee(driver_name)
            #create vehicle
            self.env['fleet.vehicle'].create({
                'license_plate': license_plate,
                'model_id': model.id,
                'odometer': current_km,
                'tank_capacity': tank_capacity,
                'vin_sn': vin,
                'company_id': company_id,
                'driver_id': driver_id,
                'location': location,
                'acquisition_date': acquisition_date,
                'tag_ids': tags,
                'external_carid': car_id,
                'cm': 8.5 if model.brand_id.name == 'Volkswagen' else 30,
                'sarcina_utila_nominala': 0.8 if model.brand_id.name == 'Volkswagen' else 3,
                'spor_buc': 10 if model.brand_id.name == 'Volkswagen' else 5,
                'spor_buc_cu_remorca': 0 if model.brand_id.name == 'Volkswagen' else 10,
                'spor_judet': 5 if model.brand_id.name == 'Volkswagen' else 5,
                'spor_judet_cu_remorca': 0 if model.brand_id.name == 'Volkswagen' else 10,
                'spor_alte': 0 if model.brand_id.name == 'Volkswagen' else 0,
                'spor_alte_cu_remorca': 0 if model.brand_id.name == 'Volkswagen' else 5,
                'spor_tractare_remorca1': 0 if model.brand_id.name == 'Volkswagen' else 32,
                })
        else:
            if current_km != vehicle.odometer:
                vehicle.write({'odometer': current_km})

    def create_driver_employee(self, driver_name):
        driver_id =  self.env['res.partner'].search([['name', '=', driver_name]], limit=1).id or self.env['res.partner'].create({'name': driver_name}).id
        employee_id = self.env['hr.employee'].search([['name', '=ilike', driver_name]], limit=1).id or self.env['hr.employee'].create({'name': driver_name}).id
        return driver_id

    def import_gps_alerts_alarme(self, data, carId):
        token = self.alarme_login()
        headers = {
          'Content-Type': 'application/json',
          'Token': token
        }

        yesterday = datetime.datetime.today() - datetime.timedelta(days=1)
        start_date_time = yesterday.strftime("%Y-%m-%dT00:00:00.000")
        end_date_time = yesterday.strftime("%Y-%m-%dT23:59:59.000")
        values = """{"startTime": """""+start_date_time+""",
            "endTime": """""+end_date_time+""",
            "carId": """+ str(carId) +"""
          }
        """
        url = "https://%s/SASFleetService/api/reports/events" % self.website
        response_body = requests.post(url, params={'api-version': '1.0'}, headers=headers, data=values)
        #print response_body.content
        self.initArray(data, ['fueled'])
        alert_prev = None
        fueled_alerts = []
        fuelLevel = 0
        fuelAdded = 0
        dist=0
        for alert in json.loads(response_body.content):
            time_on_road = parse_date(alert['date']) - parse_date(alert_prev['date']) if alert_prev else 0
            dist = dist + self.distance(alert['latitude'], alert['longitude'],alert_prev['latitude'], alert_prev['longitude']) if alert_prev else 0
#            print "fuelLevel=%s|fuelLevel_prev=%s|speed1=%s|speed2=%s|dist=%s|time_on_road=%s|event=%s" % (alert['fuelLevel'], fuelLevel, alert['speed'], alert_prev['speed'] if alert_prev else 0, dist, time_on_road, alert['triggerEvent'])
            fuel_dif = alert['fuelLevel'] - fuelLevel
            if alert['triggerEvent'] == 6 and fuelLevel < alert['fuelLevel'] and fuel_dif>10:
                fuelAdded = fuelAdded + alert['fuelLevel'] - fuelLevel
                fueled_alerts.append(alert)
                #print "fuelLevel_dif=%s|fuelAdded=%s|event=%s" % (fuel_dif,fuelAdded, alert['triggerEvent'])
            if alert['triggerEvent'] == 6:
                data['nr_porniri_opriri'] = data['nr_porniri_opriri'] + 1 if 'nr_porniri_opriri' in data else 1
            alert_prev = alert
            fuelLevel = alert['fuelLevel']
        print "carId=%s|Comb total=%s lit|De=%s ori|total dist=%s" % (carId, fuelAdded, len(fueled_alerts), dist)
        data['fueled'] = fuelAdded

    @api.model
    def import_gps_alarme(self, days_to_process=1):
        token = self.alarme_login()
        alarme_car_details = self.get_alarme_cars(token)

        headers = {
          'Content-Type': 'application/json',
          'Token': token
        }

        start_date = datetime.datetime.today() - datetime.timedelta(days=days_to_process)
        end_date = start_date + datetime.timedelta(days=1)

        for faz_date in self.daterange(start_date, end_date):
            for car in alarme_car_details.cars:
                start_date_time = faz_date.strftime("%Y-%m-%dT00:00:00.000")
                end_date_time = faz_date.strftime("%Y-%m-%dT23:59:59.000")
                values = """{"startTime": """""+start_date_time+""",
                    "endTime": """""+end_date_time+""",
                    "isClosedTimeInterval": false,
                    "carId": """+ str(car['carId']) +"""
                  }
                """
                #print values
                url = "https://%s/SASFleetService/api/reports/travelsheet" % self.website
                try:
                    response_body = requests.post(url, params={'api-version': '1.0'}, headers=headers, data=values)
                    payload = Payload(response_body.content)
                    print "%s|TotalKM=%s|WorkTime=%s|Idle=%s" % (payload.licensePlate, payload.totalDistance, payload.workTimeSpanInSeconds, payload.idleTimeSpanInSeconds)
                    data = {}
                    self.initArray(data, ['buc', 'mun', 'alte', 'D1', 'D2','D3','D4','D6', 'trasee', 'trasee_gps', 'timp_local', 'timp_inter', 'timp_inc_desc'])
                    for segment in payload.segments:
                        #print "index=%s, fuelLevel=%s, fueled=%s" % (segment['indexId'], segment['fuelLevel'], segment['fueled'])
                        self.collect_gps(data, parse_date(segment['dateStart']), parse_date(segment['dateEnd']), segment['addressStart'], segment['addressEnd'], segment['cityStart'], segment['cityEnd'],\
                         segment['countyStart'].replace(' (RO)', ''), segment['countyEnd'].replace(' (RO)', ''), self.toFloat(segment['distance']), segment['latitudeStart'], segment['latitudeEnd'], \
                         segment['longitudeStart'], segment['longitudeEnd'], segment['averageSpeed'])

                    self.import_gps_alerts_alarme(data, car['carId'])
                    local_time = sum(item for item in data['timp_local'])
                    inter_time = sum(item for item in data['timp_inter'])
                    timp_inc_desc = sum(item for item in data['timp_inc_desc'])
                    total_work_time = local_time + inter_time
                    self.write_faz(faz_date, data, payload.totalDistance, payload.licensePlate, local_time, inter_time, total_work_time, timp_inc_desc, data['nr_porniri_opriri'] if 'nr_porniri_opriri' in data else 0)

                except Exception:
                    #pass
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    #print "*** print_tb:"
                    #traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)
                    #print "*** print_exception:"
                    traceback.print_exception(exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout)
    @api.model
    def import_gps_fms(self, days_to_process=1):
        url = self.api_base_url + "GetVehicles.ashx"
        response_body = requests.post(url, params={'accessToken': self.api_key, 'format':'json'})
        cars = json.loads(response_body.content)

        start_date = datetime.datetime.today() - datetime.timedelta(days=days_to_process)
        end_date = start_date + datetime.timedelta(days=1)

        for faz_date in self.daterange(start_date, end_date):
            for car in cars:
                start_date_time = faz_date.strftime("%Y%m%d 00:00:00")
                end_date_time = faz_date.strftime("%Y%m%d 23:59:59")

                url = self.api_base_url + "GetVehicleTracks.ashx"
                try:
                    query_params = {'accessToken': self.api_key, 'format':'json',
                    'plateNumber': car['VehiclePlate'],
                    'startDateTime': start_date_time,
                    'endDateTime': end_date_time,
                    }
                    print "query_params=%s" % query_params
                    response_body = requests.post(url, params = query_params)

                    car_tracks = json.loads(response_body.text)
                    #print "car_tracks %s" % car_tracks
                    data = {}
                    self.initArray(data, ['buc', 'mun', 'alte', 'D1', 'D2','D3','D4','D6', 'trasee', 'trasee_gps', 'timp_local', 'timp_inter', 'timp_inc_desc'])
                    totalDistance = 0
                    for segment in car_tracks:
                        addressStart = [self.clean_diacritice(address.strip()) for address in segment['AddressStart'].split(',')]
                        addressStop = [self.clean_diacritice(address.strip()) for address in segment['AddressStop'].split(',')]
                        distance = self.toFloat(segment['DistanceMeters']) / 1000
                        totalDistance = totalDistance + distance
                        startDateTime = datetime.datetime.strptime(segment['StartDateTime'], '%Y-%m-%dT%H:%M:%S')
                        endDateTime = datetime.datetime.strptime(segment['EndDateTime'], '%Y-%m-%dT%H:%M:%S')
                        self.collect_gps(data, startDateTime, endDateTime, addressStart[0], addressStop[0], addressStart[1], addressStop[1], addressStart[2], addressStop[2], distance, segment['LatitudeStart'], segment['LatitudeStop'], segment['LongitudeStart'], segment['LongitudeStop'], None)

                    local_time = sum(item for item in data['timp_local'])
                    inter_time = sum(item for item in data['timp_inter'])
                    timp_inc_desc = sum(item for item in data['timp_inc_desc'])
                    total_work_time = local_time + inter_time
                    self.write_faz(faz_date, data, totalDistance, car['VehiclePlate'], local_time, inter_time, total_work_time, timp_inc_desc)
                except Exception:
                    #pass
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    #print "*** print_tb:"
                    #traceback.print_tb(exc_traceback, limit=4, file=sys.stdout)
                    #print "*** print_exception:"
                    traceback.print_exception(exc_type, exc_value, exc_traceback, limit=4, file=sys.stdout)

    def write_faz(self, faz_date, data, totalDistance, licensePlate, local_time=0, inter_time=0, total_work_time=0, timp_inc_desc=0, nr_porniri_opriri=0):
        #print sum(item.dist for item in data['mun']) + sum(item.dist for item in data['alte'])
        d1 = sum(item for item in data['D1'])
        d2 = sum(item for item in data['D2'])
        d6 = sum(item for item in data['D6'])
        d4 = sum(item for item in data['D4'])
        road_categories = [dist_cat for dist_cat in [{'name':'D1','total':d1},{'name':'D2','total':d2},{'name':'D4','total':d4},{'name':'D6','total':d6}] if dist_cat['total'] > 0]

        buc_km = sum(item.dist for item in data['buc'])
        mun_km = sum(item.dist for item in data['mun'])
        alte_km = sum(item.dist for item in data['alte'])

        print "local_time=%s|interurban=%s|WorkTime=%s|timp_inc_desc=%s|nr_porniri_opriri=%s" % (local_time, inter_time, total_work_time, timp_inc_desc, nr_porniri_opriri)
        vehicle = self.env['fleet.vehicle'].search([['license_plate', '=', licensePlate]], limit=1)
        if vehicle.id:
            foaie_de_parcurs = self.env['fleet_fpz.foaie_de_parcurs'].search([
            ['vehicle_id', '=', vehicle.id],
            ['date', '=', faz_date.strftime("%Y-%m-%d")]
            ], limit=1) or \
            self.env['fleet_fpz.foaie_de_parcurs'].create({
            'vehicle_id': vehicle.id,
            'date': faz_date.strftime("%Y-%m-%d"),
            'index_km_total': self.toFloat(totalDistance)
            })

            foaie_de_parcurs.write({
            'index_km_total': totalDistance,
            'road_categories': self.get_road_categories(road_categories),
            'trasee': self.get_trasee(data['trasee_gps']),
            'km_urbani_buc': buc_km,
            'km_urbani_judet': mun_km,
            'km_urbani_alte': alte_km,
            'km_urbani_buc_coef': vehicle.spor_buc,
            'km_urbani_judet_coef': vehicle.spor_judet,
            'km_urbani_alte_coef': vehicle.spor_alte,
            'nr_porniri_opriri': nr_porniri_opriri,
            'timp_local': self.sec_to_hours(local_time),
            'timp_inter': self.sec_to_hours(inter_time),
            'total_work_time': self.sec_to_hours(total_work_time),
            'timp_inc_desc': self.sec_to_hours(timp_inc_desc),
            'fuel_pump': data['fueled'] if 'fueled' in data else 0
            })

            print "found vehicle %s - %s" % (vehicle.name, foaie_de_parcurs.numar)
        else:
            print "not found vehicle %s" % (licensePlate)
    def get_road_categories(self, road_categories):
        road_category_ids = [(6, 0,  [self.env['fleet_fpz.parcurs_drum'].create({'km': cat['total'], 'categorie_drum_id': \
            self.env['fleet_fpz.categorie_drum'].search([['coeficient', '=', cat['name']]], limit=1).id}).id for cat in road_categories])]
        #print "get_road_categories=%s" % road_category_ids
        return road_category_ids

    def get_trasee(self, trasee):
        array_trasee = [self.env['fleet_fpz.parcurs_drum_traseu'].create(
            {'localitate_start': traseu['loc_start'],
            'localitate_stop': traseu['loc_stop'],
            'data_start': traseu['data_start'],
            'data_stop': traseu['data_stop'],
            'lat_start': traseu['lat_start'],
            'lon_start': traseu['lon_start'],
            'lat_stop': traseu['lat_stop'],
            'lon_stop': traseu['lon_stop'],
            'dist': traseu['dist'],
            'viteza': traseu['viteza'],
            }).id for traseu in trasee]
        print "array_trasee %s" % array_trasee
        trasee_ids = [(6, 0, array_trasee)]

        return trasee_ids

    def collect_gps(self, data, start_date, end_date, address_start, address_stop, city_start, city_stop, county_start, county_stop, dist, lat_start, lat_stop, lon_start, lon_stop, speed):
        self.collect_spor_urban(data, start_date, end_date,address_start, address_stop, city_start, city_stop, county_start, county_stop, dist, lat_start, lon_start)
        #calculate speed when distance > 1km

        if not speed and dist > 1:
            print "end_date=%s - start_date=%s = %s sec" % (end_date, start_date, (end_date - start_date).seconds)
            speed = dist / (float((end_date - start_date).seconds) / 3600)
            print "calculated speed = %s km/h" % (speed)
        print "address_start=%s address_stop=%s city_start=%s city_stop=%s|speed=%s|dist=%s|timp=%s" % (address_start, address_stop, city_start, city_stop,speed, dist,(end_date - start_date).seconds)
        if speed > 5:
            if speed < 25 and dist>10 and (city_start=='-' or city_start=='' or city_end=='-' or city_end==''):
                data['D4'].append(dist)
            elif (city_start != '-' or city_start != '') and (city_stop != '-' or city_stop != '')\
                and (address_start != '-' or address_start != '') and (address_stop != '-' or address_stop != ''):
                #oras/localitate
                data['D2'].append(dist)
            elif speed <= 15 and dist > 0 and dist < 50:
                data['D6'].append(dist)
            else:
                data['D1'].append(dist)

            duration = (end_date - start_date).seconds
            if city_start != city_stop:
                data['timp_inter'].append(duration)
            if 'last_city_stop_time' in data:
                data['timp_inc_desc'].append((start_date - data['last_city_stop_time']).seconds)
            if city_start == city_stop:
                data['timp_local'].append(duration)

            data['last_city_stop_time'] = end_date

            if dist>0:
                data['trasee_gps'].append({
                'loc_start': city_start,
                'loc_stop': city_stop,
                'data_start': start_date,
                'data_stop': end_date,
                'lat_start': lat_start,
                'lon_start': lon_start,
                'lat_stop': lat_stop,
                'lon_stop': lon_stop,
                'dist': dist,
                'viteza': speed
                })

    def collect_spor_urban(self, data, start_date, end_date, address_start, address_stop, city_start, city_stop, county_start, county_stop, dist, lat, lon):
        spor = SporCirculatieUrbana(start_date, end_date, address_start, address_stop, city_start, city_stop, county_start, county_stop, dist)
        if (city_start != '-' or city_start != '') and (city_stop != '-' or city_stop != ''):
            #aceasi adresa
            judet_oras = self.closest(self.judete_orase, {'lat': lat, 'lon': lon})
            #print "%s - [%s, %s]" % (county_start, judet_oras[0], judet_oras[1])
            if county_start in self.judete_orase or county_start.lower() == judet_oras[0].lower():
                #print "judet %s found in %s" % (county_start, judet_oras[0])
                if city_start in self.judete_orase[judet_oras[0]] or city_start.lower() == judet_oras[1].lower():
                    #print "%s found in %s" % (city_start, judet_oras[1])
                    if city_start == 'Bucuresti':
                        #bucuresti
                        data['buc'].append(spor)
                    else:
                        #orase municipii sau resedinta judet
                        data['mun'].append(spor)
                else:
                    #alte or
                    data['alte'].append(spor)
                    #print "oras %s not found in %s" % (city_start, judet_oras[1])
            else:
                #print "judet %s not found in %s" % (county_start, judet_oras[0])
                data['alte'].append(spor)

    def from_utc(self, date):
        utc = datetime.datetime.strptime(date, '%Y-%m-%dT%H:%M:%S')
        utc = utc.replace(tzinfo=self.from_zone)
        return utc.astimezone(self.to_zone)

    def clean_diacritice(self, text):
        return text.replace('ţ', 't').replace('ă', 'a').replace('ş','s').replace('â','a').replace('î','i')

    def flatten_json(self, y):
        out = {}
        def flatten(x, name=''):
            if type(x) is dict:
                for a in x:
                    flatten(x[a], name + a + '_')
            else:
                if name.endswith('latitudine_'):
                    if not name[:-12] in out:
                        out[name[:-12]] = {}
                    out[name[:-12]]['latitudine'] = x
                if name.endswith('longitudine_'):
                    if not name[:-13] in out:
                        out[name[:-13]] = {}
                    out[name[:-13]]['longitudine'] = x

        flatten(y)
        return out

    def distance(self, lat1, lon1, lat2, lon2):
        p = 0.017453292519943295
        a = 0.5 - cos((lat2-lat1)*p)/2 + cos(lat1*p)*cos(lat2*p) * (1-cos((lon2-lon1)*p)) / 2
        dist = 12742 * asin(sqrt(a))
        return dist

    def closest(self, data, v):
        data = self.flatten_json(data)
        mun_oras = min(data, key = lambda o: self.distance(v['lat'],v['lon'],data[o]['latitudine'],data[o]['longitudine']))
        return mun_oras.split('_')

    def toFloat(self, nr):
        try:
            return float(nr)
        except:
            return 0
    def sec_to_hours(self, seconds):
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        hours = float(h + (float(m) / 60))
        print "%s:%s = %s" % (h, m, hours)
        return hours
    def initArray(self, data, properties):
        for prop in properties:
            if not prop in data:
                data[prop] = []

    def daterange(self, start_date, end_date):
        for n in range(int ((end_date - start_date).days)):
            yield start_date + datetime.timedelta(n)

class Payload(object):
    def __init__(self, j):
        self.__dict__ = json.loads(j)

class SporCirculatieUrbana(object):
    def __init__(self, date_start, date_stop, address_start, address_stop, city_start, city_stop, county_start, county_stop, dist):
        self.address_start = address_start
        self.address_stop = address_stop
        self.city_start = city_start
        self.city_stop = city_stop
        self.county_start = county_start
        self.county_stop = county_stop
        self.dist = dist
        self.date_start = date_start
        self.date_stop = date_stop

    def __str__(self):
        return "%s,%s,%s,%s,%s,%s,%s" % (self.address_start, self.address_stop, self.city_start, self.city_stop, self.county_start, self.county_stop, self.dist)
    def __repr__(self):
        return self.__str__()
