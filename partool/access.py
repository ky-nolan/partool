#!/usr/bin/env python3

import coloredlogs
import json
import logging
import requests
import utils
import os
import sys
import pandas as pd
import argparse
import time

requests.packages.urllib3.disable_warnings()
coloredlogs.install()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class values(object):

	def parseArgs(self, args):
		for arg in args:
			self.filename = arg.filename
			self.n = arg.n
			self.i = arg.i
			self.p = arg.p
			self.s = arg.s
			self.w = arg.w
			self.d = arg.d

def createVpcDom():
	'''
	Function creates a vpc pair
	'''

def postMoUni(env, apic, template, kwargs):
	'''
	generic function to generate JSON payloads from
	jinja2 templates and posting to uni.
	'''
	uniUri = '/api/mo/uni.json'
	uniUrl = apic.baseUrl + uniUri
	# load and render template
	payloadTemplate = env.get_template(template)
	payload = payloadTemplate.render(kwargs)
	response = apic.session.post(uniUrl, verify=False, data=payload)
	utils.responseCheck(response)

def createNodeP(env, apic, nodePName, id, nodePolGrp):
	'''
	Function creates switch profiles
	'''
	uniUri = '/api/mo/uni.json'
	uniUrl = apic.baseUrl + uniUri
	# load and render switch profile template
	nodeTemplate = env.get_template('nodeP.json')
	nodePayload = nodeTemplate.render(nodePName=nodePName, nodeId=id, nodePolGrp=nodePolGrp)
	nodeResp = apic.session.post(uniUrl, verify=False, data=nodePayload)
	utils.responseCheck(nodeResp)
	logging.info('Node Profile {} created'.format(nodePName))

def createIntfP(env, apic, intfPName):
	'''
	Function creates interface profiles
	'''
	uniUri = '/api/mo/uni.json'
	uniUrl = apic.baseUrl + uniUri
	# load and render interface profile template
	intfTemplate = env.get_template('intfP.json')
	intfPayload = intfTemplate.render(intfPName=intfPName)
	intfResp = apic.session.post(uniUrl, verify=False, data=intfPayload)
	utils.responseCheck(intfResp)

def createIntfRs(env, apic, nodePName, intfPName):
	uniUri = '/api/mo/uni.json'
	uniUrl = apic.baseUrl + uniUri
	# load, render, and post the rsAccPortP
	intfRsTemplate = env.get_template('rsAccPortP.json')
	intfRsPayload = intfRsTemplate.render(nodePName=nodePName, intfPName=intfPName)
	intfRsResp = apic.session.post(uniUrl, verify=False, data=intfRsPayload)
	utils.responseCheck(intfRsResp)
	logging.info('Interface Profile {} related to {}'.format(intfPName, nodePName))

def fabricBase(apic, *args, **kwargs):
	'''
	Function takes in existing APIC requests session, reads in values
	from a xlsx spreadsheet, and uses them to create APIC MOs related
	to APIC Fabric Policies. Allows passing of filename for the xlsx,
	but if one is not specified, values.xlsx is used as a default

	param apic: requests session to use for HTTP Methods

	'''
	options = values()
	options.parseArgs(args)
	keywords = kwargs
	# Check for filename arg. if not specified, generate base values/objects
	wb = options.filename
	# Open Values xlsx. If it doesn't existing raise a fault
	filePath = os.path.abspath(wb)

	# Check if workbook exists and load workbook with pandas
	if not os.path.exists(filePath):
		logging.critical('values.xlsx or {} not found!'.format(wb))
		sys.exit()
	# Load jinja2 templates
	env = utils.loader()
	if options.n == True:
		nodeDf = pd.read_excel(filePath, sheet_name='nodes')
		for row in nodeDf.iterrows():
			nodePro = row[1]['nodePName']
			intfPro = row[1]['intfPName']
			nodeId = row[1]['nodeId']
			nodePolGrp = row[1]['nodePolGrp']
			logging.info('creating nodeP {} with nodeId {}'.format(nodePro, nodeId))
			createNodeP(env, apic, nodePro, nodeId, nodePolGrp)
	if options.i == True:
		intfProDf = pd.read_excel(filePath, sheet_name='interfaceProfiles')
		for row in intfProDf.iterrows():
			nodePro = row[1]['nodePName']
			intfPro = row[1]['intfPName']
			logging.info('creating intfP {}'.format(intfPro))
			logging.info('associating to nodeP {}'.format(nodePro))
			createIntfP(env, apic, intfPro)
			createIntfRs(env, apic, nodePro, intfPro)
	if options.p == True:
		logging.info('Creating Interface Policy Groups')
		intfPolGrpDf = pd.read_excel(filePath, sheet_name='interfacePolicyGroups')
		intfPolGrpDf.where(intfPolGrpDf.notnull(), '')
		for row in intfPolGrpDf.iterrows():
			lagT = str(row[1]['lagT'])
			if lagT.lower() == 'node' or lagT.lower() == 'link':
				postMoUni(env, apic, 'infraAccBndlGrp.json', row[1])
				logging.info('VPC|Port-channel Interface Policy Group {} deployed'.format(row[1]['name']))
			elif lagT == 'nan':
				postMoUni(env, apic, 'infraAccPortGrp.json', row[1])
				logging.info('Access Interface Policy Group {} deployed'.format(row[1]['name']))
			else:
				logging.critical('Invalid lagT value in worksheet interfacePolicyGroups')
				logging.critical('node = vpc; link=discrete port-channel; <null> = access')
				logging.critical('lagT value specified was {}'.format(lagT))
				sys.exit()
			time.sleep(5)
	if options.d == True:
		logging.info('Deploying interface selectors from interfaces worksheet')
		intfDf = pd.read_excel(filePath, sheet_name='interfaces')
		for row in intfDf.iterrows():
			postMoUni(env, apic, 'infraHPortS.json', row[1])
			logging.info('Deployed {} to interface profile {}'.format(row[1]['hPortS'], row[1]['accPortProf']))
			time.sleep(3)

	if options.s == True and options.w == '':
		logging.critical('single post set, but worksheet option -w not specified')
		logging.critical('please specify a worksheet to load post data from')
		sys.exit(1)
	elif options.s == True and options.w != '':
		postMoUni(env, apic, kwargs['template'], kwargs)


def main(*args):
	parser = argparse.ArgumentParser(description="Bulk Access Policies")
	parser.add_argument('-n',
	                    action="store_true",
	                    default=False,
	                    help="set this option to deploy switch profiles")
	parser.add_argument('-i',
	                    action="store_true",
	                    default=False,
	                    help="set this option to deploy interface profiles")
	parser.add_argument('-p',
	                    action="store_true",
	                    default=False,
	                    help="set this option to deploy interface policy-groups")
	parser.add_argument('-s',
	                    action="store_true",
	                    default=False,
	                    help="set this for single posts")
	parser.add_argument('-w',
	                    required=False,
	                    nargs="?",
	                    default='',
	                    help="set worksheet for single posts")
	parser.add_argument('-d',
	                    action="store_true",
	                    default=False,
	                    help="set this to deploy interface selectors from interfaces worksheet")
	parser.add_argument('-f',
	                    '--filename',
	                    required=False,
	                    nargs="?",
	                    default='values.xlsx',
	                    help="set this option to read from a non-default file. The default is values.xlsx")
	args, unknown = parser.parse_known_args()
	apic = utils.apicSession()
	fabricBase(apic,args,**dict(kwarg.split('=') for kwarg in unknown))
	apic.session.close()

if __name__ == '__main__':
	main()
