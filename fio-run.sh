#!/bin/bash
# HOwTO
# 1, make sure fio is installed
# 2, copy this script intto the mountpoint dir or sub-dir of the device you want to test.
# 3, run the script
# 4, wait and collect all result files (*.txt)
 
DIO=1;
FILE_DIR=tmp;
DATA_SIZE=10G;
NO_FILE=10;

cd $(dirname $0);
mkdir tmp;

fio --output=seqread.txt -directory=$FILE_DIR -direct=$DIO \
	-name=seqread \
	-description='Sequential Read' \
	-size=$DATA_SIZE \
	-nrfiles=$NO_FILE \
	-readwrite=read

fio --output=seqwrite.txt -directory=$FILE_DIR -direct=$DIO \
	-name=seqwrite \
	-description='Sequential Write' \
	-size=$DATA_SIZE \
	-nrfiles=$NO_FILE \
	-readwrite=write

fio --output=randread.txt -directory=$FILE_DIR -direct=$DIO \
	-name=randread \
	-description='Random Read' \
	-size=$DATA_SIZE \
	-nrfiles=$NO_FILE \
	-readwrite=randread

fio --output=randwrite.txt -directory=$FILE_DIR -direct=$DIO \
	-name=randwrite \
	-description='Random Write' \
	-size=$DATA_SIZE \
	-nrfiles=$NO_FILE \
	-readwrite=randwrite

fio --output=randrw.txt -directory=$FILE_DIR -direct=$DIO \
	-name=randrw \
	-description='Random Read/Write' \
	-size=$DATA_SIZE \
	-nrfiles=$NO_FILE \
	-readwrite=randrw

rm -rf $FILE_DIR;
echo; echo; echo;
echo "IO performance test done";
