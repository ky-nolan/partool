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

def createVpcDom():
	'''
	Function creates a vpc pair
	'''

def postMoUni(env, apic, template, **kwargs):
	'''
	generic function to generate JSON payloads from
	jinja2 templates and posting to uni.
	'''
	# load and render template
	payloadTemplate = env.get_template(template)
	payload = payloadTemplate.render(kwargs)
	respose = apic.session.post(uniUrl, verify=False, data=payload)
	utils.responseCheck(response)
	return logging.info('postMoUni successfully deployed')
	

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
	if kwargs['single'] == True and kwargs['ws'] == '':
		logging.critical('single post set, but worksheet option -w not specified')
		logging.critical('please specify a worksheet to load post data from')
	elif kwargs['single'] == True and kwargs['ws'] != '':
		df = pd.read_excel(filePath, sheet_name=kwargs['ws'])
		postMoUni(env, apic, template)
	if kwargs['nodes'] == True:
		for row in fabricDf.iterrows():
			vpcId = str(row[1]['vpcId'])
			nodePro = row[1]['nodePName']
			intfPro = row[1]['intfPName']
			nodeId = row[1]['nodeId']
			nodePolGrp = row[1]['nodePolGrp']
			if vpcId.lower() != 'Null':
				logging.info('creating intfP {}'.format(intfPro))
				logging.info('associating to nodeP {}'.format(nodePro))
				createIntfP(env, apic, intfPro)
				createIntfRs(env, apic, nodePro, intfPro)
			elif vpcId.lower() == 'Null':
				logging.info('creating nodeP {} with nodeId {}'.format(nodePro, nodeId))
				createNodeP(env, apic, nodePro, nodeId, nodePolGrp)
			else:
				logging.critical('incorrect vpcId value. specify integer or Null')
				sys.exit()
	if kwargs['interfaces'] == True:
		for row in fabricDf.iterrows():
			nodePro = row[1]['nodePName']
			intfPro = row[1]['intfPName']
			createIntfP(env, apic, intfPro)
			createIntfRs(env, apic, nodePro, intfPro)
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
	parser.add_argument('-s',
	                    action="store_true",
	                    default=False,
	                    help="set this for single posts")
	parser.add_argument('-w',
	                    required=False,
	                    nargs="?",
	                    default='',
	                    help="set worksheet for single posts")	
	parser.add_argument('-f',
	                    '--filename',
	                    required=False,
	                    nargs="?",
	                    default='values.xlsx',
	                    help="set this option to read from a non-default file. The default is values.xlsx")
	args = parser.parse_args()
	apic = utils.apicSession()
	fabricBase(apic,
	           filename=args.filename,
	           nodes=args.n,
	           interfaces=args.i,
	           policies=args.p,
	           single=args.s,
	           ws=args.w)

if __name__ == '__main__':
	main()