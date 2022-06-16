#!/bin/bash

for host in $(cat host-ip.txt); do
	scp FILENAME user@$host:/path
done
