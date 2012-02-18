#!/usr/bin/env python
'''
Created on 1 aug 2011

@author: Johan
'''

import subprocess
import urllib2

ini_file = "/path/to/haproxy-poller.ini"
proxy_url = 'http://url.to.haproxy.stats.page:8080/haproxy?stats;csv'

# SEE http://code.google.com/p/haproxy-docs/wiki/StatisticsMonitoring#CSV_format
output = (
          { "hap_proxy_name": False },
          { "hap_sv_name": False },
          { "hap_qcur": True },
          { "hap_qmax": True },
          { "hap_scur": True },
          { "hap_smax": True },
          { "hap_slim": False },
          { "hap_stot": True },
          { "hap_bin": True },
          { "hap_bout": True },
          { "hap_dreq": False },
          { "hap_dresp": False },
          { "hap_ereq": False },
          { "hap_econ": False },
          { "hap_eresp": False },
          { "hap_wretr": False },
          { "hap_wredis": False },
          { "hap_status": True },
          { "hap_weight": False },
          { "hap_act": False },
          { "hap_bck": False },
          { "hap_chkfail": False },
          { "hap_chkdown": False },
          { "hap_lastchg": False },
          { "hap_downtime": False },
          { "hap_qlimit": False },
          { "hap_pid": False },
          { "hap_iid": False },
          { "hap_sid": False },
          { "hap_throttle": False },
          { "hap_lbtot": False },
          { "hap_tracked": False },
          { "hap_type": False },
          { "hap_rate": False },
          { "hap_rate_lim": False },
          { "hap_rate_max": False }, {"Null": False } )
"""
These are not supported in the version of HAProxy in Ubuntu LTS 10.04
{ "hap_check_status": True },
{ "hap_check_code": True },
{ "hap_check_duration": True },
{ "hap_hrsp_1xx": True },
{ "hap_hrsp_2xx": True },
{ "hap_hrsp_3xx": True },
{ "hap_hrsp_4xx": True },
{ "hap_hrsp_5xx": True },
{ "hap_hrsp_other": True },
{ "hap_hanafail": False },
{ "hap_req_rate": False },
{ "hap_req_rate_max": False },
{ "hap_req_tot": False },
{ "hap_cli_abrt": False },
{ "hap_srv_abrt": False }
)
"""

def parse_ini(i=ini_file):
    d = {}
    for line in open(i,'r'):
        (key,value) = line.split(':')
        d[key.rstrip('\r\n')] = value.rstrip('\r\n')
    return d

def poll(p=proxy_url):
    u = urllib2.urlopen(p)
    return u.read()

def get_result(d):
    csv_split = []
    rd = {}
    for r in d.splitlines():
        csv_split = r.split(',')
        rd["%s,%s" % (csv_split[0],csv_split[1])] = csv_split
    return rd

def push_result(r,d,filename="/tmp/haproxy_zabbixsend"):
    def get_output_key(index):
        return index.keys()[0]
    server = ""
    input_text = []
    for k in r.keys():
        if d.has_key(k):
            server = d[k]
            for i in range(0,len(r[k])):
                key = get_output_key(output[i])
                if output[i][key] is True:
                    input_text.append("%s %s %s\n" % (server,key,r[k][i]))
    #zabbix_send_string = "\r\n".join(input_text)
    f = open(filename,'w')
    f.writelines(input_text)
    f.close()
    return filename

def zabbixSend(filename,dryrun=False):
    if dryrun is True:
        for k in data.keys():
            print "%s: %s" % (k,data[k])
    else:
        p = subprocess.Popen(['/usr/bin/zabbix_sender',
                              '-z', '127.0.0.1',
                              '-p', '10051',
                              '-i', filename], stdout=subprocess.PIPE, shell=False).communicate()

if __name__ == '__main__':
    settings = parse_ini()
    data = poll()
    result = get_result(data)
    filename = push_result(result,settings)
    zabbixSend(filename)

