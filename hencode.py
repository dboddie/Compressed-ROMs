#!/usr/bin/env python

import pprint, struct, sys

class DecodingError(Exception):
    pass

class Leaf:

    def __init__(self, value, weight):
    
        self.value = value
        self.weight = weight
    
    def dump(self, n):
    
        print n, self.value
    
    def serialise(self, n, encdict, node_array, type_array, bits = 1):
    
        encdict[self.value] = (n, bits)
        node_array += [self.value]
        # This node is a leaf.
        type_array += [1]

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
    
    def serialise(self, n, encdict, node_array, type_array, bits = 0):
    
        i = len(node_array)
        
        # Add an entry to be filled in later.
        node_array += [0]
        # This node is not a leaf.
        type_array += [0]
        
        v0 = n
        v1 = n | (1 << bits)
        
        if isinstance(self.leaf0, Leaf):
            self.leaf0.serialise(v0, encdict, node_array, type_array, bits + 1)
            # Fill in the offset that points to the second leaf or node.
            node_array[i] = len(node_array) - i - 1
            self.leaf1.serialise(v1, encdict, node_array, type_array, bits + 1)
        else:
            self.leaf1.serialise(v0, encdict, node_array, type_array, bits + 1)
            # Fill in the offset that points to the second leaf or node.
            node_array[i] = len(node_array) - i - 1
            self.leaf0.serialise(v1, encdict, node_array, type_array, bits + 1)

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
    type_array = []
    nodes[0].serialise(0, encdict, node_array, type_array)
    
    return encdict, node_array, type_array

def encode(input_file, output_file):

    data = []
    
    while True:
    
        ch = input_file.read(1)
        if not ch:
            break
        
        i = ord(ch)
        data.append(i)
    
    node_bits, node_array, type_array, output_data = encode_data(data)
    output_file.write(encode_write(len(data), node_bits, node_array,
                                   type_array, output_data))

def encode_write(size, node_bits, node_array, type_array, output_data):

    # Write the size of the original data.
    output_buf = ""
    output_buf += struct.pack("<H", size)
    
    # Write the size of the node and type arrays, and the number of bits needed
    # for each node.
    output_buf += struct.pack("<H", len(node_array))
    output_buf += struct.pack("<B", node_bits)
    
    # Write the node and type arrays to the file.
    bit = 0
    c = 0
    for offset in node_array:
        c = c | (offset << bit)
        bit += node_bits
        while bit >= 8:
            output_buf += struct.pack("<B", c & 0xff)
            c = c >> 8
            bit -= 8
    
    if bit != 0:
        output_buf += struct.pack("<B", c & 0xff)
    
    bit = 0
    c = 0
    for type_bit in type_array:
        c = c | (type_bit << bit)
        bit += 1
        if bit == 8:
            output_buf += struct.pack("<B", c)
            c = 0
            bit = 0
    
    if bit != 0:
        output_buf += struct.pack("<B", c)
    
    # Write the encoded data.
    output_buf += "".join(map(chr, output_data))
    
    return output_buf

def encode_data(input_data):

    count = [0] * 256
    
    for c in input_data:
        count[c] += 1
    
    encdict, node_array, type_array = sorted(count)
    
    bit = 0
    c = 0
    output_data = []
    
    for i in input_data:
    
        v, l = encdict[i]
        while l > 0:
            c = c | ((v & 1) << bit)
            v = v >> 1
            l -= 1
            bit += 1
            if bit == 8:
                output_data.append(c)
                bit = 0
                c = 0
    
    if bit != 0:
        output_data.append(c)
    
    # Find the number of bits used to represent the maximum node value.
    node_bits = 0
    m = max(node_array)
    while m > 0:
        node_bits += 1
        m = m >> 1
    
    # At least one bit must be used.
    node_bits = max(1, node_bits)
    
    return node_bits, node_array, type_array, output_data

def decode_data(input_data, node_array, type_array, size, expected_output = None):

    bit = 0
    c = 0
    data = []
    offset = 0
    i = 0
    
    while len(data) < size:
    
        if bit == 0:
            c = input_data[i]
            i += 1
        
        # If the current node is a choice node and not a leaf then find where
        # it leads to.
        if type_array[offset] == 0:
        
            if c & 1 == 0:
                offset += 1
            else:
                offset += node_array[offset] + 1
        
        # If the current node is a leaf node then read the value and prepare
        # for the next one.
        if type_array[offset] == 1:
        
            data.append(node_array[offset])
            
            if expected_output and data[-1] != expected_output[len(data)-1]:
                raise DecodingError, "Decoding check failed at offset %x." % (len(data)-1)
            
            offset = 0
        
        c = c >> 1
        bit = (bit + 1) % 8
    
    return data

def decode(input_file, output_file):

    # Read the number of nodes and their size in bits.
    nodes = struct.unpack("<H", input_file.read(2))[0]
    node_bits = struct.unpack("<B", input_file.read(1))[0]
    node_mask = (1 << node_bits) - 1
    
    # Read the nodes themselves.
    node_array = []
    n = 0
    c = 0
    bit = 0
    while n < nodes:
    
        # Read bytes until there are enough bits for a node.
        if bit < node_bits:
            c = c | (ord(input_file.read(1)) << bit)
            bit += 8
        
        # If there are enough node bits, create a node and keep any remaining
        # bits for the next node.
        if bit >= node_bits:
            node_array.append(c & node_mask)
            bit -= node_bits
            c = c >> node_bits
            n += 1
    
    # Read the types of the nodes.
    type_array = []
    n = 0
    c = 0
    while n < nodes:
    
        if n % 8 == 0:
            c = ord(input_file.read(1))
        
        type_array.append((c >> (n % 8)) & 1)
        n += 1
    
    # Read the size of the original data.
    size = struct.unpack("<H", input_file.read(2))[0]
    
    # Read the encoded data.
    data = map(ord, input_file.read())
    
    decoded_data = decode_data(data, node_array, type_array, size)
    output_file.write("".join(map(chr, decoded_data)))


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
