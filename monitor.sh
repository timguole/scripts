#!/bin/bash
# Generate test data for Grafana MySQL data source.
#
# The database table schema is:
#create table metrics(
#    ts datetime,
#    running int,
#    blocked int,
#    swapd bigint,
#    free bigint,
#    buffer bigint,
#    cache bigint,
#    swapin bigint,
#    swapout bigint,
#    blkin bigint,
#    blkout bigint,
#    irq bigint,
#    cswitch bigint,
#    cpuus int,
#    cpusys int,
#    cpuidle int,
#    cpuwait int,
#    cpusteal int
#);

source ./utils.sh

dbname='';
dbuser='';
dbpass='';
interval=''; # how many seconds

while true; do
	timestamp=$(date '+%Y-%m-%d %H:%M:%S');
	metrics=$(join_args ',' $(vmstat | sed -n '3p'));
	mysql -u$dbuser -p$dbpass $dbname \
		-e "insert into metrics values('$timestamp', $metrics);"
	sleep $interval;
done

