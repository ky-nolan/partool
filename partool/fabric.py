import jinja2
import coloredlogs
import json
import logging
import requests
import utils
import os
import sys
import pandas as pd

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

def createNodeP(env, apic, nodeRow):
	'''
	Function creates switch profile and interface profiles
	'''
	# load and render interface profile template
	intfTemplate = env.get_template('intfP.json')
	intfPayload = intfTemplate.render(name=nodeRow['name'])
	if nodeRow['nodeId1'] != Null and nodeRow['nodeId2'] != Null:
		# load and render switch profile template
		nodeTemplate = env.get_template('nodeP.json')
	elif nodeRow['nodeId1'] != Null and nodeRow['nodeId2'] == Null:
		logging.info('')
	else:
		logging.critical('Node Id values incorrect')
		
	nodePayload = nodeTemplate.render(name=name, nodeId=nodeId)
	uniUri = '/api/mo/uni.json'
	uniUrl = apic.baseUrl + uniUri
	apic.session.post(uniUrl, verify=False, data=intfPayload)
	apic.session.post(uniUrl, verify=False, data=nodePayload)
	

def fabricBase(apic, **kwargs):
	'''
	Function takes in existing APIC requests session, reads in values
	from a xlsx spreadsheet, and uses them to create APIC MOs related
	to APIC Fabric Policies. Allows passing of filename for the xlsx,
	but if one is not specified, values.xlsx is used as a default
	
	param apic: requests session to use for HTTP Methods
	
	'''
	# Check for kwargs. if not specified, generate base values/objects
	if 'filename' in kwargs:
		wb = kwargs['filename']
	else:
		wb = 'values.xlsx'
	
	# Open Values xlsx. If it doesn't existing raise a fault
	filePath = os.path.abspath(wb)
	
	# Check if workbook exists and load workbook with pandas
	if not os.path.exists(filePath):
		logging.critical('values.xlsx or {} not found!'.format(wb))
		sys.exit(status=2)
	fabricDf = pd.read_excel(filePath, sheet_name='fabric')
	
	# Load jinja2 templates
	env = utils.loader()
	for row in fabricDf.iterrows():
		logging.info((row[1]['name'],row[1]['nodeId']))
		#logging.info(row['name'],row['nodeId'])
		createNodeP(env, apic, row[1])
	

def main(**kwargs):
	apic = utils.apicSession()
	fabricBase(apic)


if __name__ == '__main__':
	main(**dict(arg.split('=') for arg in sys.argv[1:]))