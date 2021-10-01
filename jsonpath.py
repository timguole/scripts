#!/usr/bin/python3

from shlex import shlex
import sys
import re
import io


class JSONPath:
	'''
	Split a path into path elements. The default elements seperator is
	slash (/)
	e.g.
		jp = JSONPath("/a/b/c")
		pl = list(jp.items()) # pl is ["a", "b", "c"]
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
		self.ready = True


	def items(self):
		'''
		This method returns a generator
		'''
		if not self.ready:
			self.__split()
		for e in self.elements:
			yield e


def get_object(obj, path):
	''' Get object from a loaded json document.

		obj: the loaded json document
		path: filesystem-path-like string to the sub-object.

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
		'''
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
	_find(obj, path, values)
	return values


def printerr(msg):
	print(msg, file=sys.stderr)


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
	except json.JSONDecodeError as e:
		printerr('Failed to decode the input')
		printerr(e)
		exit(1)
	jp = JSONPath(path_str, seperator)
	path_list = list(jp.items())
	if len(path_list) == 0:
		printerr('Invalid path')
		exit(1)
	v = get_object(jobject, path_list)
	print(v)

