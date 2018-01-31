import jinja2
import coloredlogs
import json
import logging
import requests
import utils
import os
import sys
import pandas as pd
import argparse

requests.packages.urllib3.disable_warnings()
coloredlogs.install()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def createObject(env, template, **kwargs):
	'''
	generic function to generate JSON payloads from
	jinja2 templates and posting to uni.
	'''
	# load and render template
	payloadTemplate = env.get_template(template)
	payload = payloadTemplate.render(kwargs)

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

def createIntfP(env, apic, intfPName, nodePName):
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
	# load, render, and post the rsAccPortP
	intfRsTemplate = env.get_template('rsAccPortP.json')
	intfRsPayload = intfRsTemplate.render(nodePName=nodePName, intfPName=intfPName)
	intfRsResp = apic.session.post(uniUrl, verify=False, data=intfRsPayload)
	utils.responseCheck(intfRsResp)
	logging.info('Interface Profile {} created and linked to {}'.format(intfPName, nodePName))



def fabricBase(apic, **kwargs):
	'''
	Function takes in existing APIC requests session, reads in values
	from a xlsx spreadsheet, and uses them to create APIC MOs related
	to APIC Fabric Policies. Allows passing of filename for the xlsx,
	but if one is not specified, values.xlsx is used as a default
	
	param apic: requests session to use for HTTP Methods
	
	'''
	# Check for filename arg. if not specified, generate base values/objects
	if 'filename' in kwargs:
		wb = kwargs['filename']
	else:
		wb = 'values.xlsx'
	# Open Values xlsx. If it doesn't existing raise a fault
	filePath = os.path.abspath(wb)
	
	# Check if workbook exists and load workbook with pandas
	if not os.path.exists(filePath):
		logging.critical('values.xlsx or {} not found!'.format(wb))
		sys.exit()
	
	logging.info('Loading data from fabric worksheet in {}'.format(wb))
	fabricDf = pd.read_excel(filePath, sheet_name='fabric')
	
	# Load jinja2 templates
	env = utils.loader()
	
	if kwargs['nodes'] == True:
		for row in fabricDf.iterrows():
			if row[1]['nodeId1'] != 'Null' and row[1]['nodeId2'] != 'Null':
				logging.info('Two node IDs in row, skipping nodeProfile and creating Interface Profile')
			elif row[1]['nodeId1'] != 'Null' and row[1]['nodeId2'] == 'Null':
				createNodeP(env, apic, row[1]['nodePName'], row[1]['nodeId1'], row[1]['nodePolGrp'])
			else:
				logging.critical('incorrect node Id values.')
				sys.exit()
	if kwargs['interfaces'] == True:
		for row in fabricDf.iterrows():
			createIntfP(env, apic, row[1]['intfPName'], row[1]['nodePName'])
	if kwargs['policies'] == True:
		logging.info('Creating Interface Policy Groups')
	

def main(*args):
	parser = argparse.ArgumentParser(description="Fabric Builder")
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
	parser.add_argument('-f',
	                    '--filename',
	                    required=False,
	                    nargs="?",
	                    default='values.xlsx',
	                    help="set this option to read from a non-default file. The default is values.xlsx")
	args = parser.parse_args()
	apic = utils.apicSession()
	fabricBase(apic, filename=args.filename, nodes=args.n, interfaces=args.i, policies=args.p)

if __name__ == '__main__':
	main()