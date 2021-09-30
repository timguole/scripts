#!/usr/bin/python3

import select
import socket
import time
import logging
import argparse

# Connect to server at startup, and connect to target only when there is
# data from server socket.

class CC:
	def __init__(self, server, server_port, target, target_port) :
		self.server = server
		self.server_port = server_port
		self.target = target
		self.target_port = target_port

	def __init_socket(self, host, port) :
		sock = None

		try :
			sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			sock.connect((host, port))
			logging.info('connect to {0}:{1}'.format(host, port))
		except socket.error as e :
			logging.error('Failed to init socket')
			logging.error(e)
			if socket != None:
				sock.close()
			sock = None

		return sock


	def run(self) :
		self.cs1 = self.__init_socket(self.server, self.server_port)
		self.cs1_fd = self.cs1.fileno()
		self.cs2 = None
		self.cs2_fd = -1
		self.epoll = select.epoll()
		self.epoll.register(self.cs1_fd, select.EPOLLIN)

		while True :
			try :
				res = self.epoll.poll(timeout=60)
				logging.debug('epoll timeout')
				logging.debug(res)
				# res is [(fd, events), ...]
				for r in res :
					fd = r[0]
					event = r[1]
					if fd == self.cs1_fd and event & select.EPOLLIN :
						if self.cs2 == None:
							logging.info('try to connect to target')
							self.cs2 = self.__init_socket(self.target, self.target_port)
							self.cs2_fd = self.cs2.fileno()
							self.epoll.register(self.cs2_fd, select.EPOLLIN)
						self.__read_write(self.cs1, self.cs2)
					elif fd == self.cs2_fd and event & select.EPOLLIN :
						self.__read_write(self.cs2, self.cs1)
					elif event & select.EPOLLHUP or event & select.EPOLLERR :
						break
			except Exception as e :
				logging.error(e)

	def __read_write(self, s1, s2):
		max_bytes = 8192
		try :
			data = s1.recv(max_bytes)
			if len(data) == 0:
				logging.info('close socket to target')
				self.cs2.close()
				self.cs2 = None
				self.epoll.unregister(self.cs2_fd)
				self.cs2_fd = -1
			s2.send(data)
		except socket.error as e :
			logging.error(e)

if __name__ == '__main__':
	ap = argparse.ArgumentParser(description = 'Connnect to two servers and exchange data ')
	ap.add_argument('--server-host', nargs=1, required=True)
	ap.add_argument('--server-port', nargs=1, required=True, type=int)
	ap.add_argument('--target-host', nargs=1, required=True)
	ap.add_argument('--target-port', nargs=1, required=True, type=int)
	arguments = ap.parse_args()
	h1 = arguments.server_host[0]	
	p1 = arguments.server_port[0]	
	h2 = arguments.target_host[0]	
	p2 = arguments.target_port[0]	

	cc = CC(h1, p1, h2, p2)
	cc.run()
