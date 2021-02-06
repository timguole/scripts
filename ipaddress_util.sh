#!/bin/bash

# Convert an IPv4 address to an integer
# e.g.
#	1.1.1.1 => 16843009
#
# $1: an IPv4 address
function ip2i() {
	if ! echo "$1" | grep -Eq '^((0|[1-9][0-9]{0,2})\.){3}(0|[1-9][0-9]{0,2})$'; then
		return 1;
	fi
	echo "$1" | awk -F'.' '{print $1, $2, $3, $4;}' \
			| while read q1 q2 q3 q4; do
		# The first part of an IPv4 address in a dotted-quad format is
		# between 1 and 255
		if [[ q1 -lt 1 || q1 -gt 255 \
				|| q2 -lt 0 || q2 -gt 255 \
				|| q3 -lt 0 || q3 -gt 255 \
				|| q4 -lt 0 || q4 -gt 255 ]]; then
			return 1;
		fi
		echo $(( (q1 << 24) + (q2 << 16) + (q3 << 8) + q4));
	done
}

# Convert an integer to an IPv4 address
# e.g.
#	16843009 => 1.1.1.1
#
# $1: an integer
function i2ip() {
	if ! echo "$1" | grep -Eq '^[0-9]+$'; then
		reeturn 1;
	fi
	if [[ $(( $1 > 0xffffffff)) -eq 1 ]]; then
		return 1;
	fi
	local q1=$(( ($1 & 0xff000000) >> 24 ));
	local q2=$(( ($1 & 0x00ff0000) >> 16 ));
	local q3=$(( ($1 & 0x0000ff00) >> 8 ));
	local q4=$(( $1 & 0x000000ff ));
	echo ${q1}.${q2}.${q3}.${q4};
}

# Test if an IPv4 netmask is valid or not
# return 0, if the netmask is a valid IPv4 netmask
#
# $1: an IPv4 netmask
function validate_netmask() {
	local i=$(ip2i "$1");
	if [[ -z "$i" ]]; then
		return 1;
	fi
	for e in $(seq 0 31); do
		m=$((0xffffffff - (2 ** e) + 1 ));
		if [[ $m -eq $i ]]; then
			return 0;
		fi
	done
	return 1;
}

# Convert a dotted-quad netmask to a prefix length
# e.g.
#	255.255.255.0 => 24
# $1: an IPv4 netmask in dotted-quad format
function dot2len() {
	local i=$(ip2i "$1");
	if [[ -z "$i" ]]; then
		return 1;
	fi
	for e in $(seq 0 31); do
		m=$((0xffffffff - (2 ** e) + 1 ));
		if [[ $m -eq $i ]]; then
			echo $((32 - e));
			return 0;
		fi
	done
	return 1;
}

# Convert a prefix length to a dotted-quad netmask
# e.g.
#	24 => 255.255.255.0
# $1: an IPv4 netmask prefix length
function len2dot() {
	if [[ "$1" -lt 1 || "$1" -gt 32 ]]; then
		return 1;
	fi

	m=$((0xffffffff - (2 ** (32 - $1)) + 1 ));
	echo $(i2ip $m);
}

# Output the netwok of a pair of IPv4 address and netmask
# e.g.
#	1.1.1.1 255.0.0.0 => 1.0.0.0
#
# $1: an IPv4 address
# $2: an IPv4 netmask
function get_network() {
	local iaddress=$(ip2i $1);
	if [[ -z "$iaddress" ]]; then
		return 1;
	fi
	
	if validate_netmask $2; then
		local inetmask=$(ip2i $2);
	fi

	local inetwork=$(( iaddress & inetmask));
	echo $(i2ip $inetwork);
}

# Generate a range of IPv4 addresses
# e.g.
#	192.168.1.1 192.168.1.5 255.255.255.0
# will generate the following IP addresses:
#	192.168.1.1
#	192.168.1.2
#	192.168.1.3
#	192.168.1.4
#	192.168.1.5
#
# $1: the first IPv4 address of a range
# $2: the last IPv4 address of a range
# $3: an IPv4 netmask
function ipgen() {
	if ! validate_netmask $3; then
		return 1;
	fi

	local first_int=$(ip2i $1);
	local last_int=$(ip2i $2);
	local mask=$(ip2i $3);

	if [[ -z "$first_int" || -z "$last_int" || -z "$mask" ]]; then
		return 1;
	fi

	if [[ $((first_int & mask)) -ne $((last_int & mask)) ]]; then
		return 1;
	fi

	for ((i=$first_int; $((i <= last_int)); $((i++)) )); do
		echo $(i2ip $i);
	done
}

