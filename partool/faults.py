#!/Users/barsubus/_dev/rest-totoro/venv3.6/bin python
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

def faults(apicSession, baseUrl):
	faultsUri = '/api/node/class/faultSummary.json?query-target-filter=' \
	    'and()&order-by=faultSummary.severity'
	faultsUrl = baseUrl + faultsUri
	faultsResponse = apicSession.get(faultsUrl, verify=False)
	faultsJson = json.loads(faultsResponse.text)
	return faultsJson

def main(**kwargs):
	apicSession, baseUrl = utils.login()
	if 'filename' in kwargs:
		wb = kwargs['filename']
	else:
		wb = 'discovery.xlsx'
	faultsResponse = faults(apicSession, baseUrl)
	data = []
	logging.info(wb)
	for fault in faultsResponse['imdata']:
		data.append(fault['faultSummary']['attributes'])
	utils.dictDump(data, wb, 'faults')
	apicSession.close()

if __name__ == '__main__':
	main(**dict(arg.split('=') for arg in sys.argv[1:]))
