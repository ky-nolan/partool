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

class tenant(object):
	'''
	Object that represents a Tenant Object and includes functions to retrieve lists
	of child

	Attributes:
	name: A string representing the Tenant's name
	'''
	def __init__(self, name):
		'''
		Return a Tenant object whose name is *name* 
		'''
		self.name = name

	def __dict__(self):
		print('placeholder')

	def getVrfs(self):
		print('placeholder')

	def getBds(self):
		print('placeholder')

	def getEpgs(self):
		print('placeholder')


def tenants(apic):
	tnUri = '/api/class/fvTenant.json'
	tnUrl = apic.baseUrl + tnUri
	tenantsResponse = apic.session.get(tnUrl, verify=False)
	tenantsJson = json.loads(tenantsResponse.text)
	return tenantsJson

def bds(apic, **kwargs):
	'''
	'''
	if 'tenant' in kwargs:
		tnName = kwargs['tenant']
	else:
		tnName = ''
	bdUri = '/api/class/fvBD.json?' \
	    'query-target-filter=wcard(fvBD.dn,"{}")'.format(tnName)
	bdUrl = apic.baseUrl + bdUri
	bdResponse = apic.session.get(bdUrl, verify=False)
	bdJson = json.loads(bdResponse.text)
	return bdJson

def subnet(apic, **kwargs):
	'''
	'''
	if 'bd' in kwargs:
		bdName = kwargs['bd']
	else:
		bdName = ''
	if 'tenant' in kwargs:
		tnName = kwargs['tenant']
	else:
		tnName = ''
	subnetUri = '/api/mo/uni/tn-{}/BD-{}.json?' \
	    'rsp-subtree=children&rsp-subtree-filter' \
	    '=eq(fvSubnet)'.format(tnName, bdName)
	subnetUrl = apic.baseUrl + subnetUri
	subnetResponse = apic.session.get(subnetUrl, verify=False)
	subnetJson = json.loads(subnetResponse.text)
	return subnetJson

def main(**kwargs):
	wb = 'discovery.xlsx'
	apic = utils.apicSession()
	tenantsResponse = tenants(apic)
	apic.session.close()
	logging.info('Printing Tenants')
	for tenant in tenantsResponse['imdata']:
		logging.info(tenant['fvTenant']['attributes']['name'])
		bdJson = bds(
		    apic,
		    tenant=tenant['fvTenant']['attributes']['name'])
		[logging.info(' ->' + bd['fvBD']['attributes']['name']) for bd in bdJson['imdata']]


if __name__ == '__main__':
	main(**dict(arg.split('=') for arg in sys.argv[1:]))
