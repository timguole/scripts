#!/bin/bash

# Make sure that bin log is on in mysqld

# Uncomment the line below as needed
#exec 1>> /path/to/backup.log 2>&1;

db_username='';
db_password='';
backup_dir='';
timestamp=$(date '+%Y%m%d%H%M%S');
today_dir="$backup_dir/$timestamp";
week_day=$(date '+%w');

# the day performing a full backup
# the day is Sunday
full_day=0;

# the bin log index file
bin_index='';

# file contains the new bin log file name after flushing
bin_name='';

function full_backup() {
	mysqldump -u$db_username -p"$db_password" \
			-A -R --triggers --single-transaction \
			--master-data=2 \
			--flush-logs > $today_dir/alldb_${timestamp}.sql &
	sleep 60; # wait for flushing logs
	new_log=$(tail -n 1 $bin_index);
	echo $new_log >> $bin_name;
	wait -f; # wait for mysqldump job
	date;
	gzip $today_dir/*.sql
}

function incremental_backup() {
	mysql -u$db_username -p$db_password -e 'flush logs;';
	first_log=$(tail -n 1 $bin_name);
	last_log=$(tail -n 2 $bin_index | sed -n '1p');
	new_log=$(tail -n 1 $bin_index);
	echo $new_log >> $bin_name;
	for b in $(cat $bin_index | sed -n -e "\|$first_log|,\|$last_log|p"); do
		cp $b $today_dir/;
	done
}

date;
mkdir -p $today_dir;

if [[ "$week_day" -eq "$full_day" ]]; then
	echo Full backup;
	full_backup;
else
	echo Incremental backup;
	incremental_backup;
fi

# TODO: Add code to remove old backups
