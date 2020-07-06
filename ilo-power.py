#!/usr/bin/python3
# Power on/off/reset HPE server

import sys
import argparse
import pexpect

ps1 = r'</.*iLO->'

def check_status(child):
	if b'status=0' not in child.before:
		print(child.before.decode(encoding='UTF8'))


def feed_password(child, password):
	while True:
		i = child.expect([r'\(yes/no\)\? ', r'assword: '])
		if i == 0:
			child.sendline("yes")
		elif i == 1:
			child.sendline(password)
			break
		else:
			print('Login error')


if __name__ == '__main__':
	ap = argparse.ArgumentParser(description = 'Power on/off server')
	ap.add_argument('--user', metavar='<ilo-user>', required=True)
	ap.add_argument('--password', metavar='<ilo-password>', required=True)
	ap.add_argument('--power', choices=['on', 'off', 'reset'], \
			nargs=1, required=True)
	ap.add_argument('--ilo', nargs='+', required=True)
	arguments = ap.parse_args()
	action = arguments.power[0]
	user = arguments.user[0]
	password = arguments.password[0]

	for ilo_ip in arguments.ilo:
		print(f"Power {action} server {ilo_ip}")
		child = pexpect.spawn(f'ssh -c aes256-cbc {user}@{ilo_ip}')
		feed_password(child, password)
		child.expect(ps1)
		child.sendline("power " + action)
		child.expect(ps1)
		check_status(child)
		child.sendline("exit")
		child.expect(pexpect.EOF)
