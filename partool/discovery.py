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
		self.dn = ''
		self.nameAlias = ''

	def __dict__(self):
		print('placeholder')

	def getVrfs(self):
		print('placeholder')

	def getBds(self):
		print('placeholder')

	def getEpgs(self):
		print('placeholder')


def tenants(apic):
	tnUri = '/api/class/fvTenant.json?rsp-prop-include=config-only'
	tnUrl = apic.baseUrl + tnUri
	tenantsResp = apic.session.get(tnUrl, verify=False)
	tenantsJson = json.loads(tenantsResp.text)
	return tenantsJson['imdata']

def bds(apic, **kwargs):
	'''
	'''
	if 'tenant' in kwargs:
		tnName = kwargs['tenant']
	else:
		tnName = ''
	bdUri = '/api/class/fvBD.json?' \
	    'query-target-filter=wcard(fvBD.dn,"{}")&rsp-prop-include=config-only'.format(tnName)
	bdUrl = apic.baseUrl + bdUri
	bdResponse = apic.session.get(bdUrl, verify=False)
	bdJson = json.loads(bdResponse.text)
	return bdJson['imdata']

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
	subnetUri = '/api/class/fvSubnet.json?query-target-filter=' \
		'wcard(fvSubnet.dn,"tn-{}/BD-{}/")'.format(tnName, bdName)
	subnetUrl = apic.baseUrl + subnetUri
	subnetResponse = apic.session.get(subnetUrl, verify=False)
	subnetJson = json.loads(subnetResponse.text)
	return subnetJson['imdata']

def ap(apic, **kwargs):
	if 'tenant' in kwargs:
		tnName = kwargs['tenant']
	else:
		tnName = ''
	apUri = '/api/class/fvAp.json?query-target-filter=wcard(fvAp.dn, '\
		'"tn-{}")'.format(tnName)
	apUrl = apic.baseUrl + apUri
	apResp = apic.session.get(apUrl, verify=False)
	apJson = json.loads(apResp.text)
	return apJson['imdata']

def epgs(apic, **kwargs):
	if 'tenant' in kwargs:
		tnName = kwargs['tenant']
	else:
		tnName = ''
	if 'ap' in kwargs:
		apName = kwargs['ap']
	else:
		apName = ''
	epgUri = '/api/class/fvAEPg.json?query-target-filter=wcard(fvAEPg.dn, '\
		'"tn-{}/ap-{}/")'.format(tnName, apName)
	epgUrl = apic.baseUrl + epgUri
	epgResp = apic.session.get(epgUrl, verify=False)
	epgJson = json.loads(epgResp.text)
	return epgJson['imdata']


def main(**kwargs):
	# Set Variables
	wb = 'discovery.xlsx'
	tnData = []
	tnCols = ['descr', 'dn', 'name', 'nameAlias', 'ownerKey','ownerTag']
	bdData = []
	bdCols = ['tenant',
			'bdName',
			'subnetIp',
			'subnetScope',
			'subnetPref',
			'subnetVirtual']
	epgData = []
	epgCols = ['tenant',
			'app',
			'epg',
			'bdTenant',
			'bd']

	# Create login session to APIC
	apic = utils.apicSession()

	# Get the current tenants
	tenantsResp = tenants(apic)

	'''
	 Loop through tenants and collect additional information. Including:
	 	1) BDs
	 		a) Subnets within BDs
	 	2) EPGs
	 		a) EPG Details
	 		b) Related Domains
	 		c) Related BD
	 		d) Related Consumed Contracts
	 		e) Related Provided Contracts
	'''
	for tenant in tenantsResp:
		tnData.append(tenant['fvTenant']['attributes'])
		bdResp = bds(apic,tenant=tenant['fvTenant']['attributes']['name'])
		for bd in bdResp:
			subnetResp = subnet(apic,
								bd=bd['fvBD']['attributes']['name'],
								tenant=tenant['fvTenant']['attributes']['name'])
			if not subnetResp:
				bdData.append((
					tenant['fvTenant']['attributes']['name'],
					bd['fvBD']['attributes']['name'],
					'Null',
					'Null',
					'Null',
					'Null'))
			else:
				for sub in subnetResp:
					bdData.append((
						tenant['fvTenant']['attributes']['name'],
						bd['fvBD']['attributes']['name'],
						sub['fvSubnet']['attributes']['ip'],
						sub['fvSubnet']['attributes']['scope'],
						sub['fvSubnet']['attributes']['preferred'],
						sub['fvSubnet']['attributes']['virtual']))
			apResp = ap(apic, tenant=tenant['fvTenant']['attributes']['name'])
			if not apResp:
				logging.info('No App Profiles Found in Tenant {}'.format(tenant['fvTenant']['attributes']['name']))
			else:
				for app in apResp:
					epgResp = epgs(apic,
								tenant=tenant['fvTenant']['attributes']['name'],
								ap=app['fvAp']['attributes']['name'])
					if not epgResp:
						logging.info('No EPGs found in App Profile {}'.format(app['fvAp']['attributes']['name']))
					else:
						for epg in epgResp:
							epgData.append((
								tenant['fvTenant']['attributes']['name'],
								app['fvAp']['attributes']['name'],
								epg['fvAEPg']['attributes']['name'],
								epg['fvAEPg']['attributes']['nameAlias'],
								epg['fvAEPg']['attributes']['prefGrMemb'],
								epg['fvAEPg']['attributes']['pcTag']
								)
							)
	for aepG in epgData:
		logging.info(aepG)
	writer = utils.writer(wb)
	utils.dictDumpTwo(writer, tnData, tnCols, 'fvTenant')
	utils.dictDumpTwo(writer, bdData, bdCols, 'fvBD')
	apic.session.close()

if __name__ == '__main__':
	main(**dict(arg.split('=') for arg in sys.argv[1:]))
