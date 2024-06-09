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

nodes = {}
stack = []
done = []

def dep_gen(d):
	for n in d:
		yield n


for line in open(sys.argv[1]):
	nd = line.split(':')
	node = nd[0].strip()
	if len(node) == 0:
		raise Exception('invalid node name: ' + l)
	dep = dep_gen(nd[1].split())
	nodes[node] = dep


for k in nodes.keys():
	stack.append(k)
	while len(stack) > 0:
		n = stack[-1]
		if n in done:
			stack.pop()
			continue
		try:	
			d = next(nodes[n])
			assert(d not in stack)
			stack.append(d)
			continue
		except KeyError as e:
			print('Non-exist node: ' + n)
			raise e
		except StopIteration as si:
			print('Do: ' + n)
			done.append(n)
			stack.pop()

assert(len(done) == len(nodes))
