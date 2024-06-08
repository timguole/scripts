#!/usr/bin/python3

# process dependencies.
# Input format:
# 	Node: DEPENDENCY ...
# e.g.:
#	a:
#	b: a
#	c: a b
#	d: c b

import sys
import pprint

nodes = {}
stack = []
done = []

for line in open(sys.argv[1]):
	nd = line.split(':')
	node = nd[0].strip()
	dep = nd[1].split()
	if len(node) == 0:
		raise Exception('invalid node name: ' + l)
	nodes[node] = dep

pprint.pp(nodes)

for k in nodes.keys():
	stack.append(k)
	while len(stack) > 0:
		n = stack[-1]
		if n in done:
			stack.pop()
			continue
		try:	
			d = nodes[n]
		except KeyError:
			raise Exception('node does not exist: ' + n)
		if len(d) == 0:
			print('Do: ', n)
			done.append(n)
			stack.pop()
		else:
			# If the current node has 'not-done' dependencies,
			# push them into stack and remove 'done' dependencies from
   			# the node.
			_d = list()
			for i in d:
				if i not in done:
					_d.append(i)
					stack.append(i)
			assert(len(stack) <= len(nodes))
			nodes[n] = _d

assert(len(done) == len(nodes))
