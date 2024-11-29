#!/bin/bash

# Find and print broken symblic links under the directory "$1".

find "$1" -type l -exec ls -lh {} \; | awk '{print $9, $11}' |\
		 while read l f; do
		 	pushd $(dirname $l);
			if ! ls $f > /dev/null 2>&1; then
				echo "Broken: $l -> $f";
			fi
			popd;		 
		 done
