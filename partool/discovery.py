import coloredlogs
import json
import logging
import requests
import utils
import sys

requests.packages.urllib3.disable_warnings()
coloredlogs.install()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def getIntfP(apic, baseUrl):
    intfProfUri = '/api/class/infraAccPortP.json'
    intfProfUrl = baseUrl + intfProfUri
    intfProfResp = apic.session.get(intfProfUrl, verify=False)
    utils.responseCheck(intfProfResp)
    intfProfJson = json.loads(intfProfResp.text)
    return intfProfJson

def writeIntfP(apic, writer, wb):
    intfProfResp = getIntfP(apic, apic.baseUrl)
    data = {}
    columnNames = ['name', 'dn']
    for intfProf in intfProfResp['imdata']:
        name = intfProf['infraAccPortP']['attributes']['name']
        dn = intfProf['infraAccPortP']['attributes']['dn'] 
        data[name] = dn
    utils.dictDumpTwo(writer, list(data.items()), columnNames, 'interfaceProfiles')   
    return logging.info('Interface Profiles written to {}'.format(wb))

def getAccPortGrp(apic, baseUrl):
    accPortGrpUri = '/api/node/class/infraAccPortGrp.json'
    accPortGrpUrl = baseUrl + accPortGrpUri
    accPortGrpResp = apic.session.get(accPortGrpUrl, verify=False)
    utils.responseCheck(accPortGrpResp)
    accPortGrpJson = json.loads(accPortGrpResp.text)
    return accPortGrpJson

def getAccBndlGrp(apic, baseUrl):
    accBndlGrpUri = '/api/node/class/infraAccBndlGrp.json'
    accBndlGrpUrl = baseUrl + accBndlGrpUri
    accBndlGrpResp = apic.session.get(accBndlGrpUrl, verify=False)
    utils.responseCheck(accBndlGrpResp)
    accBndlGrpJson = json.loads(accBndlGrpResp.text)
    return accBndlGrpJson

def writePolGrps(apic, writer, wb):
    # Discrete Port Policy Groups
    accPortGrpResp = getAccPortGrp(apic, apic.baseUrl)
    data = []
    columnNames = ['name', 'dn', 'type']
    for accPortGrp in accPortGrpResp['imdata']:
        name = accPortGrp['infraAccPortGrp']['attributes']['name']
        dn = accPortGrp['infraAccPortGrp']['attributes']['dn']
        type = 'access'
        data.append([name, dn, type])
    # Port-channel or vPC Policy Groups
    accBndlGrpResp = getAccBndlGrp(apic, apic.baseUrl)
    for accBndlGrp in accBndlGrpResp['imdata']:
        name = accBndlGrp['infraAccBndlGrp']['attributes']['name']
        dn = accBndlGrp['infraAccBndlGrp']['attributes']['dn']
        if accBndlGrp['infraAccBndlGrp']['attributes']['lagT'] == 'link':
            type = 'port-channel'
        elif accBndlGrp['infraAccBndlGrp']['attributes']['lagT'] == 'node':
            type = 'vpc'
        data.append([name, dn, type])
    logging.info(data)
    utils.dictDumpTwo(writer, data, columnNames, 'intfPolGrps')
    return logging.info('Interface Policy Groups written to {}'.format(wb))

def main(**kwargs):
    '''
    '''
    apic = utils.apicSession()
    if 'filename' in kwargs:
        wb = kwargs['filename']
    else:
        wb = 'build-info.xlsx'
    writer = utils.writer(wb)
    writeIntfP(apic, writer, wb)
    writePolGrps(apic, writer, wb)
    apic.session.close()	

if __name__ == '__main__':
    main(**dict(arg.split('=') for arg in sys.argv[1:]))
