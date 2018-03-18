# PARTOOL
Python ACI Rest Tools - PARTOOL is a series of command line tools to be used for interfacing with Cisco's Application Centric Infrastructure (ACI). Currently, the tool solely communicates with the ACI Controller or APIC (Application Policy Infrastructure Controller).

## utils module (utils.py)
The utils module is a utilities module that is used to house general functions for other modules. E.g. - creating a requests session with the APIC or a function to perform a generic HTTP POST to the Cisco APIC.

## access module (access.py)
Used to deploy fabric access policies. It is a command line tool that allows you to specify
the following options -
	1) -n : read in data from nodes worksheet in xlsx file and creates leaf switch
profiles.
	2) -i ; read in data from interfaceProfiles worksheet in xlsx file and creates leaf interface
profiles.
	3) -p ; read in data from interfacePolGrps worksheet in xlsx file and creates interface policy
groups.
	4) -d ; read in data from interfaces worksheet in xlsx file and creates interface selectors

## discovery module (discovery.py)
Used to collect information about an existing fabric (Only uses HTTP GET Method). It is a command
line tool that allows you to specify the following keyword arguments
    1) filename=<filename>.xlsx
        e.g. - python filename=lab-fabric-discovery.xlsx would collect info and write it to
        lab-fabric-discovery.xlsx
Currently, the discovery model collects the following information from the Cisco APIC and writes in to an excelspreadsheet. 
    1) DHCP Clients: Spines, Leafs, vPC VIPs, AVE, AVS, etc.
    2) Tenants
        a) Application Network Profiles
        b) Endpoint Groups
        c) Bridge Domains
        d) Open Faults


## portbounce (portbounce.py)
The portbounce tool can be used to shut/no shut an ACI Leaf or Spine interface. Upon execution, the tool will prompt the user to specify a pod ID, node ID, and port ID. After validating the specified integers are within acceptable ranges, it will proceed to administrativly disable the port, wait 1 second, and re-enable the port. *** Currently there is no support for FEX Modules or Uplink ports, that have been converted to downlinks.
