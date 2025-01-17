#!/usr/bin/python3
''' Monitor servers' status via iLO.

The program reads settings in 'servers.cfg' under current directory and
fetch server rollup status via iLO restful API.

Format of servers.cfg
[iLO]
username=
password=

[servers]
ip1
ip2
...
'''

from ilo import iLO
import sys
import configparser
import signal
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed


fmt_str = '{:>15}{:>10}{:>7}{:>11}'

def fetch_status(iloip, username, password):
	ilo_host = 'https://' + iloip
	i = iLO(ilo_host, username, password)
	try:
		i.login()
		my_status = i.get_system(iLO.SYSTEM_HEALTH)
		my_power = i.get_system(iLO.POWER_STATE)
		my_auto_on = i.get_system(iLO.POWER_AUTO_ON)
		r = fmt_str.format(iloip, my_status[0], my_power[0], my_auto_on[0])
	except Exception as e:
		raise e
	finally:
		i.logout()
	return r


if __name__ == '__main__':
	def ki_handler(signum, stack_frame):
		exit(0)
	signal.signal(signal.SIGINT, ki_handler)

	config = configparser.ConfigParser()
	try:
		config.read_file(open('servers.cfg'))
	except Exception:
		print('Failed to open config file', file=sys.stderr)
		exit(1)

	ilo_user = config.get('iLO', 'username')
	ilo_pass = config.get('iLO', 'password')
	results = []

	with ThreadPoolExecutor(max_workers=32) as pe:
		# create a dict to hold all futures by list comprehension
		# then wait for all futures to finish and return result
		task_futures = {pe.submit(fetch_status, my_ip, ilo_user, ilo_pass): my_ip \
				for my_ip in config.options('servers')}
		try:
			for tf in as_completed(task_futures, timeout=15):
				iloip = task_futures[tf]
				try:
					results.append(tf.result())
				except Exception as e:
					print('Exception on', iloipe, e, file=sys.stderr)
					results.append(fmt_str.format(iloip, 'N/A', 'N/A', 'N/A'))
		except Exception as e:
			print(e, file=sys.stderr)

	results.sort()
	print(fmt_str.format('Server_IP', 'Health', 'Power', 'AutoOn'))
	for i in results:
		print(i)

	exit(0)

