#!/usr/bin/python3
# A manager thread dynamically manages several worker threads
# If the workder does not exist, we create it.
# If the worker is idle for a long time, we remove it.
#
# Input: NAME TASK1 TASK2 ...
# e.g.: a 1 2 3 4

import threading
import time
import datetime

class Manager:
	def __init__(self):
		self.free_seconds = 10
		self._quit = False
		self.lock = threading.Lock()
		self.workers = {}
		self.thread = threading.Thread(target = self._loop)
		self.thread.start()


	def set_task(self, name, tasks):
		self.lock.acquire()
		try:
			wt = self.workers[name]
		except KeyError:
			print('New worker:' + name)
			wt = [Worker(name), datetime.datetime.now()]
			self.workers[name] = wt
		print('add tasks to ' + name)
		wt[1] = datetime.datetime.now()
		wt[0].set_tasks(tasks)
		self.lock.release()


	def quit(self):
		self._quit = True
		self.thread.join()
		print('Manager thread exited')


	def _loop(self):
		while True:
			if self._quit is True:
				for k in list(self.workers):
					self.workers[k][0].quit()
				return

			now = datetime.datetime.now()
			self.lock.acquire()
			for k in list(self.workers):
				w = self.workers[k][0]
				ft = now - self.workers[k][1]
				if ft.seconds > self.free_seconds \
						and w.is_busy() == False:
					w.quit()
					self.workers.pop(k)
					print('Remove worker: ' + k)
			self.lock.release()
			time.sleep(2)
		

class Worker:
	def __init__(self, name):
		self.name = name
		self.thread = threading.Thread(target = self._work_loop)
		self.condition_var = threading.Condition()
		self.tasks = []
		self._quit = False
		self._busy = False
		self.thread.start()


	def _work_loop(self):
		local_tasks = []
		while True:
			if self._quit == True:
				return
			with self.condition_var:
				if len(self.tasks) == 0:
					print(self.name + ': empty, going to wait')
					self._busy = False
					self.condition_var.wait()

				local_tasks = list(self.tasks)
				self.tasks.clear()

			for t in local_tasks:
				print(self.name + ': working ' + t)
				time.sleep(1)
			self._busy = False


	def set_tasks(self, tasks):
		with self.condition_var:
			self.tasks.extend(tasks)
			self._busy = True
			self.condition_var.notify()


	def is_busy(self):
		return self._busy


	def quit(self):
		self._quit = True
		with self.condition_var:
			self.condition_var.notify()
		self.thread.join()
		print(self.name + ': quit')


if __name__ == '__main__':
	m = Manager()
	while True:
		task = input('Enter worker name and tasks: ')
		l = task.split()
		if l[0] == 'quit':
			break
		m.set_task(l[0], l[1:])

	m.quit()
