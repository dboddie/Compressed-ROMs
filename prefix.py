#!/usr/bin/env python

import pprint, sys

class Leaf:

    def __init__(self, value, weight):
    
        self.value = value
        self.weight = weight
    
    def dump(self, n):
    
        print n, self.value
    
    def serialise(self, n, encdict, node_array, bits):
    
        encdict[self.value] = (n, bits)
        node_array += [-self.value]

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
    
    def serialise(self, n, encdict, node_array, bits = 0):
    
        i = len(node_array)
        
        # Add an entry to be filled in later.
        node_array += [0]
        
        v0 = n
        v1 = n | (1 << bits)
        
        if isinstance(self.leaf0, Leaf):
            self.leaf0.serialise(v0, encdict, node_array, bits + 1)
            # Fill in the offset that points to the second leaf or node.
            node_array[i] = len(node_array) - i
            self.leaf1.serialise(v1, encdict, node_array, bits + 1)
        else:
            self.leaf1.serialise(v0, encdict, node_array, bits + 1)
            # Fill in the offset that points to the second leaf or node.
            node_array[i] = len(node_array) - i
            self.leaf0.serialise(v1, encdict, node_array, bits + 1)

def sorted(count):

    values = []
    i = 0
    while i < 256:
        values.append((count[i], i))
        i += 1
    
    # Discard values that didn't occur.
    values = filter(lambda (n, i): n != 0, values)
    # Sort the values in increasing order of frequency.
    values.sort()
    
    nodes = map(lambda (n, i): Leaf(i, n), values)
    total = len(nodes)
    
    while len(nodes) > 1:
    
        n0 = nodes.pop(0)
        n1 = nodes.pop(0)
        node = Node(n0, n1)
        total += 1
        i = 0
        while i < len(nodes):
            if node.weight < nodes[i].weight:
                nodes.insert(i, node)
                break
            i += 1
        else:
            nodes.append(node)
    
    encdict = {}
    node_array = []
    nodes[0].serialise(0, encdict, node_array)
    
    print len(node_array)
    print min(node_array), max(node_array), total
    
    return encdict, node_array

def encode(input_file, output_file):

    count = [0] * 256
    data = []
    
    while True:
    
        ch = input_file.read(1)
        if not ch:
            break
        
        i = ord(ch)
        count[i] += 1
        data.append(i)
    
    encdict, node_array = sorted(count)
    
    bit = 0
    c = 0
    output_data = []
    
    for i in data:
    
        v, l = encdict[i]
        while l > 0:
            c = c | ((v & 1) << bit)
            v = v >> 1
            l -= 1
            bit += 1
            if bit == 8:
                output_file.write(chr(c))
                output_data.append(c)
                bit = 0
                c = 0
    
    if bit != 0:
        output_file.write(chr(c))
        output_data.append(c)
    
    # Decode to test.
    decode_(output_data, node_array, data, len(data))

def decode_(input_data, node_array, expected_output, size = 32768):

    bit = 0
    c = 0
    data = []
    offset = 0
    i = 0
    
    while len(data) < size:
    
        if bit == 0:
            c = input_data[i]
            i += 1
        
        if c & 1 == 0:
            offset += 1
        else:
            offset += node_array[offset]
        
        if node_array[offset] <= 0:
            data.append(-node_array[offset])
            if data[-1] != expected_output[len(data)-1]:
                sys.stderr.write("Decoding check failed at offset %x.\n" % (len(data)-1))
                sys.exit(1)
            offset = 0
        
        c = c >> 1
        bit = (bit + 1) % 8
    
    return data

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
