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


def tenants(apicSession, baseUrl):
	tnUri = '/api/class/fvTenant.json'
	tnUrl = baseUrl + tnUri
	tenantsResponse = apicSession.get(tnUrl, verify=False)
	tenantsJson = json.loads(tenantsResponse.text)
	return tenantsJson

def bds(apicSession, baseUrl, **kwargs):
	'''
	'''
	if 'tenant' in kwargs:
		tnName = kwargs['tenant']
	else:
		tnName = ''
	bdUri = '/api/class/fvBD.json?' \
	    'query-target-filter=wcard(fvBD.dn,"{}")'.format(tnName)
	bdUrl = baseUrl + bdUri
	bdResponse = apicSession.get(bdUrl, verify=False)
	bdJson = json.loads(bdResponse.text)
	return bdJson

def subnet(apicSession, baseUrl, **kwargs):
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
	subnetUrl = baseUrl + subnetUri
	subnetResponse = apicSession.get(subnetUrl, verify=False)
	subnetJson = json.loads(subnetResponse.text)
	return subnetJson

def main(**kwargs):
	wb = 'discovery.xlsx'
	apicSession, baseUrl = utils.login()
	tenantsResponse = tenants(apicSession, baseUrl)
	apicSession.close()
	logging.info('Printing Tenants')
	for tenant in tenantsResponse['imdata']:
		logging.info(tenant['fvTenant']['attributes']['name'])
		bdsTxt = bds(
		    apicSession,
		    baseUrl,
		    tenant=tenant['fvTenant']['attributes']['name'])
		[logging.info(' ->' + bd['fvBD']['attributes']['name']) for bd in bdsTxt['imdata']]


if __name__ == '__main__':
	main(**dict(arg.split('=') for arg in sys.argv[1:]))
