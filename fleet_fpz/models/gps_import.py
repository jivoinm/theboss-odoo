import logging
from odoo import models, fields, api
_logger = logging.getLogger(__name__)


class alarme_data_import(models.AbstractModel):
    _name = "fleet_fpz.alarme_data_import"

    @api.model
    def toFloat(nr):
        try:
            return float(nr)
        except:
            return 0
    @api.model
    def initArray(data_nr, properties):
        for prop in properties:
            if not prop in data[nr]:
                data[nr][prop] = []

    @api.model
    def addDistance(nr, address, city, county, dist, lat, lon):
        initArray(data[nr], ['buc', 'mun', 'alte', 'D1', 'D2','D3','D6'])
        if dist > 0:
            calc_dist = dist - history[nr] if nr in history and history[nr] > dist else dist
            if address != '-' and city == 'Bucuresti' and county == 'Bucuresti (RO)':
                data[nr]['buc'].append(calc_dist)
            if county != 'Bucuresti (RO)':
                if address == '-' and city == '-':
                    data[nr]['mun'].append(calc_dist)
                    if speed <= 15 * 1.85200:
                        data[nr]['D6'].append(calc_dist)
                    else:
                        data[nr]['D3'].append(calc_dist)
                elif address != '-' and city == '-':
                    data[nr]['mun'].append(calc_dist)
                    if speed >= 60 * 1.85200:
                        data[nr]['D1'].append(calc_dist)
                    else:
                        data[nr]['D2'].append(calc_dist)
                else:
                    data[nr]['alte'].append(calc_dist)
                    data[nr]['D3'].append(calc_dist)

            history[nr] = dist
            if 'lat' in data[nr] and 'lon' in data[nr]:
                calculated_speed = 0
                km_between_points = haversine(data[nr]['lat'], data[nr]['lon'], lat, lon)
                if 'end_date' in data[nr]:
                    time_between_points = date - data[nr]['end_date']
                    dist_meeters_per_sec = km_between_points * 1000 / time_between_points.seconds
                    calculated_speed = dist_meeters_per_sec * 18 / 5

                #print "speed:%s - calculated_speed:%s" % (toFloat(speed) * 1.85200, calculated_speed)

    @api.model
    def haversine(lon1, lat1, lon2, lat2):
        """
        Calculate the great circle distance between two points
        on the earth (specified in decimal degrees)
        """
        # convert decimal degrees to radians
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        # haversine formula
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        km = 6367 * c
        return km

    @api.model
    def load_data_line(self, start_date, end_date):
        _logger.info('load data started...')
        with open('gps.report.csv') as f:
            for line in f:
                line = line.strip()
                line = line.split(",")

                if len(line) >=21:
                    #nr = line[1].replace(" ", "")
                    nr = line[1]
                    driver = line[2]
                    utc = datetime.strptime(line[3], '%Y-%m-%d %H:%M:%S.000')
                    utc = utc.replace(tzinfo=from_zone)
                    date = utc.astimezone(to_zone)
                    fake = line[4]
                    lat = toFloat(line[5])
                    lon = toFloat(line[6])
                    speed = line[7]
                    course = line[8]
                    event = line[9]
                    address = line[10]
                    city = line[11]
                    county = line[12]
                    location = line[13]
                    distance = toFloat(line[14])
                    fuel_used = toFloat(line[15])
                    fuel_level = toFloat(line[16])
                    if 'False' == fake:
                        if not nr in data:
                            data[nr] = {}
                        addDistance(nr, address, city, county, distance, lat, lon)
                        #calc_cat(nr, distance, lat, lon, speed, date)
                        if not 'start_date' in data[nr]:
                            data[nr]['start_date'] = date
                        data[nr]['end_date'] = date
                        data[nr]['lat'] = lat
                        data[nr]['lon'] = lon
        data_calc = {}
        for item in data.keys():
            data_calc[item] = {}
            data_calc[item]['start_date'] = data[item]['start_date'].strftime("%Y-%m-%d %H:%M:%S")
            data_calc[item]['end_date'] = data[item]['end_date'].strftime("%Y-%m-%d %H:%M:%S")
            data_calc[item]['buc'] = sum(data[item]['buc'])
            data_calc[item]['mun'] = sum(data[item]['mun'])
            data_calc[item]['alte'] = sum(data[item]['alte'])
            data_calc[item]['D1'] = sum(data[item]['D1'])
            data_calc[item]['D2'] = sum(data[item]['D2'])
            data_calc[item]['D3'] = sum(data[item]['D3'])
            data_calc[item]['D6'] = sum(data[item]['D6'])

    def load_data(self, nr, driver, data, lat, lon, speed, course, event, address, city, county, poi_location, distance, fuel_used, fuel):
        pass
