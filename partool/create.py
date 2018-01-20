#!/usr/bin/env python

import logging
import requests
'''
class node:
	def __init__(self):
		print('object created')

		self.podId = kwargs.
	 	self.nodeId = nodeId
	 	self.hostname = hostname
	 	self.peerNodeId = peerNodeId

'''
def login():
	apicIp = '10.89.169.66'
	payload = '''{
		"aaaUser" : {
			"attributes" : {
				"name" : "admin",
				"pwd" : "password"
				}
			}
		}
		'''
	loginUri = '/api/aaaLogin.json'
	faultsUri = '/api/node/class/faultSummary.json?query-target-filter=and()&order-by=faultSummary.severity'

	baseUrl = 'https://{}'.format(apicIp)
	loginUrl = baseUrl + loginUri
	faultsUrl = baseUrl + faultsUri

	with requests.Session() as s:
		p = s.post(loginUrl, data=payload, verify=False)
		print(p.text)
		faultsResponse = s.get(faultsUrl, verify=False)
		print(faultsResponse.text)

def printKwargs(**kwargs):
	for key, value in kwargs.items():
		print("The value of {} is {}".format(key, value))

def main():
	login()

if __name__ == '__main__':
	main()
