#!/bin/bash

if [[ -z "$1" ]]; then
	echo "Usage: $0 <system-list>";
    echo;
    echo "system-list format is :";
    echo "<hostname> <pxe-ip> <pxe-mac> <optional-other-mac>";
	exit 1;
fi

messages_log='/var/log/messages';
http_access_log='/var/log/httpd/access_log';

cat $1 | while read name pxe_ip pxe_mac other_mac; do
    pxe_mac=$(echo $pxe_mac | tr '[:upper:]' '[:lower:]');
    other_mac=$(echo $other_mac | tr '[:upper:]' '[:lower:]');
	cblr_sys=$(cobbler system find --name $name);
	if [[ "$?" != 0 ]]; then
		echo Cobbler error >&2;
		exit 1;
	fi

	if [[ -z "$cblr_sys" ]]; then
		echo $name not found in cobbler;
		continue;
	fi

	# If netboot is false, the installation is already completed
	netboot=$(cobbler system report --name $name | grep Netboot | awk '{print $NF}');
	if [[ "$netboot" == False ]]; then
		continue;
	fi

	if ! grep -qE "DHCPDISC.*${pxe_mac}.*" $messages_log; then
		for m in $other_mac; do
			if grep -qE "DHCPDISC.*${m}.*" $messages_log; then
				echo $name wrong mac;
				wrong_mac='true';
				break;
			fi
		done

		if [[ "$wrong_mac" != 'true' ]]; then
			echo $name no dhcp request;
		fi
		continue;
	fi

	if ! grep -qE "tftp.*${pxe_ip}" $messages_log; then
		echo $name no tftp request;
		continue;
	fi

	if ! grep -qE "tftp.*${pxe_ip}.*initrd" $messages_log; then
		echo $name tftp not finished;
		continue;
	fi

	if ! grep -qE "$pxe_ip" $http_access_log; then
		echo $name no http request;
		continue;
	fi
done

