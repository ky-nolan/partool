import coloredlogs
import logging
import json
import requests
import requests.packages.urllib3
import os
from getpass import getpass
import re
import pandas as pd
import jinja2

requests.packages.urllib3.disable_warnings()
coloredlogs.install()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def _zero_pad(match):
	# optional '-' to support negative numbers
	_num_re = re.compile(r'-?\d+')
	# number of chars in the largest possible int
	_maxint_digits = 8
	# format for zero padding positive integers
	_zero_pad_int_fmt = '{{0:0{0}d}}'.format(_maxint_digits)
	# / is 0 - 1, so that negative numbers will come before positive
	_zero_pad_neg_int_fmt = '/{{0:0{0}d}}'.format(_maxint_digits)
	n = int(match.group(0))
	# if n is negative, we'll use the negative format and flip the number using
	# maxint so that -2 comes before -1, ...
	return _zero_pad_int_fmt.format(n) \
	       if n > -1 else _zero_pad_neg_int_fmt.format(n + _maxint_digits)

def zero_pad_numbers(s):
	_num_re = re.compile(r'-?\d+')
	return _num_re.sub(_zero_pad, s)

def checkfile(path):
	path = os.path.expanduser(path)
	if not os.path.exists(path):
		return path
	root, ext = os.path.splitext(os.path.expanduser(path))
	dir = os.path.dirname(root)
	fname = os.path.basename(root)
	candidate = fname+ext
	index = 0
	ls  = set(os.listdir(dir))
	while candidate in ls:
		candidate = "{}_{}{}".format(fname,zero_pad_numbers(str(index)),ext)
		index    += 1
		logging.info("Specified file {} exists".format(path))
		logging.info("Creating file as {}".format(candidate))
	return os.path.join(dir,candidate)

def findCreds(jsonFile):
	filePath = os.path.abspath(jsonFile)
	if os.path.exists(filePath):
		with open(filePath) as infoJson:
			logger.info('Attempting to open {}'.format(filePath))
			try:
				d = json.load(infoJson)
				logging.info('{} loaded.'.format(filePath))
				logging.info('Checking for APIC access info')
				apicIp = str(d['apicIp'])
				username = d['apicUsername']
				password = d['apicPassword']
				if not apicIp = '':
					logging.info("APIC IP found in {}".format(jsonFile))
				else:
					try:
						apicIp = str(input(
							"APIC IP not specified in {}\n" \
							"APIC IP:".format(jsonFile)))
					except ValueError:
						print('APIC IP')
						apicIp = str(input())
				if not username == '':
					logging.info("APIC Username found in {}".format(jsonFile))
				else:
					try:
						username = str(input(
						    "Username not specified in {}\n" \
						    "Username:".format(jsonFile)))
					except ValueError:
						print('Username:')
						username = str(input())
				if not password == '':
					logging.info("APIC Password found in {}".format(jsonFile))
				else:
					try:
						password = getpass()
					except ValueError:
						print('Password:')
						password = getpass()
				if not apicIp == '':
					baseUrl = "https://" + apicIp
					logging.info("APIC IP/Hostname found in {}".format(jsonFile))
				else:
					try:
						baseUrl = 'https://' + str(input('APIC IP or Hostname:'))
					except ValueError:
						baseUrl = 'https://' + str(input('APIC IP or Hostname:'))
				payload = {"aaaUser" : {
				    "attributes" : {
				        "name" : username,
				        "pwd"  : password
				    }}}
				return payload, baseUrl
			except IOError:
				logging.critical('{} file not found!'.format(jsonFile))

class apicSession(object):

	def __init__(self):
		self.payload, self.baseUrl = findCreds('info.json')
		self.loginUri = '/api/aaaLogin.json'
		self.loginUrl = self.baseUrl + self.loginUri
		self.session = self.login()

	def login(self):
		with requests.Session() as s:
			p = s.post(self.loginUrl, json=self.payload, verify=False)
			responseCheck(p)
			return s


def responseCheck(response):
	'''
	Check if response status code is 200 and do nothing if it is. If value
	other than 200, raise fault and log the status code.
	'''
	if response.status_code != 200:
		logging.critical(response.text)
		response.raise_for_status()

def login():
	'''

	'''
	payload, baseUrl = findCreds('info.json')
	loginUri = '/api/aaaLogin.json'
	loginUrl = baseUrl + loginUri

	with requests.Session() as s:
		p = s.post(loginUrl, json=payload, verify=False)
		if p.status_code != 200:
			logging.critical("Error response code = {}".format(p.status_code))
			logging.critical("Response = {}".format(p.text))
			raise Error
		else:
			logging.info("Connection to APIC successful")

def dictDump(writer, data, ws):
	'''
	'''
	df = pd.DataFrame(data)
	df.to_excel(writer, sheet_name=ws)
	return logger.info('{} data written successfully!'.format(ws))

def dictDumpTwo(writer, data, columnNames, ws):
	'''
	'''
	df = pd.DataFrame(data, columns=columnNames)
	df.to_excel(writer, sheet_name=ws)
	return logger.info('{} data written successfully!'.format(ws))

def writer(wb):
	return pd.ExcelWriter(path=wb, engine='xlsxwriter')


def loader():
	'''
	Function sets the jinja2 template folder to load ACI related
	json files from. It returns an object that can be used to
	load jinja2 formatted json files to pass variables into for
	ACI Managed Object (MO) creation
	'''
	loader = jinja2.FileSystemLoader(searchpath="./templates/")
	env = jinja2.Environment(loader=loader)
	env.filters['jsonify'] = json.dumps
	return env

def template(env, jsonFile):
	'''
	Function loads a specified JSON/jinja2 template

	param env: jinja2 object representing the loaded templates
	param jsonFile: name of the JSON template file to be loaded

	returns template to be passed variables to be rendered
	'''
	template = env.get_template(jsonFile)
	return template
