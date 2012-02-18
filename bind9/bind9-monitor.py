#!/usr/bin/env python
'''
Created on Aug 16, 2011

Populate value_mapper with all the Sections/Items that is desired to monitor.
By design it seems like Bind only displays the monitored parameters that carries
non-null values, so this needs to be updated a while after the Bind server
has been running.

parse_stats() returns a key:value dictionary, together with UNAME it's easy to construct an
output suitable for zabbix_sender

sys.argv[1] could be the path to the Bind statistics file or hard coded in the STATS variable

@author: johan
'''

import os
import re
import sys

UNAME=os.uname()[1] # OR SET THIS MANUALLY
STATS="named.stats.txt"

value_mapper = {'Incoming Requests': { 'QUERY': 'incoming_req'},
                'Incoming Queries': { 'A': 'incoming_qr_a',
                                      'PTR': 'incoming_qr_ptr',
                                      'SOA': 'incoming_qr_soa',
                                      'AAAA': 'incoming_qr_aaaa',
                                      'MX': 'incoming_qr_mx',
                                      'SRV': 'incoming_qr_srv' },
                'Outgoing Queries': { 'A': 'outgoing_qr_a',
                                      'NS': 'outgoing_qr_ns',
                                      'PTR': 'outgoing_qr_ptr',
                                      'SOA': 'outgoing_qr_soa',
                                      'AAAA': 'outgoing_qr_aaaa',
                                      'MX': 'outgoing_qr_mx',
                                      'SRV': 'outgoing_qr_srv' }, 
                'Name Server Statistics': { 'IPv4_requests_received': 'ns_stats_req_ipv4',
                                            'TCP_requests_received': 'ns_stats_req_tcp', 
                                            'responses_sent': 'ns_stats_resp_sent',
                                            'queries_resulted_in_succesful_answer': 'ns_stats_qr_succcess',
                                            'queries_resulted_in_non_authoritative_answer': 'ns_stats_qr_nonauth',
                                            'queries_resulted_in_nxrrset': 'ns_stats_qr_nxrrset', 
                                            'queries_resulted_in_NXDOMAIN': 'ns_stats_qr_nxdomain',
                                            'queries_caused_recursion': 'ns_stats_qr_recursion',
                                            'duplicate_queries_received': 'ns_stats_qr_dups',
                                            'queries_resulted_in_SERVFAIL': 'ns_stats_servfail' }, 
                'Resolver Statistics': { 'IPv4_queries_sent': 'res_stats_ipv4_sent',
                                         'IPv4_responses_received': 'res_stats_ipv4_received',
                                         'NXDOMAIN_received': 'res_stats_nxdomain',
                                         'query_retries': 'res_stats_retries', 
                                         'query_timeouts': 'res_stats_timeouts', 
                                         'IPv4_NS_address_fetches': 'res_stats_ipv4_nsfetch', 
                                         'IPv6_NS_address_fetches': 'res_stats_ipv6_nsfetch', 
                                         'IPv6_NS_address_fetch_failed': 'res_stats_ipv6_nsfail', 
                                         'queries_with_RTT_<_10ms': 'res_stats_rtt_10ms',
                                         'queries_with_RTT_10-100ms': 'res_stats_rtt_100ms',
                                         'queries_with_RTT_100-500ms': 'res_stats_rtt_500ms', 
                                         'queries_with_RTT_500-800ms': 'res_stats_rtt_800ms', 
                                         'queries_with_RTT_800-1600ms': 'res_stats_rtt_1600ms'},
                'Cache DB RRsets': { 'A': 'cache_a',
                                     'NS': 'cache_ns',
                                     'CNAME': 'cache_cname', 
                                     'PTR': 'cache_ptr',
                                     'AAAA': 'cache_aaaa', 
                                     'DS': 'cache_ds', 
                                     'RRSIG': 'cache_rrsig',
                                     '!AAAA': 'cache_xcl_aaaa', 
                                     'NXDOMAIN': 'cache_nxdomain'},
                'Socket I/O Statistics': { 'UDP/IPv4_sockets_opened': 'socket_ipv4_udp_open',
                                           'UDP/IPv6_sockets_opened': 'socket_ipv6_udp_open',
                                           'TCP/IPv4_sockets_opened': 'socket_ipv4_tcp_open',
                                           'TCP/IPv6_sockets_opened': 'socket_ipv6_tcp_open',
                                           'UDP/IPv4_sockets_closed': 'socket_ipv4_udp_close',
                                           'TCP/IPv4_sockets_closed': 'socket_ipv4_tcp_close',
                                           'UDP/IPv4_connections_established': 'socket_ipv4_udp_established',
                                           'TCP/IPv4_connections_accepted': 'socket_ipv4_tcp_accepted'}
                }

def get_stats(fn):
    f = open(fn,'r')
    rl = f.read().splitlines()
    return rl

def get_key_name(section,item):
    value = None
    if value_mapper.has_key(section):
        if value_mapper[section].has_key(item):
            value = value_mapper[section][item]
    return value

def parse_stats(rl):
    section = None
    result = {}
    for line in rl:
        if line.startswith('++ '):
            section = re.sub('\+','',line).lstrip(' ').rstrip(' ')
        elif line.startswith(' ') and not section is None:
            item_row_array = re.sub('^\s+','',line).split(' ')
            item_name = "_".join(item_row_array[1::])
            item_value = item_row_array[0]
            zabbix_key = get_key_name(section,item_name)
            if not zabbix_key is None:
                result[zabbix_key] = item_value
    return result

if __name__ == '__main__':
    fn = None
    try:
        sys.argv[1]
    except:
        fn = STATS
    else:
        fn = sys.argv[1]
    rl = get_stats(fn)
    result = parse_stats(rl)
    for key in result.keys():
        print "%s %s %s" % (UNAME,key,result[key]) #PIPE TO ZABBIX SENDER