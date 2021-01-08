#!/bin/bash

index_file='index.txt';
index_sign='index.txt.sig';
base_url='http://url/';

if curl --silent $base_url$index_file --output $index_file \
		$base_url$index_sign --output $index_sign; then
	echo Downloaded $index_file and $index_sign;
else
	echo Failed to downloaded $index_file and $index_sign;
	exit 1;
fi

if gpg --verify $index_sign $index_file; then
	echo Good signature for $index_file;
else
	echo Bad signature for $index_file;
	exit 1;
fi

cat $index_file | while read sum name; do
	if curl --silent $base_url$name --output $name; then
		echo Downloaded file: $name;
	else
		echo Failed to download file: $name;
		continue;
	fi
	new_sum=$(md5sum $name | awk '{print $1}');
	if [[ "$sum" == "$new_sum" ]]; then
		echo Good chechsum for $name: $new_sum;
		chmod u+x $name;
		#./$name;
	else
		echo Bad checksum for $name: $new_sum;
	fi
done
