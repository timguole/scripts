#!/usr/bin/python

from datetime import date, timedelta
import logging
import sys
import os

# a global logger
logger = None

def setup_logging():
	global logger
	basedir = os.path.dirname(sys.argv[0])
	logfile = os.path.join(basedir, 'logname.log')
	FMT = '%(asctime)-15s %(levelname)-9s %(message)s'
	logging.basicConfig(filename=logfile, format=FMT, level=logging.INFO)
	logger = logging.getLogger('foobar')


def month_ago(d, n):
	''' Return a date object n months ago before d
		NOTE:
		 the target month may not have that many days
		 as the month in d.
	'''
	if n <= 0:
		return None
	td = timedelta(days=1)
	d1 = d.replace(day=1)
	for i in range(n):
		d1 = d1.replace(day=1)
		d1 = d1 - td
	return d1.replace(day=d.day)


if __name__ == '__main__':
	setup_logging()
	try:
		logger.info('start')

		t = date.today()
		for i in range(5, 12):
			old_date = month_ago(t, i)
			month = '{:0>#2d}'.format(old_date.month)

		old_date = month_ago(t, 4)
		od = old_date.replace(day=1)
	except Exception as e:
		logger.error(e)
		exit(1)
	finally:
		logger.info('stop')
	exit(0)

