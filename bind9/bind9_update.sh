#!/bin/sh
# Sample cron job - put on the Bind servers
# These settings are default for Ubuntu/Debian

RNDC=/usr/sbin/rndc
BIND9MON=/path/to/bind9-monitor.py # <- set this
ZABBIXSEND=/usr/bin/zabbix_sender
CONFIG=/var/cache/bind/named.stats
ZABBIXHOST=your-zabbix-nms # <- set this

[ -e $CONFIG ] && rm $CONFIG

$RNDC stats
$BIND9MON $CONFIG | $ZABBIXSEND -z $ZABBIXHOST -i -
