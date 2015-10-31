#!/usr/bin/env python

import sys

class Leaf:

    def __init__(self, value, weight):
    
        self.value = value
        self.weight = weight
    
    def dump(self, n):
    
        print n, self.value

class Node:

    def __init__(self, leaf0, leaf1):
    
        if leaf0.weight < leaf1.weight:
            self.leaf0 = leaf0
            self.leaf1 = leaf1
        else:
            self.leaf1 = leaf0
            self.leaf0 = leaf1
        
        self.weight = leaf0.weight + leaf1.weight
    
    def dump(self, n = ""):
    
        if isinstance(self.leaf0, Leaf):
            self.leaf0.dump(n + "0")
            self.leaf1.dump(n + "1")
        else:
            self.leaf0.dump(n + "1")
            self.leaf1.dump(n + "0")

def sorted(count):

    values = []
    i = 0
    while i < 256:
        values.append((count[i], i))
        i += 1
    
    values = filter(lambda (n, i): n != 0, values)
    values.sort()
    
    nodes = map(lambda (n, i): Leaf(i, n), values)
    
    while len(nodes) > 1:
    
        n0 = nodes.pop(0)
        n1 = nodes.pop(0)
        node = Node(n0, n1)
        i = 0
        while i < len(nodes):
            if node.weight < nodes[i].weight:
                nodes.insert(i, node)
                break
            i += 1
        else:
            nodes.append(node)
    
    nodes[0].dump()

def encode(input_file, output_file):

    count = [0] * 256
    
    while True:
    
        ch = input_file.read(1)
        if not ch:
            break
        
        i = ord(ch)
        count[i] += 1
    
    sorted(count)


if __name__ == "__main__":

    args = sys.argv[1:]
    
    command = None
    input_file = sys.stdin
    output_file = sys.stdout
    
    try:
        command = args.pop(0)
        input_file = args.pop(0)
        output_file = args.pop(0)
    
    except IndexError:
    
        if not command:
            sys.stderr.write("Usage: %s --encode|--decode [<input file> <output file>]\n" % sys.argv[0])
            sys.exit(1)
    
    if input_file != sys.stdin:
        if input_file == "-":
            input_file = sys.stdin
        else:
            input_file = open(input_file, "rb")
    
    if output_file != sys.stdout:
        output_file = open(output_file, "wb")
    
    if command == "--encode":
        encode(input_file, output_file)
    else:
        decode(input_file, output_file)
    
    sys.exit()
