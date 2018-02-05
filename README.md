# partool

## access module
Used to deploy fabric access policies. It is a command line tool that allows you to specify
the following options -
	1) -n : read in data from nodes worksheet in xlsx file and creates leaf switch
profiles.
	2) -i ; read in data from interfaceProfiles worksheet in xlsx file and creates leaf interface
profiles.
	3) -p ; read in data from interfacePolGrps worksheet in xlsx file and creates interface policy
groups.
	4) -d ; read in data from nodes worksheet in xlsx file and creates interface policy
groups.

## discovery module
Used to collect information about an existing fabric (Only uses HTTP GET Method). It is a command
line tool that allows you to specify the following keyword arguments
    1) filename=<filename>.xlsx
        e.g. - python filename=lab-fabric-discovery.xlsx would collect info and write it to
        lab-fabric-discovery.xlsx
