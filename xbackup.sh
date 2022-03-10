#!/bin/bash
# The backup policy is:
#	- do a full backup on Sunday.
#	- if there is no previous backup, do a full backup even it is not Sun.
#	- else, do an incremental backup.

my_cnf=
username=
password=
base_dir=
log_dir=$base_dir/log;

today=$(date '+%Y%m%d');
today_log="$log_dir/$today.log";
yesterday=$(date -d '24 hours ago' '+%Y%m%d');
yesterday_dir=$(ls -d $base_dir/$yesterday-*);
weekday=$(date '+%a');

mkdir -p $log_dir;
touch $today_log;
exec > $today_log 2>&1

# determine the backup type
if [[ "$weekday" == Sun ]]; then
	backup_type=full;
elif [[ ! -d "$yesterday_dir" ]]; then
	backup_type=full;
else
	backup_type=incr;
fi

backup_dir=$base_dir/$today-$backup_type-$weekday;

date;
echo "DIR: $backup_dir";
mkdir -p $backup_dir;

if [[ $backup_type == 'full' ]]; then
	echo Making a full backup;
 	xtrabackup --user=$username --pass=$password --backup \
			--defaults-file=$my_cnf \
			--target-dir=$today_dir;
else
	echo Makeing an incremental backup;
 	xtrabackup --user=$username --pass=$password --backup \
			--defaults-file=$my_cnf \
			--target-dir=$today_dir \
			--incremental-basedir=$yesterday_dir;
fi

# clean old backup files
echo Old backup to be deleted:
find $base_dir -maxdepth 1 -mtime +30 -type d;

echo Deleting old backups
find $base_dir -maxdepth 1 -mtime +30 -type d -exec rm -rf {} \;

