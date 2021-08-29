#!/usr/bin/python3

from shlex import shlex
import re

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
	# Convert string into a list
	# e.g.
	# from '/a/b/c' to ['a', 'b', 'c']
	_s = shlex(path, posix=True, punctuation_chars='/*?')
	_s.worchars += '@'
	_l = list(_s)
	p = [element for element in _l if not re.match(r'^/+$', element)]
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
	_find(obj, p, values)
	return values


if __name__ == '__main__':
	import json
	import sys

	if len(sys.argv) == 1:
		print('Usage: {} <path> [<json-file>]'.format(sys.argv[0]))
		exit(1)

	json_file = sys.stdin
	if len(sys.argv) == 3:
		json_file = open(sys.argv[2])

	try:
		jobject = json.load(json_file)
	except json.JSONDecodeError as e:
		print('Failed to decode the input', file=sys.stderr)
		print(e, file=sys.stderr)
		exit(1)
	v = get_object(jobject, sys.argv[1])
	print(v)

