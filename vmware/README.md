vmware poller in zabbix
-----------------------

Python script for polling ESXi servers via CIM. Only tested in ESXi4.1 free.
Shows stuff like service tag, sel, fan, psu, raid controller status..

Short how to:

1. Install pywbem python module (apt-get install python-pywbem - when running debuntu)
2. Import template into zabbix
3. Create vmware host and map it to template
4. Cron job for vmware-poller.py, provide details for server (vmware-poller.py -h   for help)

Monitoring items can be extended by creating new subclasses of CIMBasePoller and mapping them in the SERVERMODEL dict
