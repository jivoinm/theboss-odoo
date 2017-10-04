from urllib2 import Request, urlopen
import requests, json

class alarme_car_import(object):
    def __init__(self):
        self.website = 'www22.alarma.ro'
        self.username = 'frasinuldwn'
        self.password = '12345'

    def import_cars(self):
        token = self.login()
        headers = {
          'Content-Type': 'application/json',
          'Token': token
        }
        url = "https://%s/SASFleetService/api/info" % self.website
        response_body = requests.get(url, params={'api-version': '1.0'}, headers=headers)
        payload = Payload(response_body.content)
        for company in payload.companies:
            print company['companyId']

        for car in payload.cars:
            br = [branch['name'] for branch in payload.branches if branch['branchId'] == car['branchId']]
            wp = [workpoint['name'] for workpoint in payload.workPoints if workpoint['branchId'] == car['branchId'] and workpoint['workPointId'] == car['workPointId']]
            print "carId:%s, plate:%s, branch:%s, workpoint:%s" % (car['carId'], car['licensePlate'], br[0], wp[0])



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

    def load_website(self):
        requst = Request('https://sasfleetlogin.alarma.ro/LoginService.svc/webServers/'+ self.username)

class fms_vodafone(object):
    _name = "fleet_fpz.fms_vodafone_car_import"
    api_key = "40789C4685884267B0265B6379F595D9"
    api_base_url = " https://fms.vodafone.ro/_layouts/15/S2/WebApi/StandardApi/";

    def import_cars(self):
        url = self.api_base_url + "GetVehicles.ashx"
        response_body = requests.post(url, params={'accessToken': self.api_key, 'format':'json'})

        cars = json.loads(response_body.content)
        for car in cars:
            print car['Category']


class Payload(object):
    def __init__(self, j):
        self.__dict__ = json.loads(j)


#alarme = alarme_car_import()
#alarme.import_cars()
fms = fms_vodafone()
fms.import_cars()
