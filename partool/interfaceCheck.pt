import kyle_login
import json
import logging
from pprint import pprint
import time

logging.basicConfig(level=logging.CRITICAL, format='%(asctime)s - %(levelname)s - %(message)s')

# give all the Nodes(leads/spines)
#/api/node/class/fabricNode.xml?
#/api/node/class/fabricNode.xml?


class interface:
    def __init__(self, dict, loginObj):
        self.interfaceNumber = dict["id"]
        self.upDown = dict["adminSt"]
        self.description = dict["descr"]
        self.autoNeg = dict["autoNeg"]
        self.usage = dict["usage"]
        self.mtu = dict["mtu"]
        self.__dn = dict["dn"]
        self.__monDn = dict["monPolDn"]

        # query the child for more info
        apicIp = loginObj.ip
        s = loginObj.session
        # query to dive into the child interface
        self.__childDn = "https://" + apicIp + "/api/node/mo/" + self.__dn + "/phys.json"
        self.__spfDN = "https://" + apicIp + "/api/node/mo/" + self.__dn + "/phys/fcot.json"
        r3 = s.get(self.__spfDN)
        dic3 = r3.json()['imdata'][0]['ethpmFcot']['attributes']
        r = s.get(self.__childDn)
        try:
            dict2 = r.json()['imdata'][0]['ethpmPhysIf']['attributes']
        except:
            dict2 = r.json()['imdata'][0]['eltmPhysIf']['attributes']
        self.backplaneMac = dict2["backplaneMac"]
        self.encapVlan = dict2['encap']
        self.accessVlan = dict2['accessVlan']
        self.primaryVlan = dict2['primaryVlan']
        self.operVlans = dict2['operVlans']
        self.operSpeed = dict2['operSpeed']
        self.operSt = dict2['operSt'] #protocol up/down
        self.sfp = dic3['typeName'] #sfp
        self.sfpType = dic3['type']
        self.operMode = dict2['operMode'] # trunk or not
        self.operDuplex = dict2['operDuplex']
        self.allowedVlans = dict2['allowedVlans']

        self.node = None
        self.__nodeAttached = False

    def __str__(self):
        if self.__nodeAttached is True:
            return str(self.node.hostname + ", " + self.node.nodeNumber + ", " + self.interfaceNumber + ", " + self.upDown + " "+ self.operSt + ", " + self.description + ", " + self.operSpeed + ", " + self.sfp + ', ' + self.usage)
        else:
            return str(self.interfaceNumber + ", " + self.upDown + ", " + self.description)

    #adds node obj to the interface
    def attachNode(self, nodeList):
        nodeTemp = self.__dn.split("/")[2].replace('node-', "").replace(" ", '')
        for n in nodeList:
            if n.nodeNumber == nodeTemp:
                self.node = n
                self.__nodeAttached = True

    def attachlldp(self, lldpList):
        #/api/node/class/lldpIf.json?
        pass


class node:
    def __init__(self, dict, loginObj):
        self.serial = dict['serial']
        self.role = dict['role']
        self.model = dict['model']
        self.nodeNumber = dict['id']
        self.hostname = dict['name']
        self.__dn = dict["dn"]

        # grabbing child OBJ
        apicIp = loginObj.ip
        s = loginObj.session
        childQuery = "https://" + apicIp + "/api/node/mo/" + self.__dn +"/sys.json"
        r = s.get(childQuery)
        dict2 = r.json()['imdata'][0]['topSystem']['attributes']
        self.address = dict2['address']
        self.oobAddress = dict2['oobMgmtAddr']
        self.tepPool = dict2['tepPool']
        self.systemUpTime = dict2['systemUpTime']
        self.fabricMAC = dict2['fabricMAC']
        self.fabricDomain = dict2['fabricDomain']
        self.fabricId = dict2['fabricId']
        self.controlPlaneMTU = dict2['controlPlaneMTU']
        self.__currentTime = dict2['currentTime']

    def __str__(self):
        return str(self.hostname + ", " + self.nodeNumber + ", " + self.address + ", " + self.oobAddress)

loginObj = kyle_login.login('10.224.97.51', 'admin', 'cisco123')
s = loginObj.session

# get for interfaces
r = s.get('https://10.224.97.51/api/node/class/l1PhysIf.json')

# get for nodes
r2 = s.get("https://" + loginObj.ip + '/api/node/class/fabricNode.json?')



# iterating Nodes
r2Data = r2.json()['imdata']
allNodes = []
for i in r2Data:
    i = i['fabricNode']['attributes']
    nodeI = node(i, loginObj)
    allNodes.append(nodeI)
    print nodeI



# iternation interfaces
data = r.json()['imdata']
allInts = []
for i in data:
    i = i['l1PhysIf']['attributes']
    inter = interface(i, loginObj)
    allInts.append(inter)
    inter.attachNode(allNodes)
    print inter
