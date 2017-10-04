# -*- coding: utf-8 -*-
from urllib2 import Request, urlopen
import requests, json, datetime
from dateutil import tz
import sys, traceback, unicodedata, re
from math import cos, asin, sqrt
from dateutil.parser import parse as parse_date

reload(sys)
sys.setdefaultencoding('utf-8')
class car_import(object):
    def __init__(self):
        self.website = 'www22.alarma.ro'
        self.username = 'frasinuldwn'
        self.password = '12345'

        self.api_key = "40789C4685884267B0265B6379F595D9"
        self.api_base_url = " https://fms.vodafone.ro/_layouts/15/S2/WebApi/StandardApi/";

        with open('judete_orase.json') as data_file:
            self.judete_orase = json.load(data_file)
        self.from_zone = tz.tzutc()
        self.to_zone = tz.tzlocal()

    def login(self):
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
    def get_alarme_cars(self):
        token = self.login()
        headers = {
          'Content-Type': 'application/json',
          'Token': token
        }
        url = "https://%s/SASFleetService/api/info" % self.website
        response_body = requests.get(url, params={'api-version': '1.0'}, headers=headers)
        payload = Payload(response_body.content)
        return payload.cars

    def import_gps_alerts_alarme(self, data, carId):
        token = self.login()
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

    def get_alarme_cars(self, token):
        headers = {
          'Content-Type': 'application/json',
          'Token': token
        }
        url = "https://%s/SASFleetService/api/info" % self.website
        response_body = requests.get(url, params={'api-version': '1.0'}, headers=headers)
        return Payload(response_body.content)

    def import_gps_alarme(self, days_to_process=1):
        token = self.login()
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
                    print "%s|TotalKM=%s|WorkTime=%s|Idle=%s|normedConsumptionPer100Km=%s" % (payload.licensePlate, payload.totalDistance, payload.workTimeSpanInSeconds, payload.idleTimeSpanInSeconds,payload.normedConsumptionPer100Km)
                    data = {}
                    self.initArray(data, ['buc', 'mun', 'alte', 'D1', 'D2','D3','D6', 'trasee', 'trasee_gps', 'timp_local', 'timp_inter', 'timp_inc_desc'])
                    for segment in payload.segments:
                        #print "index=%s, fuelLevel=%s, fueled=%s" % (segment['indexId'], segment['fuelLevel'], segment['fueled'])
                        self.collect_gps(data, self.from_utc(segment['dateStart']), self.from_utc(segment['dateEnd']), segment['addressStart'], segment['addressEnd'], segment['cityStart'], segment['cityEnd'],\
                         segment['countyStart'].replace(' (RO)', ''), segment['countyEnd'].replace(' (RO)', ''), self.toFloat(segment['distance']), segment['latitudeStart'], segment['latitudeEnd'], \
                         segment['longitudeStart'], segment['longitudeEnd'], segment['averageSpeed'])

                    self.import_gps_alerts_alarme(data, car['carId'])
                    local_time = sum(item for item in data['timp_local'])
                    inter_time = sum(item for item in data['timp_inter'])
                    total = (self.from_utc(payload.segments[0]['dateStart']) - self.from_utc(payload.segments[-1]['dateEnd'])).seconds
                    total_work_time = (local_time + inter_time)
                    timp_inc_desc = total - (local_time + inter_time)

                    print "local_time=%s|interurban=%s|WorkTime=%s|timp_inc_desc=%s|total=%s|start=%s->end=%s|nr_porniri_opriri=%s" % (local_time, inter_time, total_work_time, timp_inc_desc, total, payload.segments[0]['dateStart'], payload.segments[-1]['dateEnd'], data['nr_porniri_opriri'])
                except Exception:
                    #pass
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    #print "*** print_tb:"
                    #traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)
                    #print "*** print_exception:"
                    traceback.print_exception(exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout)

    def import_gps_fms(self, days_to_process=1):
        url = self.api_base_url + "GetVehicles.ashx"
        response_body = requests.post(url, params={'accessToken': self.api_key, 'format':'json'})
        cars = json.loads(response_body.content)

        start_date = datetime.datetime.today() - datetime.timedelta(days=days_to_process)
        end_date = start_date + datetime.timedelta(days=1)
        print "%s - %s" % (start_date, end_date)
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
                    car_tracks = json.loads(response_body.content)
                    #print "car_tracks %s" % car_tracks
                    data = {}
                    self.initArray(data, ['buc', 'mun', 'alte', 'D1', 'D2','D3','D6', 'trasee', 'trasee_gps', 'timp_local', 'timp_inter', 'timp_inc_desc'])
                    totalDistance = 0
                    for segment in car_tracks:
                        addressStart = [self.clean_diacritice(address.strip()) for address in segment['AddressStart'].split(',')]
                        addressStop = [self.clean_diacritice(address.strip()) for address in segment['AddressStop'].split(',')]
                        #print "%s-%s, %s-%s, %s-%s, %s" % (segment['StartDateTime'], segment['EndDateTime'], segment['LatitudeStart'], segment['LongitudeStart'], segment['LatitudeStop'], segment['LongitudeStop'], segment['DistanceMeters'])
                        #print "addressStart=%s %s %s" % (addressStart[0], addressStart[1], addressStart[2])
                        distance = self.toFloat(segment['DistanceMeters']) / 1000
                        totalDistance = totalDistance + distance
                        startDateTime = datetime.datetime.strptime(segment['StartDateTime'], '%Y-%m-%dT%H:%M:%S')
                        endDateTime = datetime.datetime.strptime(segment['EndDateTime'], '%Y-%m-%dT%H:%M:%S')

                        self.collect_gps(data,startDateTime, endDateTime, addressStart[0], addressStop[0],\
                         addressStart[1], addressStop[1], addressStart[2], \
                         addressStop[2], distance, segment['LatitudeStart'], segment['LatitudeStop'], segment['LongitudeStart'], segment['LongitudeStop'])
                        #print "%s-%s | %s-%s" % (segment['LatitudeStart'], segment['LongitudeStart'], segment['LatitudeStop'], segment['LongitudeStop'])
                        #print "%s - %s" % (distance, totalDistance)
                        #print "%s-%s, %s-%s, %s-%s, %s" % (segment['StartDateTime'], segment['EndDateTime'], segment['LatitudeStart'], segment['LongitudeStart'], segment['LatitudeStop'], segment['LongitudeStop'], segment['DistanceMeters'])
                        #print "addressStart=%s %s %s" % (addressStart[0], addressStart[1], addressStart[2])
                        #self.collect_gps(data, self.from_utc(segment['dateStart']), self.from_utc(segment['dateEnd']), segment['addressStart'], segment['addressEnd'], segment['cityStart'], segment['cityEnd'],\
                        # segment['countyStart'].replace(' (RO)', ''), segment['countyEnd'].replace(' (RO)', ''), self.toFloat(segment['distance']), segment['latitudeStart'], segment['latitudeEnd'], \
                        # segment['longitudeStart'], segment['longitudeEnd'], segment['averageSpeed'])
                    #print "data=%s" % (data)
                    #self.write_faz(faz_date, data, payload.totalDistance, payload.licensePlate)

                except Exception, e:
                    #pass
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    #print "*** print_tb:"
                    traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)
                    #print "*** print_exception:"
                    traceback.print_exception(exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout)
    def daterange(self, start_date, end_date):
        for n in range(int ((end_date - start_date).days)):
            yield start_date + datetime.timedelta(n)

    def collect_gps(self, data, start_date, end_date, address_start, address_stop, city_start, city_stop, county_start, county_stop, dist, lat_start, lat_stop, lon_start, lon_stop, speed=None):
        self.collect_spor_urban(data, start_date, end_date,address_start, address_stop, city_start, city_stop, county_start, county_stop, dist, lat_start, lon_start)
        #calculate speed when distance > 1km
        #print "speed=%s dist=%s" % (speed, dist)
        if not speed and dist > 1:
            #print "end_date=%s - start_date=%s = %s sec" % (end_date, start_date, (end_date - start_date).seconds)
            speed = dist / (float((end_date - start_date).seconds) / 3600)
            #print "calculated speed = %s km/h" % (speed)
        if (city_start != '-' or city_start != '') and (city_stop != '-' or city_stop != '')\
            and (address_start != '-' or address_start != '') and (address_stop != '-' or address_stop != ''):
            #oras/localitate
            data['D2'].append(dist)
        elif (city_start == '-' or city_start == '') and (city_stop == '-' or city_stop == ''):
            if speed <= 15:
                data['D6'].append(dist)
            else:
                data['D1'].append(dist)

        duration = (end_date - start_date).seconds
        if city_start != city_stop:
            data['timp_inter'].append(duration)
        if 'last_city_stop' in data and city_start != data['last_city_stop']:
            data['timp_inter'].append((start_date - data['last_city_stop_time']).seconds)
        if city_start == city_stop:
            data['timp_local'].append(duration)
        # if speed == 0:
        #     data['timp_inc_desc'].append(duration)

        data['last_city_stop'] = city_stop
        data['last_city_stop_time'] = end_date

        if  len(data['trasee']) == 0 and (city_start != '' or city_start != '-'):
            data['trasee'].append(city_start)
            data['trasee_gps'].append({'loc_start': city_start, 'loc_stop': city_stop, 'data_start': start_date, 'data_stop': end_date})
        elif data['trasee'][-1] != city_start and (city_start != '' or city_start != '-'):
            data['trasee'].append(city_start)
            data['trasee_gps'].append({'loc_start': city_start, 'loc_stop': city_stop, 'data_start': start_date, 'data_stop': end_date})


    def collect_spor_urban(self, data, start_date, end_date, address_start, address_stop, city_start, city_stop, county_start, county_stop, dist, lat, lon):
        spor = SporCirculatieUrbana(start_date, end_date, address_start, address_stop, city_start, city_stop, county_start, county_stop, dist)
        #print "spor=%s" % spor
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

    def toFloat(self, nr):
        try:
            return float(nr)
        except:
            return 0
    def initArray(self, data, properties):
        for prop in properties:
            if not prop in data:
                data[prop] = []

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

    def _compute_cn(self):
        record = Payload(json.dumps({
                'road_categories': [],
                'conditii_nefavorabile': False,
                'km_urbani_buc_coef': 5,
                'km_urbani_judet_coef': 5,
                'km_urbani_alte_coef': 5,
                'remorca1_id': False,
                'remorca2_id': False,
                'km_urbani_buc': 0,
                'km_urbani_judet': 150,
                'km_urbani_alte': 55,
                'kg': 40
                }))
        vehicle = Payload(json.dumps({
            'cm': 25,
            'spor_tractare_remorca1': 0
        }))
        record.road_categories = [Payload(json.dumps({'km_echivalent': 100}))]
        record.vehicle_id = vehicle
        #Coeficientul de corectie "A" are valoarea 1,1 si se aplica de regula in perioada 1 decembrie - 15 martie.
        a = 1.1 if record.conditii_nefavorabile else 1
        #self._compute_km_coef()
        #       Pe
        #Cn = ---- x Cmg x KG x A x Sb + Q [litri]
        #      100
        #Pe = Ped + T + U + I +/- Ra [km echivalenti]
        #Ped = Suma de la i=1 pina la 6 Pi x Di [km echivalenti]
        #     Pt
        #T = ---- x t [km echivalenti]
        #     100
        #     Pu
        #U = ---- x u [km echivalenti]
        #     100
        #I = np x i [km echivalenti]
        #      Pa
        #Ra = ---- x ra [km echivalenti]
        #     100
        #Cmg = a se calcula
        #              Cr
        #Sb = -----------------------
        #       Pe/100 x Cmv x KG x A
        #Sporul de consum combustibil pentru opriri si demarari repetate (Q1)
        #             Cm
        #Q1 = 0,25 x ------nod [litri]
        #            100
        #Sporul de consum combustibil pentru insotirea combinei (Q2)
        #Q2 = 0,1 x Cm x nc [litri]
        #Sporul de consum combustibil pentru actionarea instalatiilor speciale (Q3)
        #Q3 = np x qi [litri]
        #Sporul de consum combustibil pentru incalzirea motoarelor pe timp de iarna (Q4)
        #Q4 = 0,05 x Cm x ni [litri]
        #Sporul de consum combustibil pentru formarea rezervei de aer (Q5)
        #Q5 = 0,025 x Cm [litri]
        ped = sum(drum.km_echivalent for drum in record.road_categories)
        print "ped=%s" % ped
        t = 0 #Sporul pentru tractare (T)
        if record.remorca1_id:
            t = (record.remorca1_km / 100) * record.vehicle_id.spor_tractare_remorca1 if record.vehicle_id.spor_tractare_remorca1 else 0
        if record.remorca2_id:
            t = t + (record.remorca2_km / 100) * record.vehicle_id.spor_tractare_remorca2 if record.vehicle_id.spor_tractare_remorca2 else 0
        print "t=%s" % t
        u = (record.km_urbani_buc / 100) * record.km_urbani_buc_coef + \
        (record.km_urbani_judet / 100) * record.km_urbani_judet_coef + \
        (record.km_urbani_alte / 100) * record.km_urbani_alte_coef
        print "U=%s" % u
        pe = ped + t + u
        cm = record.vehicle_id.cm if record.vehicle_id.cm else self._compute_cm()

        #peste 1.5 tone
        consum = (pe / 100) * cm * record.kg/cm * a
        print consum
        #sub 1.5 tone
        consum = (pe / 100) * cm  * a
        print consum
        # cr = self._compute_cr()
        # sb = cr / consum if consum > 0 else 0
        # q = 0.025 * (cm /100) * record.nr_porniri_opriri if record.nr_porniri_opriri > 0 else 0
        # cn = consum * sb + q
        # print "consum nominal %s" % cn
        # record.consum_comb = cn
        # record.consum_comb_diference = (record.joja_ant_rezervor - record.joja_ant_rezervor) - cn

    def _compute_cm(self):
        return 1
    def _compute_cr(self):
        return 1
    def _compute_kg(self):
        return 1
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

car_import = car_import()

#car_import.import_gps_alarme(3052, 3)
car_import.import_gps_alarme()
#car_import.import_gps_fms('BN-37-FRS', '20170704 00:00:00', '20170704 23:59:59')
#car_import.import_gps_fms(10)
#car_import._compute_cn()
#data = "Bistriţa-năsăud, trada Gării Reghin Mureş".replace('ţ', 't').replace('ă', 'a').replace('ş','s').replace('â','a').replace('î','i')
#print data
#dist = 13
#end_date = datetime.datetime(2017,1,1,10,0,0)
#start_date = datetime.datetime(2017,1,1,9,30,0)
#print (float((end_date - start_date).seconds) / 3600)
#speed = dist / (float((end_date - start_date).seconds) / 3600)
#print "calculated speed = %s km/h" % (speed)
