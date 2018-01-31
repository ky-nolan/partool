import coloredlogs
import json
import logging
import requests
import utils
import sys

requests.packages.urllib3.disable_warnings()
coloredlogs.install()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def faults(apic, baseUrl):
	faultsUri = '/api/node/class/faultSummary.json?query-target-filter=' \
	    'and()&order-by=faultSummary.severity'
	faultsUrl = baseUrl + faultsUri
	faultsResponse = apic.session.get(faultsUrl, verify=False)
	utils.responseCheck(faultsResponse)
	faultsJson = json.loads(faultsResponse.text)
	return faultsJson

def main(**kwargs):
	'''
	apicSession, baseUrl = utils.login()
	if 'filename' in kwargs:
		wb = kwargs['filename']
	else:
		wb = 'discovery.xlsx'
	faultsResponse = faults(apicSession, baseUrl)
	data = []
	for fault in faultsResponse['imdata']:
	data.append(fault['faultSummary']['attributes'])
	utils.dictDump(data, wb, 'faults')
	apicSession.close()
	'''
	apic = utils.apicSession()
	if 'filename' in kwargs:
		wb = kwargs['filename']
	else:
		wb = 'discovery.xlsx'
	faultsResponse = faults(apic, apic.baseUrl)
	data = []
	for fault in faultsResponse['imdata']:
		data.append(fault['faultSummary']['attributes'])
	writer = utils.writer(wb)
	utils.dictDump(data, 'faults')
	apic.session.close()	

if __name__ == '__main__':
	main(**dict(arg.split('=') for arg in sys.argv[1:]))
19581287
