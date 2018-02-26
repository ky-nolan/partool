import jinja2
import coloredlogs
import logging
import requests
import utils
import argparse
import time

def main():
	# Disable unsigned certificate warning
	requests.packages.urllib3.disable_warnings()

	# Start logging
	coloredlogs.install()
	logging.basicConfig(level=logging.INFO)
	logger = logging.getLogger(__name__)

	# Add command line arguments
	parser = argparse.ArgumentParser(description="Port Bounce")
	parser.add_argument('-p',
						'--podId',
						type=int,
						default=0,
						help="ACI Pod Id with node and port to be bounced"
						)
	parser.add_argument('-n',
						'--nodeId',
						type=int,
						default=0,
						help="ACI Leaf/Spine Node ID with port to be bounced."
						)
	parser.add_argument('-i',
						'--portId',
						type=int,
						default=0,
						help="Switch port ID to be bounced."
						)
	parser.add_argument('-u',
					'--user',
					type=str,
					help="Username for logging into APIC"
					)
	parser.add_argument('-s',
				'--pwd',
				type=str,
				help="Password for logging into APIC"
				)
	args = parser.parse_args()

	# Check argument values
	if args.podId > 0 and args.podId < 12:
		pod = args.podId
	else:
		pod = int(input("Enter Pod Id: "))
		if pod > 0 and pod < 12:
			pass
		else:
			logging.critical('Invalid Pod Id. Enter value between 1 - 12.')
			raise ValueError
	if args.nodeId > 99 and args.nodeId < 3999:
		node = args.nodeId
	else:
		node = int(input("Enter Node Id: "))
		if node > 99 and node < 3999:
			pass
		else:
			logging.critical('Invalid Node Id. Enter value between 99 - 3999.')
			raise ValueError
	if args.portId > 0 and args.portId < 49:
		port = args.portId
	else:
		port = int(input("Enter Port Id: "))
		if port > 0 and port < 49:
			pass
		else:
			logging.cricitcal('Invalid Port Id. Enter value between 1 - 48.')
			raise ValueError

	# Create login session with APIC
	ls = utils.apicSession()
	shutArgs = {
	    'tDn': 'topology/pod-{}/paths-{}/pathep-[eth1/{}]'.format(str(pod),str(node),str(port)),
	    'lc': 'blacklist',
	}
	# Shutdown the specified port and log success
	resp = utils.postMo(ls,
	                    '/api/node/mo/uni/fabric/outofsvc.json',
	                    'fabricRsOosPath.json',
	                    args=shutArgs)

	logging.info('NodeId - {} PortId - {} disabled.'.format(node, port))
	logging.info('Sleeping for 10 seconds before re-enabling...')

	# Sleep for 10 seconds
	time.sleep(10)

	noShutArgs = {
	    'dn': 'uni/fabric/outofsvc/rsoosPath-[topology/pod-{}/paths-{}/pathep-[eth1/{}]]'.format(str(pod),node,port),
	    'status': 'deleted'
	}	
	# Re-enable the port
	resp = utils.postMo(ls,
	                    '/api/node/mo/uni/fabric/outofsvc.json',
	                    'fabricRsOosPath.json',
	                    noShutArgs)

	# Close the login session with APIC
	ls.session.close()



if __name__ == '__main__':
	main()