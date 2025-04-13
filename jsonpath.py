#!/usr/bin/python3

from shlex import shlex
import sys
import io


class JSONPath:
	'''Find data in a json object
	Path starts with a `/` and each component in a path is either
	index of a list or key in a dict. `*` means all element in a list
	or all values in a dict. `?` means all keys in a dict or the
	length of a list. And `?` is only valid as the last component of
	a path.

	Path examples:
		"/a/b/c"
		"/a/*/c"
		"/a/21/c"
		"/a/?"
	e.g.
		import io
		import json
		jp = JSONPath("/a/b/c")
		sio = io.StringIO('{"{'foo': ['bar', 'zoo']}")
		data = jp.find(json.load(sio))
	'''
	def __init__(self, path, sep='/'):
		'''
		path: a string
		sep: the elements seperator character, the default is slash
		'''
		self.sio= io.StringIO(path)
		self.sep = sep
		self.elements = []
		self.ready = False


	def __getchar(self):
		self.curr = self.sio.read(1)
		return self.curr


	def __split(self):
		ele = ''
		self.elements = []
		while self.__getchar() != '':
			c = self.curr
			if c == self.sep:
				if ele != '':
					self.elements.append(ele)
					ele = ''
			elif c == '\\':
				ele += self.__getchar()
			else:
				ele += c
		if ele != '':
			self.elements.append(ele)
		if len(self.elements) == 0:
			raise ValueError('Empty path')
		self.ready = True


	def __parse(self):
		'''
		This method returns a generator
		'''
		if not self.ready:
			self.__split()


	def find(self, json_object):
		''' json_object: the loaded json document'''
		def _find(o, k, v):
			if isinstance(o, list):
				if len(k) == 1:
					if k[0] == '*':
						v.extend(o)
					elif k[0] == '?':
						v.append(len(o))
					else:
						v.append(o[int(k[0])])
				else: # there are still more than one path elements
					if k[0] == '*':
						for _o in o:
							_find(_o, k[1:], v)
					elif k[0] == '?':
						raise SyntaxError("'?' can only appear at the last")
					else:
						_find(o[int(k[0])], k[1:], v)
			elif isinstance(o, dict):
				if len(k) == 1:
					if k[0] == '*':
						for key, val in o.items():
							v.append(val)
					elif k[0] == '?':
						v.extend(o.keys())
					else:
						v.append(o[k[0]])
				else:
					if k[0] == '*':
						for key, val in o.items():
							_find(val, k[1:], v)
					elif k[0] == '?':
						raise SyntaxError("'?' can only appear at the last")
					else:
						_find(o[k[0]], k[1:], v)

		values = []
		self.__parse()
		_find(json_object, self.elements, values)
		return values


def printerr(msg):
	print('Error: ', msg, file=sys.stderr)


if __name__ == '__main__':
	import json
	import argparse

	ap = argparse.ArgumentParser(description='Get data from a JSON file.')
	ap.add_argument('-s', default='/',
			help='Path elements seperator, default is slash')
	ap.add_argument('-f', default='',
			help='Path to a JSON file, default is stdin')
	ap.add_argument('-p', required=True, help='a file-path-like string')
	args = ap.parse_args()
	seperator = args.s[0]
	path_str = args.p
	jf = args.f
	if len(jf) == 0:
		json_file = sys.stdin
	else:
		json_file = open(jf)

	try:
		jobject = json.load(json_file)
		jp = JSONPath(path_str, seperator)
		v = jp.find(jobject)
		print(v)
	except json.JSONDecodeError as e:
		printerr('Failed to decode the input')
		printerr(e)
		exit(1)
	except Exception as e:
		printerr('Failed to find value')
		printerr(e)
		exit(1)

