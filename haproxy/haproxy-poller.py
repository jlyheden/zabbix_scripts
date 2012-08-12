#!/usr/bin/env python
'''
Created on 1 aug 2011

Add in crontab like this:
*/1 * * * * zabbix /usr/local/bin/haproxy-poller.py /usr/local/etc/haproxy-poller.ini http://<proxy-ip>:<stats-port> <zabbix-server> <zabbix-port>

@author: Johan
'''

import subprocess
import urllib2
import sys
import os
import time
import re

tmp_path = "/tmp/haproxy-poller"

# http://code.google.com/p/haproxy-docs/wiki/StatisticsMonitoring#CSV_format
# Enable monitoring of specific keys by setting True as value
# Make sure to modify the haproxy template to reflect these items
def get_options(v):
    options = { "1.3": (
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
            { "hap_rate_max": False }, {"Null": False } ),
            "1.4": (
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
            { "hap_ereq": True },
            { "hap_econ": True },
            { "hap_eresp": True },
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
            { "hap_rate_max": False },
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
            { "hap_srv_abrt": False }, { "Null": False } )
    }
    return options[v[:3]]

def get_version(i,p):
    def get_version_from_html_stats(h):
        for l in h.splitlines():
            m = re.search("HAProxy version ([\d\.]+)",l)
            if m:
                return m.groups()[0]
    version_file = os.path.join(tmp_path,"%s.version" % i.replace("/","_").replace(".","_"))
    if not os.path.exists(tmp_path):
        os.mkdir(tmp_path)
    if not os.path.exists(version_file) or (time.time() - os.path.getmtime(version_file)) > 86400:
        version = get_version_from_html_stats(poll("%s/;html" % p))
        f = open(version_file,'w')
        f.write(version)
        f.close()
        return version
    else:
        f = open(version_file,'r')
        version = f.read()
        f.close()
        return version

def parse_ini(i):
    d = {}
    for line in open(i,'r'):
        if re.match("^[a-z0-9]",line):
            (key,value) = line.split(':')
            d[key.rstrip('\r\n')] = value.rstrip('\r\n')
    return d

def poll(p):
    u = urllib2.urlopen(p)
    return u.read()

def get_result(d):
    csv_split = []
    rd = {}
    for r in d.splitlines():
        csv_split = r.split(',')
        rd["%s,%s" % (csv_split[0],csv_split[1])] = csv_split
    return rd

def push_result(r,d,v,i):
    def get_output_key(index):
        return index.keys()[0]
    filename = os.path.join("/tmp", "%s.zabbixsend" % i.replace("/","_"))
    server = ""
    input_text = []
    for k in r.keys():
        if d.has_key(k):
            server = d[k]
            for i in range(0,len(r[k])):
                key = get_output_key(get_options(v)[i])
                if get_options(v)[i][key] is True:
                    input_text.append("%s %s %s\n" % (server,key,r[k][i]))
    #zabbix_send_string = "\r\n".join(input_text)
    f = open(filename,'w')
    f.writelines(input_text)
    f.close()
    return filename

def zabbixSend(filename,zabbix_server,zabbix_port,dryrun=False):
    if dryrun is True:
        for k in data.keys():
            print "%s: %s" % (k,data[k])
    else:
        p = subprocess.Popen(['/usr/bin/zabbix_sender',
                              '-z', zabbix_server,
                              '-p', zabbix_port,
                              '-i', filename], stdout=subprocess.PIPE, shell=False).communicate()

def usage():
    print "Usage: %s ini-file haproxy-url zabbix-server zabbix-port" % sys.argv[0]
    sys.exit(1)

def main():
    if len(sys.argv) < 4:
        usage()
    ini_file = sys.argv[1]
    haproxy_url = sys.argv[2]
    zabbix_server = sys.argv[3]
    zabbix_port = sys.argv[4]
    version = get_version(ini_file,haproxy_url)
    settings = parse_ini(ini_file)
    data = poll("%s/;csv" % haproxy_url)
    result = get_result(data)
    filename = push_result(result,settings,version,ini_file)
    zabbixSend(filename,zabbix_server,zabbix_port)

if __name__ == '__main__':
    main()
