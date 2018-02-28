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

def faults(apic, **kwargs):
	if 'filename' in kwargs:
		wb = kwargs['filename']
	else:
		wb = 'discovery.xlsx'
	if 'writer' in kwargs:
		writer = kwargs['writer']
	else:
		writer = utils.writer(wb)
	faultsUri = '/api/node/class/faultSummary.json?query-target-filter=' \
	    'and()&order-by=faultSummary.severity'
	faultsUrl = apic.baseUrl + faultsUri
	faultsResp = apic.session.get(faultsUrl, verify=False)
	utils.responseCheck(faultsResp)
	faultsJson = json.loads(faultsResp.text)
	data = []
	try:
		for fault in faultsJson['imdata']:
			data.append(fault['faultSummary']['attributes'])
	except:
		logging.critical('Error iterating through faults. Exiting')
		apic.session.close()
		sys.exit()
	apic.session.close()
	utils.dictDumpTwo(writer,
			        data,
			        list(data[0].keys()),
			        'faultSummary')

def main(**kwargs):
	apic = utils.apicSession()
	if not kwargs:
		faults(apic)
	else:
		faults(apic, **kwargs)


if __name__ == '__main__':
	main(**dict(arg.split('=') for arg in sys.argv[1:]))

