#!/usr/bin/env python
'''
Created on Oct 10, 2010

Purpose:
To retrieve hardware statistics from VMware servers running ESXi

Dependencies:
pywbem python modules

Usage:
Run from crontab like:
./vmware-poller.py -s <servertype> -i <host> -z <servername>

* servertype is one of the hash key values in the SERVERMODEL hash variable below
* host is the fqdn or ip address of the vmware server
* servername is the vmware server host name in zabbix

Every CIM Class inherits the base class so just extend with a new one if a new parameter needs
to be added. Also every model needs to have a config entry in the SERVERMODEL dict, where first key
is server model and second is "description": [Class,number of iterations]

@author: johan
'''


import pywbem
from optparse import OptionParser
import subprocess
import traceback
from pywbem import CIMError

class CIMBasePoller(object):
    def __init__(self,**kwargs):
        if not kwargs.has_key('namespace'):
            kwargs['namespace'] = 'root/cimv2'
        self.client = pywbem.WBEMConnection('https://%s' % kwargs['server'],(kwargs['username'],kwargs['password']),kwargs['namespace'])
    def showAllItemDescriptions(self):
        count = 0
        for record in self.result:
            if record.has_key('ElementName'):
                print "Index: %s" % str(count)
                print "ElementName: %s" % record['ElementName']
                print "-------------------"
            count += 1
    def showAllItems(self):
        index_id = 0
        for record in self.result:
            print "---- INDEXID: %s" % str(index_id)
            for key in record.keys():
                print "%s: %s" % (key,record[key])
            print "----------------------------"
            index_id += 1
    def getHealthState(self,index):
        return self.result[index]['HealthState']
    def getDescription(self,index):
        return self.result[index]['Description']
    def getOperationalStatus(self,index):
        return self.result[index]['OperationalStatus'][0]
    def execute(self,total):
        rdict = {}
        for i in range(0,total):
            try:
                rdict.update(self.getResult(i))
            except IndexError, er:
                pass
        for k in rdict.keys(): self.zabbixSend(k, rdict[k])
    def setZabbixInfo(self, **kwargs):
        self.zabbixserver = kwargs['zabbixserver']
        self.zabbixhost = kwargs['zabbixhost']
    def zabbixSend(self, key, value):
        p = subprocess.Popen(["/usr/bin/env", "zabbix_sender",
                              "-z", str(self.zabbixserver),
                              "-s", str(self.zabbixhost),
                              "-k", str(key),
                              "-o", str(value)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False).communicate()

class CIMPowerSupplyPoller(CIMBasePoller):
    def __init__(self,**kwargs):
        super(CIMPowerSupplyPoller,self).__init__(**kwargs)
        self.result = self.client.EnumerateInstances('OMC_PowerSupply')
    def getResult(self,index):
        result = { 'powerSupplyLocationName.1.%s' % str(index+1): self.getDescription(index),
                   'powerSupplySensorState.1.%s' % str(index+1): self.getAvailability(index),
                   'powerSupplyStatus.1.%s' % str(index+1): self.getHealthState(index) }
        return result
    def getAvailability(self,index):
        return self.result[index]['Availability']

class CIMNumericSensorPoller(CIMBasePoller):
    def __init__(self,**kwargs):
        super(CIMNumericSensorPoller,self).__init__(**kwargs)
        self.result = self.client.EnumerateInstances('OMC_NumericSensor')
    def getTemperatureStatus(self):
        return self.result[10]['CurrentReading']
    def getResult(self,index):
        result = { 'systemTemperature.1.%s' % str(index+1): self.getTemperatureStatus()}
        return result

# PER720 servers have different temperature items
class CIMNumericSensorPollerPER720(CIMBasePoller):
    def __init__(self,**kwargs):
        super(CIMNumericSensorPollerPER720,self).__init__(**kwargs)
        self.result = self.client.EnumerateInstances('OMC_NumericSensor')
    def getTemperatureStatus(self):
        return self.result[5]['CurrentReading']
    def getResult(self,index):
        result = { 'systemTemperature.1.%s' % str(index+1): self.getTemperatureStatus()}
        return result
    
class CIMChassisPoller(CIMBasePoller):
    def __init__(self,**kwargs):
        super(CIMChassisPoller,self).__init__(**kwargs)
        self.result = self.client.EnumerateInstances('OMC_Chassis')
    def getSerialTag(self,index):
        return self.result[index]['SerialNumber']
    def getModel(self,index):
        return self.result[index]['Model']
    def getResult(self,index):
        result = { 'chassisServiceTagName.%s' % str(index+1): self.getSerialTag(index),
                   'chassisModelName.%s' % str(index+1): self.getModel(index) }
        return result
    
class CIMProcessorPoller(CIMBasePoller):
    def __init__(self,**kwargs):
        super(CIMProcessorPoller,self).__init__(**kwargs)
        self.result = self.client.EnumerateInstances('OMC_Processor')
    def getNumberOfCores(self,index):
        return self.result[index]['NumberOfEnabledCores']
    def getResult(self,index):
        result = { 'processorDeviceStatusStatus.1.%s' % str(index+1): self.getHealthState(index),
                   'processorDeviceStatusLocationName.1.%s' % str(index+1): self.getDescription(index) }
        return result

class CIMRaidPoller(CIMBasePoller):
    def __init__(self,**kwargs):
        super(CIMRaidPoller,self).__init__(**kwargs)
        self.result = self.client.EnumerateInstances('VMware_HHRCStorageVolume')
    def getExtentStatus(self,index):
        return self.result[index]['ExtentStatus'][0]
    def getOperationalStatus(self,index):
        return self.result[index]['OperationalStatus'][0]
    def getResult(self,index):
        result = { 'raidControllerExtentStatus.%s' % str(index+1): self.getExtentStatus(index),
                   'raidControllerOperationalStatus.%s' % str(index+1): self.getOperationalStatus(index),
                   #'raidControllerName.%s' % str(index+1): self.getDescription(index),
                   'raidControllerStatus.%s' % str(index+1): self.getHealthState(index) }
        return result

class CIMEthernetPortPoller(CIMBasePoller):
    def __init__(self,**kwargs):
        super(CIMEthernetPortPoller,self).__init__(**kwargs)
        self.result = self.client.EnumerateInstances('VMware_EthernetPort')

class CIMHardDiskPoller(CIMBasePoller):
    def __init__(self,**kwargs):
        super(CIMHardDiskPoller,self).__init__(**kwargs)
        self.result = self.client.EnumerateInstances('VMware_HHRCDiskDrive')
    def getResult(self,index):
        result = { 'arrayDiskState.%s' % str(index+1): self.getHealthState(index) }
        return result

class CIMRaidControllerBatteryPoller(CIMBasePoller):
    def __init__(self,**kwargs):
        super(CIMRaidControllerBatteryPoller,self).__init__(**kwargs)
        self.result = self.client.EnumerateInstances('VMware_HHRCBattery')
    def getBatteryStatus(self,index):
        return self.result[index]['BatteryStatus']
    def getResult(self,index):
        result = { 'batteryState.%s' % str(index+1): self.getBatteryStatus(index),
                   'batteryStatus.%s' % str(index+1): self.getHealthState(index) }
        return result

class CIMPhysicalMemoryPoller(CIMBasePoller):
    def __init__(self,**kwargs):
        super(CIMPhysicalMemoryPoller,self).__init__(**kwargs)
        self.result = self.client.EnumerateInstances('OMC_PhysicalMemory')
    def getCapacity(self,index):
        return self.result[index]['Capacity']
    def getPartNumber(self,index):
        return self.result[index]['PartNumber']
    def getResult(self,index):
        result = { 'memoryOperationalStatus.%s' % str(index+1): self.getOperationalStatus(index),
                   'memoryCapacity.%s' % str(index+1): self.getCapacity(index),
                   'memoryPartNumber.%s' % str(index+1): self.getPartNumber(index) }
        return result

class CIMRedundancySetPoller(CIMBasePoller):
    def __init__(self,**kwargs):
        super(CIMRedundancySetPoller,self).__init__(**kwargs)
        self.result = self.client.EnumerateInstances('OMC_RedundancySet')
    def getRedundancyStatus(self,index):
        return self.result[index]['RedundancyStatus']
    def getResult(self,index):
        result = { 'psRedundancy.1': self.getRedundancyStatus(1),
                   'fanRedundancy.1': self.getRedundancyStatus(0) }
        return result

class CIMTest2Poller(CIMBasePoller):
    def __init__(self,**kwargs):
        super(CIMTest2Poller,self).__init__(**kwargs)
        self.result = self.client.EnumerateInstances('VMware_HHRCStorageVolume')
        self.assoc = self.client.Associators(self.result[0].path,ClassName='VMware_HHRCAllocatedFromStoragePool')
    def run(self):
        print self.assoc

class CIMRecordLog(CIMBasePoller):
    def __init__(self,**kwargs):
        super(CIMRecordLog,self).__init__(**kwargs)
        self.result = self.client.EnumerateInstances('CIM_RecordLog')
    def getMaxNumberOfRecords(self,index):
        return self.result[index]['MaxNumberOfRecords']
    def getCurrentNumberOfRecords(self,index):
        return self.result[index]['CurrentNumberOfRecords']
    def getResult(self,index):
        return { 'selMaxRecords.%s' % str(index+1): self.getMaxNumberOfRecords(index),
                 'selCurrentRecords.%s' % str(index+1): self.getCurrentNumberOfRecords(index) }

SERVERMODEL = { 'PE1950':   {   'CIMPowerSupplyPoller':             [CIMPowerSupplyPoller,2],
                                'CIMRedundancySetPoller':           [CIMRedundancySetPoller,1],
                                'CIMNumericSensorPoller':           [CIMNumericSensorPoller,1],
                                'CIMChassisPoller':                 [CIMChassisPoller,1],
                                'CIMProcessorPoller':               [CIMProcessorPoller,2],
                                'CIMRaidPoller':                    [CIMRaidPoller,1],
                                'CIMHardDiskPoller':                [CIMHardDiskPoller,2],
                                'CIMRaidControllerBatteryPoller':   [CIMRaidControllerBatteryPoller,1],
                                'CIMPhysicalMemoryPoller':          [CIMPhysicalMemoryPoller,8],
                                'CIMRecordLog':                     [CIMRecordLog,1] },
                'PE2950':   {   'CIMPowerSupplyPoller':             [CIMPowerSupplyPoller,2],
                                'CIMRedundancySetPoller':           [CIMRedundancySetPoller,1],
                                'CIMNumericSensorPoller':           [CIMNumericSensorPoller,1],
                                'CIMChassisPoller':                 [CIMChassisPoller,1],
                                'CIMProcessorPoller':               [CIMProcessorPoller,2],
                                'CIMRaidPoller':                    [CIMRaidPoller,1],
                                'CIMHardDiskPoller':                [CIMHardDiskPoller,6],
                                'CIMRaidControllerBatteryPoller':   [CIMRaidControllerBatteryPoller,1],
                                'CIMPhysicalMemoryPoller':          [CIMPhysicalMemoryPoller,8],
                                'CIMRecordLog':                     [CIMRecordLog,1] },
                'PER710':   {   'CIMPowerSupplyPoller':             [CIMPowerSupplyPoller,2],
                                'CIMRedundancySetPoller':           [CIMRedundancySetPoller,1],
                                'CIMNumericSensorPoller':           [CIMNumericSensorPoller,1],
                                'CIMChassisPoller':                 [CIMChassisPoller,1],
                                'CIMProcessorPoller':               [CIMProcessorPoller,2],
                                'CIMRaidPoller':                    [CIMRaidPoller,1],
                                'CIMHardDiskPoller':                [CIMHardDiskPoller,6],
                                'CIMRaidControllerBatteryPoller':   [CIMRaidControllerBatteryPoller,1],
                                'CIMPhysicalMemoryPoller':          [CIMPhysicalMemoryPoller,8],
                                'CIMRecordLog':                     [CIMRecordLog,1] },
                'PER720':   {   'CIMPowerSupplyPoller':             [CIMPowerSupplyPoller,2],
                                'CIMRedundancySetPoller':           [CIMRedundancySetPoller,1],
                                'CIMNumericSensorPoller':           [CIMNumericSensorPollerPER720,1],
                                'CIMChassisPoller':                 [CIMChassisPoller,1],
                                'CIMProcessorPoller':               [CIMProcessorPoller,2],
                                'CIMRaidPoller':                    [CIMRaidPoller,1],
                                'CIMHardDiskPoller':                [CIMHardDiskPoller,6],
                                'CIMRaidControllerBatteryPoller':   [CIMRaidControllerBatteryPoller,1],
                                'CIMPhysicalMemoryPoller':          [CIMPhysicalMemoryPoller,8],
                                'CIMRecordLog':                     [CIMRecordLog,1] }
              }

def main():
    parser = OptionParser(description="VMware CIM CLI tool to be used in Zabbix")
    parser.add_option("-s", "--server-type", dest="server", help="Type is one of PE1950, PE2950, PER710", metavar="server")
    parser.add_option("-i", "--ip-address", dest="ip", help="IP-address to VMware server", metavar="ip")
    parser.add_option("-z", "--zabbix-host", dest="host", help="Host in zabbix", metavar="host")
    (options, args) = parser.parse_args()
    try:
        ZABBIX_SERVER='127.0.0.1'
        CIM_USERNAME='user' # SET TO VMWARE USER WITH PERMISSIONS TO RETRIEVE MONITORING DATA
        CIM_PASSWORD='password' # PW TO USER
        CIM_IP=str(options.ip)
        polldict = SERVERMODEL[options.server]
        for pollobjectkey in polldict.keys():
            try:
                cim = polldict[pollobjectkey][0](server=CIM_IP,username=CIM_USERNAME,password=CIM_PASSWORD)
                cim.setZabbixInfo(zabbixserver=ZABBIX_SERVER,zabbixhost=options.host)
                cim.execute(polldict[pollobjectkey][1])
            except CIMError, ex:
                pass
        print 1
    except:
        print 0
        traceback.print_exc()

if __name__ == '__main__':
    main()
