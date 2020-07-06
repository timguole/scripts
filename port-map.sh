#!/bin/bash
# Map local_ip:local_port to remote_host:remote_port
# Make sure that net.ipv4.ip_forward = 1

# If there is a new host, append it to the list and re-run this script.
# NOTE: local port must be in the range `port_range`
#
# Format: <remote_ip>:<remote_port>,<local_port>,<protocol>
# Each entry in the list is seperated by space
host_list=''

port_range=''; # Format: <start-port>:<end-port>
external_ip='' # DNAT address
local_ip='' # SNAT address
local_if='' # nic name
mark_magic=31415926
used_ports=`mktemp`;

# Get field value from a host entry.
# get_field <host> <field-number>
function get_field()
{
	local old_ifs="$IFS";
	IFS=':,';
	local _a=($1);
	IFS="$old_ifs";
	echo ${_a[$2]};
}

# Check port duplication
echo "Checking for port duplication ...";
for h in $host_list; do
	local_port=$(get_field $h 2);

	if grep -q -E "^$local_port\$" $used_ports; then
		echo "Error: duplicated map to local port $local_port";
		rm $used_ports;
		exit;
	else
		echo $local_port >> $used_ports;
	fi
done
rm $used_ports;

# Port map chains for nat table
iptables -t nat -N MAPPRE &> /dev/null;

# for TCP
if ! iptables -t nat -C PREROUTING -d $external_ip -p tcp -m multiport --dports $port_range -j MAPPRE &> /dev/null; then
	iptables -t nat -I PREROUTING -d $external_ip -p tcp -m multiport --dports $port_range -j MAPPRE;
fi

# for UDP
if ! iptables -t nat -C PREROUTING -d $external_ip -p udp -m multiport --dports $port_range -j MAPPRE &> /dev/null; then
	iptables -t nat -I PREROUTING -d $external_ip -p udp -m multiport --dports $port_range -j MAPPRE;
fi

if ! iptables -t nat -C POSTROUTING -o $local_if -m mark --mark $mark_magic -j SNAT --to-source $local_ip &> /dev/null; then
	iptables -t nat -I POSTROUTING -o $local_if -m mark --mark $mark_magic -j SNAT --to-source $local_ip;
fi

echo Flushing existing rules ...;
iptables -t nat -F MAPPRE;

echo Installing mapping rules ...;
for h in $host_list; do
	remote_host=$(get_field $h 0);
	remote_port=$(get_field $h 1);
	local_port=$(get_field $h 2);
	proto=$(get_field $h 3);

	if [ "$proto" == tcp ]; then
		iptables -t nat -A MAPPRE -d $external_ip -p tcp --dport $local_port -j MARK --set-mark $mark_magic
		iptables -t nat -A MAPPRE -d $external_ip -p tcp --dport $local_port -j DNAT --to-destination ${remote_host}:${remote_port};
	elif [ "$proto" == udp ]; then
		iptables -t nat -A MAPPRE -d $external_ip -p udp --dport $local_port -j MARK --set-mark $mark_magic
		iptables -t nat -A MAPPRE -d $external_ip -p udp --dport $local_port -j DNAT --to-destination ${remote_host}:${remote_port};
	else
		echo Unsupported protocol: $proto;
		continue;
	fi

	echo DNAT from $external_ip:$local_port to $remote_host:$remote_port, protocol is $proto;
done

iptables-save > /etc/sysconfig/iptables;

