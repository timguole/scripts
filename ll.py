#!/usr/bin/python3

import select
import socket
import time
import logging
import argparse

class LL:
	"""The core for socket, multi-threading and Async I/O."""
	def __init__(self, host1, port1, host2, port2) :
		self.host1 = host1
		self.port1 = port1
		self.host2 = host2
		self.port2 = port2


	def __init_socket(self, host, port) :
		sock = None

		try :
			sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			sock.bind((host, port))
			logging.info('Bind to {0}:{1}'.format(host, port))
			sock.listen(5)
		except socket.error as e :
			logging.error('Failed to init socket')
			logging.error(e)
			if socket != None:
				sock.close()
			sock = None

		return sock


	def run(self) :
		self.ss1 = self.__init_socket(self.host1, self.port1)
		self.ss2 = self.__init_socket(self.host2, self.port2)
		self.ss1_fd = self.ss1.fileno()
		self.ss2_fd = self.ss2.fileno()
		self.cs1 = None
		self.cs2 = None
		self.cs1_fd = -1
		self.cs2_fd = -1
		self.epoll = select.epoll()
		self.epoll.register(self.ss1.fileno(), select.EPOLLIN)
		self.epoll.register(self.ss2.fileno(), select.EPOLLIN)

		while True :
			try :
				res = self.epoll.poll(timeout=10)
				logging.debug('epoll timeout')
				logging.debug(res)
				# res is [(fd, events), ...]
				for r in res :
					fd = r[0]
					event = r[1]
					if fd == self.ss1_fd and event & select.EPOLLIN :
						try :
							conn = self.ss1.accept()
						except socket.error as e :
							logging.error('socket 1 accept error')

						logging.info('client 1 connected')
						self.cs1 = conn[0]
						self.cs1_fd = conn[0].fileno()
						self.epoll.register(self.cs1_fd, select.EPOLLIN)
					elif fd == self.ss2_fd and event & select.EPOLLIN :
						try :
							conn = self.ss2.accept()
						except socket.error as e :
							logging.error('socket 2 accept error')

						logging.info('client 2 connected')
						self.cs2 = conn[0]
						self.cs2_fd = self.cs2.fileno()
						self.epoll.register(self.cs2_fd, select.EPOLLIN)
					elif fd == self.cs1_fd and event & select.EPOLLIN :
						self.__read_write(self.cs1, self.cs2)
					elif fd == self.cs2_fd and event & select.EPOLLIN :
						self.__read_write(self.cs2, self.cs1)
					elif event & select.EPOLLHUP or event & select.EPOLLERR :
						break
			except Exception as e :
				logging.error(e)

	def __read_write(self, s1, s2):
		if s1 == None or s2 == None:
			return
		max_bytes = 8192
		try :
			data = s1.recv(max_bytes)
			if len(data) == 0:
				logging.info('close client 1 socket')
				self.cs1.close()
				self.cs1 = None
				self.epoll.unregister(self.cs1_fd)
				self.cs1_fd = -1
			s2.send(data)
		except socket.error as e :
			logging.error(e)

if __name__ == '__main__':
	ap = argparse.ArgumentParser(description = 'Listen on two sockets and exchange data ')
	ap.add_argument('--host1', nargs=1, required=True)
	ap.add_argument('--port1', nargs=1, required=True, type=int)
	ap.add_argument('--host2', nargs=1, required=True)
	ap.add_argument('--port2', nargs=1, required=True, type=int)
	arguments = ap.parse_args()
	h1 = arguments.host1[0]	
	p1 = arguments.port1[0]	
	h2 = arguments.host2[0]	
	p2 = arguments.port2[0]	

	ll = LL(h1, p1, h2, p2)
	ll.run()
