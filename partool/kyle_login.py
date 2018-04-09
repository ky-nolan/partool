import requests
import json
import logging
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
logging.basicConfig(level=logging.CRITICAL, format='%(asctime)s - %(levelname)s - %(message)s')

class credentials:
    def __init__(self,ip,user,password,session):
        self.ip = ip
        self.password = password
        self.username = user
        self.session = session
        self.error = "None"


def login(apicIp, usr, pw):
    jsonData = '{"aaaUser" : {"attributes" : {"name" : "' + usr + '","pwd" : "' + pw + '"}}}'
    s = requests.Session()
    account = credentials(apicIp, usr, pw, s)
    loginUrl = "https://"+apicIp+"/api/aaaLogin.json"
    r = s.post(loginUrl, data=jsonData, verify=False)
    try:
        json.loads(r.content)['imdata'][0]['error']['attributes']['code']
        account.error = json.loads(r.content)['imdata'][0]
        logging.error('ERROR on: '+apicIp, json.loads(r.content)['imdata'][0])
    except:
        logging.info('Logged into: '+apicIp)
    return account


#
# def main():
#     s = login('10.224.97.51', 'admin', 'cisco123').session
#     r = s.get('https://10.224.97.51/api/node/class/faultSummary.json?')
#     logging.debug(r.content)
