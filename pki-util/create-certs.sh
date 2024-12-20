#!/bin/bash

# There are two initial files:
#   * sign-request.cnf (edit this file as needed)
#   * openssl.cnf

# FIXME: edit variables below
ca_name=ca-$(date '+%Y%m%d');
country=''
org=''
common_name=''
svr_cert_name=''
days=3655

# Prepare working directory in current directory.
wd='work-dir';
rm -rf $wd;
mkdir $wd;
cp sign-request.cnf $wd;
pushd $wd;

# Create a new ca
openssl req -x509 -batch -newkey rsa:2048 -nodes -out ${ca_name}.crt \
	-keyout ${ca_name}.key -subj "/C=$country/O=$org/CN=$common_name" \
	-days $days

# Create a new certificate sign request
openssl req -newkey rsa:2048 -nodes -keyout ${svr_cert_name}.key \
	-out ${svr_cert_name}.csr -extensions v3_req -config sign-request.cnf 

# sign the new certificate
touch index.txt
openssl rand -hex -out serial 6
cp ../openssl.cnf ./
openssl ca -batch -notext -md sha256 -in ${svr_cert_name}.csr \
	-cert ${ca_name}.crt -keyfile ${ca_name}.key \
	-out ${svr_cert_name}.crt -config openssl.cnf
cat ${svr_cert_name}.key ${svr_cert_name}.crt > ${svr_cert_name}

popd;

cp $wd/${ca_name}.crt ./
cp $wd/${ca_name}.key ./
cp $wd/${svr_cert_name} ./
cp $wd/${svr_cert_name}.crt ./
cp $wd/${svr_cert_name}.key ./
cp $wd/${svr_cert_name}.csr ./
