#!/usr/bin/python3
# Collect linux performance data via ssh

import sys
import re
import argparse
import pexpect


class SSHHost:
	def __init__(self, host, port, user, password):
		self.host = host
		self.port = port
		self.user = user
		self.password = password


	def __str__(self):
		return f'{self.user}/{self.password}@{self.host}:{self.port}'


class IncorrectPassword (Exception):
	def __init__(self, msg):
		super().__init__(f'Incorrect passwordfor {msg}')


class PasswordExpired(Exception):
	def __init__(self, msg):
		super().__init__(f'PasswordExpired for {msg}')


class NoSSH (Exception):
	def __init__(self, msg):
		super().__init__(f'NoSSH for {msg}')


def setup_login(sshhost, prompt, salted_prompt, salt):
	'''Establish ssh connection and set new bash prompt
		'''
	password_sent = False
	child = pexpect.spawn( \
			f'ssh {sshhost.user}@{sshhost.host} -p {sshhost.port}', \
			echo=False, timeout=5)
	while True:
		i = child.expect([ \
				r'\(yes/no\)\?', \
				r'assword:', \
				r'[$#]', \
				pexpect.TIMEOUT, \
				pexpect.EOF], \
				timeout=5)
		if i == 0:
			child.sendline("yes")
		elif i == 1:
			# If password has been sent and we get prompt for inputting
			# password again, the password is incorrect.
			if password_sent == True:
				raise IncorrectPassword(sshhost)
			child.sendline(sshhost.password)
			password_sent = True
		elif i == 2:
			# logged in
			break
		else:
			raise NoSSH(sshhost)

	child.sendline(f"PS1=$(echo {salted_prompt} | tr -d {salt})")
	child.expect(prompt)
	return child


# NOTE: Performance data collecting functins name MUST start with the 
# prefix 'f_perf_' and receive two arguments: child. prompt. The return
# value is a JSON-like string
# The pseudo-code:
#	def f_perf_XXX(child, prompt):
#		child.sendline('linux command here')
#		child.expect(prompt)
#		processing data
#		return data

def f_perf_mem(child, prompt):
	'''Collect memory info via `free`
		'''
	child.sendline("free -m | grep Mem | awk '{print $2, $4}'")
	child.expect(prompt)
	output = child.before.decode(encoding='UTF-8')
	m = output.splitlines()[0].strip('\r\n').split(' ')
	mu = int(m[0]) - int(m[1])
	mp = int(mu / int(m[0]) * 10000)
	return f"'memusage':'{mu}','mempercent':'{mp}'"


def f_perf_cpu(child, prompt):
	'''Collect CPU utilization via `top`
		'''
	child.sendline("top -bn1 | grep -E '^%?Cpu' | awk -F',' '{print $4;}' | tr '%' ' ' | awk '{print $1}'")
	child.expect(prompt)
	output = child.before.decode(encoding='UTF-8')
	idle = output.splitlines()[0].strip('\r\n')
	cu = int((100 - float(idle)) * 100)
	return f"'cpuutil':'{cu}'"


if __name__ == '__main__':
	ap = argparse.ArgumentParser(description = 'Collect performacne data')
	ap.add_argument('--user', metavar='<login-user>', required=True)
	ap.add_argument('--password', metavar='<login-password>', required=True)
	ap.add_argument('--host', metavar='<host name or ip>', required=True)
	ap.add_argument('--port', metavar='<ssh port>', required=True)
	arguments = ap.parse_args()
	host = arguments.host
	port = arguments.port
	user = arguments.user
	password = arguments.password
	sshhost = SSHHost(host, port, user, password)

	salt = '123'
	salted_prompt = 'foo123barz'
	prompt = salted_prompt.replace('123', '')
	gkeys = list(globals().keys())
	functions = [globals()[k] for k in gkeys if re.match(r'f_perf_.+', k)]
	perf_data = []

	try:
		child = setup_login(sshhost, prompt, salted_prompt, salt)
		for f in functions:
			perf_data.append(f(child, prompt))

		child.sendline("exit")
		child.expect(pexpect.EOF)
		print('{' + ','.join(perf_data) + '}')
		exit(0)
	except IncorrectPassword as e:
		print(e)
		exit(1)
	except NoSSH as e:
		print(e)
		exit(2)
	except Exception as e:
		print(e)
		exit(3)

