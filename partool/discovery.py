import coloredlogs
import json
import logging
import requests
import utils
import sys
from faults import faults


requests.packages.urllib3.disable_warnings()
coloredlogs.install()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get(apic, url):
	resp = apic.session.get(url, verify=False)
	utils.responseCheck(resp)
	respJson = json.loads(resp.text)
	data = []
	for item in respJson['imdata']:
		data.append(item)
	return data

def getIntfP(apic, baseUrl):
	intfProfUri = '/api/class/infraAccPortP.json'
	nodePUri = '/api/class/infraNodeP.json'
	intfProfUrl = baseUrl + intfProfUri
	intfProfResp = apic.session.get(intfProfUrl, verify=False)
	utils.responseCheck(intfProfResp)
	intfProfJson = json.loads(intfProfResp.text)
	return intfProfJson

def writeIntfP(apic, writer, wb):
	intfProfs = getIntfP(apic, apic.baseUrl)
	data = {}
	columnNames = ['name', 'dn']
	for intfProf in intfProfs['imdata']:
		name = intfProf['infraAccPortP']['attributes']['name']
		dn = intfProf['infraAccPortP']['attributes']['dn']
		data[name] = dn
	utils.dictDumpTwo(writer, list(data.items()), columnNames, 'interfaceProfiles')
	return logging.info('Interface Profiles written to {}'.format(wb))

def getAccPortGrp(apic, baseUrl):
	accPortGrpUri = '/api/node/class/infraAccPortGrp.json'
	accPortGrpUrl = baseUrl + accPortGrpUri
	accPortGrpResp = apic.session.get(accPortGrpUrl, verify=False)
	utils.responseCheck(accPortGrpResp)
	accPortGrpJson = json.loads(accPortGrpResp.text)
	return accPortGrpJson

def getAccBndlGrp(apic, baseUrl):
	accBndlGrpUri = '/api/node/class/infraAccBndlGrp.json'
	accBndlGrpUrl = baseUrl + accBndlGrpUri
	accBndlGrpResp = apic.session.get(accBndlGrpUrl, verify=False)
	utils.responseCheck(accBndlGrpResp)
	accBndlGrpJson = json.loads(accBndlGrpResp.text)
	return accBndlGrpJson

def writePolGrps(apic, writer, wb):
	# Discrete Port Policy Groups
	accPortGrpResp = getAccPortGrp(apic, apic.baseUrl)
	data = []
	columnNames = ['name', 'dn', 'type']
	for accPortGrp in accPortGrpResp['imdata']:
		name = accPortGrp['infraAccPortGrp']['attributes']['name']
		dn = accPortGrp['infraAccPortGrp']['attributes']['dn']
		type = 'access'
		data.append([name, dn, type])
	# Port-channel or vPC Policy Groups
	accBndlGrpResp = getAccBndlGrp(apic, apic.baseUrl)
	for accBndlGrp in accBndlGrpResp['imdata']:
		name = accBndlGrp['infraAccBndlGrp']['attributes']['name']
		dn = accBndlGrp['infraAccBndlGrp']['attributes']['dn']
		if accBndlGrp['infraAccBndlGrp']['attributes']['lagT'] == 'link':
			type = 'port-channel'
		elif accBndlGrp['infraAccBndlGrp']['attributes']['lagT'] == 'node':
			type = 'vpc'
		data.append([name, dn, type])
	utils.dictDumpTwo(writer, data, columnNames, 'intfPolGrps')
	return logging.info('Interface Policy Groups written to {}'.format(wb))

def main(**kwargs):
	'''
	'''
	logging.info(kwargs)
	apic = utils.apicSession()
	if 'filename' in kwargs:
		wb = kwargs['filename']
	else:
		wb = 'discovery.xlsx'
	writer = utils.writer(wb)
	
	
	# Get and populated Leaf Interface Policy Groups
	writePolGrps(apic, writer, wb)
	
	# Get and populated Leaf Interface Profiles
	writeIntfP(apic, writer, wb)
	
	# Get and populate Leaf Node Profiles
	nodeData = {}
	nodeProfs = get(apic, apic.baseUrl + '/api/node/class/infraNodeP.json?' \
	                'rsp-prop-include=config-only')
	for nodeProf in nodeProfs:
		get(apic, apic.baseUrl + '/api/node/class/infraNodeP.json?')
		# Get interface profiles related to Leaf Node Profile
		rsAccPortPUri = '/api/node/mo/uni/infra/nprof-{}.json?' \
		    'query-target=children&target-subtree-class=infraRsAccPortP' \
		    '&rsp-prop-include=config-only'.format(nodeProf['infraNodeP']['attributes']['name'])
		resp = get(apic, apic.baseUrl + rsAccPortPUri)
		x = 1
		for obj in resp:
			nodeProf['infraNodeP']['attributes']['rsAccPortP' + str(x)] = obj['infraRsAccPortP']['attributes']['tDn']
			x+=1
	utils.dictDumpTwo(writer,
	                  list(nodeProf['infraNodeP']['attributes'] for nodeProf in nodeProfs),
	                  list(nodeProfs[0]['infraNodeP']['attributes'].keys()),
	                'nodeProfiles')
	
	# Get and populated Fabric Nodes
	fabNodes = get(apic, apic.baseUrl + '/api/node/class/fabricNode.json')
	utils.dictDumpTwo(writer,
	                list(fabNode['fabricNode']['attributes'] for fabNode in fabNodes),
	                list(fabNodes[0]['fabricNode']['attributes'].keys()),
	                'fabricNodes')
	
	# Get open faults and populate faults worksheet
	faultsResp = faults(apic)
	faultsData = []
	for fault in faultsResp['imdata']:
		faultsData.append(fault['faultSummary']['attributes'])
	utils.dictDumpTwo(writer,
	                  faultsData,
	                    list(faultsData[0].keys()),
	                    'faults')
	
	
	apic.session.close()

if __name__ == '__main__':
	main(**dict(arg.split('=') for arg in sys.argv[1:]))
