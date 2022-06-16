#!/bin/bash

# command examples:
#	'nohup cmd & sleep 2; exit'
#	'sudo cmd; exit'
#	'echo password | sudo -S cmd; exit'

cat host-ip.txt | while read host; do
	ssh -t -t -n user@$host "cmd; exit"
done
