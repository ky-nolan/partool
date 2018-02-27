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

def dhcpClient(apic):
	dhcpClientUri = '/api/node/class/dhcpClient.json'
	dhcpClientUrl = apic.baseUrl + dhcpClientUri
	dhcpClientResp = apic.session.get(dhcpClientUrl, verify=False)
	dhcpClientJson = json.loads(dhcpClientResp.text)
	return dhcpClientJson['imdata']

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

def fvRsBd(apic, **kwargs):
	try:
		rsBdUri = '/api/node/mo/uni/tn-{}/ap-{}/epg-{}.json?' \
			'query-target=children&' \
			'target-subtree-class=fvRsBd'.format(kwargs['tenant'],
												kwargs['app'],
												kwargs['epg'])
		rsBdUrl = apic.baseUrl + rsBdUri
		rsBdResp = apic.session.get(rsBdUrl, verify=False)
		rsBdJson = json.loads(rsBdResp.text)
		return rsBdJson['imdata']
	except KeyError:
		logging.critical('Invalid or incomplete kwargs passed to fvRsBd')
		logging.critical('Must pass tenant, app, and epg keyword arguments')
		logging.critical('Exiting!')
		sys.exit()
	except Exception as ex:
		utils.exceptTempl(ex)

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
			'nameAlias',
			'bd',
			'bdTenant',
			'prefGroupMember',
			'pcTag']
	dhcpData = []
	dhcpCols = ['podId',
				'fabricId',
				'nodeId',
				'model',
				'name',
				'nameAlias',
				'configNodeRole',
				'nodeRole',
				'nodeType',
				'ip',
				'spineLevel',
				'fwVer',
				'runningVer',
				'supported',
				'extPoolId',
				'decommissioned',
				'configIssues'
	]

	# Create login session to APIC
	apic = utils.apicSession()

	# Get Fabric Info
	dhcpClientData = dhcpClient(apic)
	for node in dhcpClientData:
		dhcpData.append((
				node['dhcpClient']['attributes']['podId'],
				node['dhcpClient']['attributes']['fabricId'],
				node['dhcpClient']['attributes']['nodeId'],
				node['dhcpClient']['attributes']['model'],
				node['dhcpClient']['attributes']['name'],
				node['dhcpClient']['attributes']['nameAlias'],
				node['dhcpClient']['attributes']['configNodeRole'],
				node['dhcpClient']['attributes']['nodeRole'],
				node['dhcpClient']['attributes']['nodeType'],
				node['dhcpClient']['attributes']['ip'],
				node['dhcpClient']['attributes']['spineLevel'],
				node['dhcpClient']['attributes']['fwVer'],
				node['dhcpClient']['attributes']['runningVer'],
				node['dhcpClient']['attributes']['supported'],
				node['dhcpClient']['attributes']['extPoolId'],
				node['dhcpClient']['attributes']['decomissioned'],
				node['dhcpClient']['attributes']['configIssues']
			)
		)

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
							rsBd = fvRsBd(apic,
							tenant=tenant['fvTenant']['attributes']['name'],
							app=app['fvAp']['attributes']['name'],
							epg=epg['fvAEPg']['attributes']['name']
							)
							if not rsBd:
								epgData.append((
									tenant['fvTenant']['attributes']['name'],
									app['fvAp']['attributes']['name'],
									epg['fvAEPg']['attributes']['name'],
									epg['fvAEPg']['attributes']['nameAlias'],
									'',
									'',
									epg['fvAEPg']['attributes']['prefGrMemb'],
									epg['fvAEPg']['attributes']['pcTag']
									)
								)
							else:
								epgData.append((
									tenant['fvTenant']['attributes']['name'],
									app['fvAp']['attributes']['name'],
									epg['fvAEPg']['attributes']['name'],
									epg['fvAEPg']['attributes']['nameAlias'],
									rsBd[0]['fvRsBd']['attributes']['tnFvBDName'],
									rsBd[0]['fvRsBd']['attributes']['dn'].split('tn-')[1].split('/')[0],
									epg['fvAEPg']['attributes']['prefGrMemb'],
									epg['fvAEPg']['attributes']['pcTag']
									)
								)
	writer = utils.writer(wb)
	try:
		faults(writer=writer)
		utils.dictDumpTwo(writer, dhcpData, dhcpCols, 'dhcpClient')
		utils.dictDumpTwo(writer, tnData, tnCols, 'fvTenant')
		utils.dictDumpTwo(writer, bdData, bdCols, 'fvBD')
		utils.dictDumpTwo(writer, epgData, epgCols, 'fvAEPg')
		apic.session.close()
	except AssertionError:
		raise AssertionError
	except Exception as ex:
		utils.exceptTempl(ex)


if __name__ == '__main__':
	main(**dict(arg.split('=') for arg in sys.argv[1:]))
