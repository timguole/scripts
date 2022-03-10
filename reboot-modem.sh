#!/bin/bash

cookie='/tmp/cookie.txt';
login='/tmp/login.json';
html='/tmp/reset.html';
r='http://192.168.1.1';

echo $$ > /home/gle/bar.pid;

while true; do
	echo > $login;
	echo > $cookie;
	echo > $html;

	if [[ $(date '+%H') = '04' ]]; then
		echo quit rebooting loop at $(date);
		break;
	fi

	echo reboot router at $(date);
	curl -s -c $cookie -o $login $r'/fh_post_login.ajax?commonName=dXNlcg==&commonPs=MTIzNDU2' 

	if ! grep -qF '"ret":"0"' $login; then
		echo login failed;
		sleep 120;
		continue;
	else
		echo login ok;
	fi

	curl -s -b $cookie -o $html $r'/resetrouter.html' 
	sk=$(cat $html | grep -E 'var sessionKey=.*' | grep -oE '[0-9]+')
	echo sessionKey is $sk;
	curl -s -b $cookie -o /dev/null $r'/rebootinfo.cgi?sessionKey='$sk;

	interval=$(( RANDOM % 420 + 180));
	echo sleep $interval seconds;
	sleep $interval;
done > /home/gle/foo.log 2>&1;
