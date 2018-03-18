#!/usr/bin/env python3

import coloredlogs
import json
import logging
import requests
import utils
import sys
import time
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
			'query-target=children&target-subtree-class=fvRs' \
		    'Bd'.format(kwargs['tenant'],
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
	date = time.strftime("%Y%m%d")
	if 'filename' in kwargs:
		wb = date + '-' + kwargs['filename']
	else:

		wb = date + '-discovery.xlsx'
	tnData = []
	tnCols = ['descr', 'dn', 'name', 'nameAlias', 'ownerKey','ownerTag']
	bdData = []
	bdCols = ['tenant',
			'bdName',
			'subnetIp',
			'subnetScope',
			'primaryIp',
			'virtualIp']
	epgData = []
	epgCols = ['tenant',
			'app',
			'epg',
			'nameAlias',
			'bd',
			'bdTenant',
			'prefGroupMember']
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
				'configIssues']
	nodePData = []
	nodePCols = ['name',
	             'descr',
	             'dn',
	             'leafSelector']
	rsAccPortPData = []
	rsAccPortPCols = ['nodeP',
	                  'interfaceProfile',
	                  'dn']

	# Create login session to APIC
	apic = utils.apicSession()

	# Get Fabric Info
	dhcpClientData = get(apic,apic.baseUrl + '/api/node/class/dhcpClient.json')
	dhcpClientList = utils.cleanListDict(dhcpClientData)
	for node in dhcpClientList:
		dhcpData.append((
				node['podId'],
				node['fabricId'],
				node['nodeId'],
				node['model'],
				node['name'],
				node['nameAlias'],
				node['configNodeRole'],
				node['nodeRole'],
				node['nodeType'],
				node['ip'],
				node['spineLevel'],
				node['fwVer'],
				node['runningVer'],
				node['supported'],
				node['extPoolId'],
				node['decomissioned'],
				node['configIssues']
			)
		)

	# Get the current tenants
	tenantsResp = get(apic, apic.baseUrl + '/api/class/fvTenant.json?' \
	                  'rsp-prop-include=config-only')

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
	tenantList = utils.cleanListDict(tenantsResp)
	for tenant in tenantList:
		tnData.append(tenant)
		bdResp = get(apic, apic.baseUrl + '/api/class/fvBD.json?' \
		             'query-target-filter=wcard(fvBD.dn,"{}")&rsp-prop-' \
		             'include=config-only'.format(tenant['name']))
		bdList = utils.cleanListDict(bdResp)
		for bd in bdList:
			subnetResp = get(apic,
				apic.baseUrl + '/api/class/fvSubnet.json?query-target-filter=' \
				'wcard(fvSubnet.dn,"tn-{}/BD-{}/")'.format(tenant['name'], 
				bd['name']))
			subnetList = utils.cleanListDict(subnetResp)
			if not subnetList:
				bdData.append((
					tenant['name'],
					bd['name'],
					'Null',
					'Null',
					'Null',
					'Null'))
			else:
				for sub in subnetList:
					bdData.append((
						tenant['name'],
						bd['name'],
						sub['ip'],
						sub['scope'],
						sub['preferred'],
						sub['virtual']))
		apResp = get(apic, apic.baseUrl + '/api/class/fvAp.json?query-target-filter=wcard('\
	        'fvAp.dn,"tn-{}")'.format(tenant['name']))
		if not apResp:
			pass
		else:
			appList = utils.cleanListDict(apResp)
			for app in appList:
				epgResp = get(apic,
			                apic.baseUrl + '/api/class/fvAEPg.json?' \
			                'query-target-filter=wcard(fvAEPg.dn, '  \
			                '"tn-{}/ap-{}/")&rsp-prop-include=config-only'.format(
				                tenant['name'],
			                    app['name']))
				if not epgResp:
					pass
				else:
					epgList = utils.cleanListDict(epgResp)
					for epg in epgList:
						rsBd = get(apic,
					        apic.baseUrl + '/api/node/mo/uni/tn-{}/ap-{}/epg-{}.json?' \
					            'query-target=children&target-subtree-class=fvRsBd'.format(
					                tenant['name'],
					                app['name'],
					                epg['name']))
						if not rsBd:
							epgData.append((
						        tenant['name'],
						        app['name'],
						        epg['name'],
						        epg['nameAlias'],
						        '',
						        '',
						        epg['prefGrMemb']
						        )
						    )
						else:
							rsBd = utils.cleanListDict(rsBd)
							epgData.append((
						        tenant['name'],
						        app['name'],
						        epg['name'],
						        epg['nameAlias'],
						        rsBd[0]['tnFvBDName'],
						        rsBd[0]['dn'].split('tn-')[1].split('/')[0],
						        epg['prefGrMemb']
						        )
						    )
	
	
	'''
	get access policy information
	
	   1) To include
	       -Switch Profiles
		   -Interface Profiles
		   -AAEPs
		   -Interface Policy Groups
		   -Interface Policies
	
	'''
	
	nodePResp = get(apic, apic.baseUrl + '/api/mo/uni/infra.json?query-target=children&target-subtree-class=infraNodeP&' \
	                  'rsp-prop-include=config-only')
	nodePList = utils.cleanListDict(nodePResp)
	for nodeP in nodePList:
		infraLeafSResp = get(apic, apic.baseUrl + '/api/mo/' + nodeP['dn'] + '.json?query-target=children&target-subtree' \
		                    '-class=infraLeafS')
		if infraLeafSResp:			
			for infraLeafS in infraLeafSResp:
				nodeTup = (nodeP['name'], nodeP['descr'], nodeP['dn'], infraLeafS['infraLeafS']['attributes']['name'])
				nodePData.append(nodeTup)
		elif not infraLeafSResp:
			nodeTup = (nodeP['name'], nodeP['descr'], nodeP['dn'], '')
			nodePData.append(nodeTup)
		rsAccPortPResp = get(apic, apic.baseUrl + '/api/mo/' + nodeP['dn'] + '.json?query-target=children&target-subtree' \
		                '-class=infraRsAccPortP')
		if rsAccPortPResp:
			rsAccPortPList = utils.cleanListDict(rsAccPortPResp)
			for rsAccPortP in rsAccPortPList:
				rsAccPortPTup = (nodeP['name'], rsAccPortP['tDn'].split('accportprof-')[1], rsAccPortP['dn'])
				rsAccPortPData.append(rsAccPortPTup)
		elif not rsAccPortPResp:
			pass
	
	writer = utils.writer(wb)
	try:
		faults(apic, writer=writer)
		utils.dictDumpTwo(writer,dhcpData,dhcpCols, 'dhcpClient')
		utils.dictDumpTwo(writer, nodePData, nodePCols, 'nodeProfiles')
		utils.dictDumpTwo(writer, rsAccPortPData, rsAccPortPCols, 'interfaceProfiles')
		utils.dictDumpTwo(writer,tnData,tnCols, 'fvTenant')
		utils.dictDumpTwo(writer,bdData,bdCols, 'fvBD')
		utils.dictDumpTwo(writer,epgData,epgCols, 'fvAEPg')
		apic.session.close()
	except AssertionError:
		raise AssertionError
	except Exception as ex:
		utils.exceptTempl(ex)


if __name__ == '__main__':
	main(**dict(arg.split('=') for arg in sys.argv[1:]))
