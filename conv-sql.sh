#!/bin/bash
# This script converts schema sql exported by PL/SQL Developer to MySQL
# syntax. This is not a general converter. It's just my own tool.

SRC_DIR=PATH-TO-EXPORTED-SQL-FILES;
DEST_DIR=PATH-TO-SAVE-MYSQL-SQL-FILES;

for sf in $SRC_DIR/*.tab; do
	echo Processing $sf;
	df=$DEST_DIR/$(basename $sf);
	iconv.exe -f GBK -t UTF-8 $sf > $df;

	# remove tablespace info
	sed -i -r -e '/^tablespace/,/  \);/d' $df;
	sed -i -r -e '/^  tablespace/,/  \);/d' $df;

	# preprecess comment
	# if the comment string is splited in multiple lines, join it first.
	sed -i -r -e ':a { /^  is.*[^;]$/N; s/\n//; ta}' $df

	# join comment statement
	sed -i -r -e '/^comment on /N; s/\n//' $df;
	col_cmt="$(grep '^comment on column' $df)";
	tab_cmt="$(grep '^comment on table' $df)";
	sed -i -r -e '/^comment on/d' $df;

	# process column comment
	echo "$col_cmt" | while read l; do
		if [[ -z "$l" ]]; then
			continue;
		fi
		cn=$(echo $l | cut -d ' ' -f 4 | cut -d'.' -f 3);
		cm=$(echo $l | cut -d ' ' -f '6-' | tr -d ';');
		sed -i -r -e "/$cn/s/,*$/ comment $cm,/" $df;
	done

	# process table comment
	echo "$tab_cmt" | while read l; do
		if [[ -z "$l" ]]; then
			continue;
		fi
		tn=$(echo $l | cut -d ' ' -f 4 | cut -d'.' -f 2);
		cm=$(echo $l | cut -d ' ' -f '6-' | tr -d ';');
		sed -i -r -e "/\)\$/s/\$/ comment = $cm;/" $df;
	done

	# process data types
	sed -i -r -e 's/ VARCHAR2/VARCHAR/' \
			-e 's/ INTEGER/BIGINT/' \
			-e 's/ NUMBER\([0-9,]+\)/BIGINT/' \
			-e 's/ NUMBER( |$)/BIGINT/' \
			$df;

	# process alter table primary key
	sed -i -r -e '/^alter table/N; s/\n//' $df;
	pk=$(grep -Eo 'primary key \(.+\)' $df);
	sed -i -r -e "/^\\)/i\  $pk" \
			-e '/^alter table.*add constraint.*primary key/d' \
			$df
done
