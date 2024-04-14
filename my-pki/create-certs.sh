#!/bin/bash

# There are two initial files:
#   - my-server-cert.req
#   - openssl.cnf

# The new CA cert name
ca_name=my-ca-$(date '+%Y%m%d');
country=CN
organization=MYSELF
common_name=MY_SERVER
ca_life=3650

# The server cert name
cert_name=my-server-cert

# Prepare working dir
wd='work-dir';
if [[ -d "$wd" ]]; then
	rm -rf $wd;
fi
mkdir $wd;
cp my-server-cert.req $wd;
pushd $wd;

# Create a new ca
openssl req -x509 -batch -newkey rsa:2048 -nodes -out ${ca_name}.crt \
	-keyout ${ca_name}.key \
	-subj "/C=$country/O=$organization/CN=$common_name" \
	-days $ca_life

# Create a new certificate sign request
openssl req -newkey rsa:2048 -nodes -keyout ${cert_name}.key \
	-out ${cert_name}.csr -extensions v3_req -config ${cert_name}.req 

# sign the new certificate
touch index.txt
openssl rand -hex -out serial 6
cp ../openssl.cnf ./
openssl ca -batch -notext -md sha256 -in ${cert_name}.csr \
	-cert ${ca_name}.crt -keyfile ${ca_name}.key \
	-out ${cert_name}.crt -config openssl.cnf
cat ${cert_name}.key ${cert_name}.crt > ${cert_name}

popd;

echo New CA cert: $wd/$ca_name.crt
echo New CA key: $wd/$ca_name.key
echo New server cert: $wd/$cert_name.crt
echo New server key: $wd/$cert_name.key
echo "New server pkcs#12: $wd/$cert_name"
