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
	data = json.loads(resp.text)
	return data['imdata']

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
	dhcpClientData = get(apic, apic.baseUrl + '/api/node/class/dhcpClient.json')
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
	tenantsResp = get(apic, apic.baseUrl + '/api/class/fvTenant.json?rsp-prop-include=config-only')

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
		bdResp = get(apic, apic.baseUrl + '/api/class/fvBD.json?' \
	    	'query-target-filter=wcard(fvBD.dn,"{}")&rsp-prop-' \
	    	'include=config-only'.format(tenant['fvTenant']['attributes']['name']))
		for bd in bdResp:
			subnetResp = get(apic,
				apic.baseUrl + '/api/class/fvSubnet.json?query-target-filter=' \
				'wcard(fvSubnet.dn,"tn-{}/BD-{}/")'.format(tenant['fvTenant']['attributes']['name'], 
				bd['fvBD']['attributes']['name']))
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
			apResp = get(apic, apic.baseUrl + '/api/class/fvAp.json?query-target-filter=wcard(fvAp.dn,' \
				'"tn-{}")'.format(tenant['fvTenant']['attributes']['name']))
			if not apResp:
				logging.info('No ANP in Tn {}}'.format(tenant['fvTenant']['attributes']['name']))
			else:
				for app in apResp:
					epgResp = get(apic,
								apic.baseUrl + '/api/class/fvAEPg.json?' \
								'query-target-filter=wcard(fvAEPg.dn, '  \
								'"tn-{}/ap-{}/")'.format(tenant['fvTenant']['attributes']['name'],
									app['fvAp']['attributes']['name']))
					if not epgResp:
						logging.info('No EPGs found in App Profile {}'.format(app['fvAp']['attributes']['name']))
					else:
						for epg in epgResp:
							rsBd = get(apic,
								apic.baseUrl + '/api/node/mo/uni/tn-{}/ap-{}/epg-{}.json?' \
									'query-target=children&target-subtree-class=fvRsBd'.format(
										tenant['fvTenant']['attributes']['name'],
										app['fvAp']['attributes']['name'],
										epg['fvAEPg']['attributes']['name']))
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
		faults(apic, writer=writer)
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
