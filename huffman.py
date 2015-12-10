#!/usr/bin/env python

# Copyright (C) 2015 David Boddie <david@boddie.org.uk>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import marshal, sys

class Node:

    """Represents a node in the tree used to encode values in the compressed
    data stream."""
    
    def __init__(self, less, greater):
    
        self.less = less
        self.greater = greater
    
    def __str__(self):
    
        return "%i:\n%s %i:\n%s" % (
            self.less[0], self.less[1], self.greater[0], self.greater[1]
            )
    
    def weight(self):
    
        return self.less[0] + self.greater[0]

class BitWriter:

    """Writes values with arbitrary numbers of bits to a sequence of bytes."""
    
    def __init__(self):
    
        self.header = None
        self.data = []
        self.current = 0
        self.bit = 0
    
    def writeHeader(self, codes):
    
        self.header = codes.items()
        self.header.sort()
    
    def write(self, value, bits = None):
    
        if bits == None:
        
            bits = 0
            v = value
            while v != 0:
                v = v >> 1
                bits += 1
        
        while bits > 0:
        
            if value & 1 == 1:
                self.current = self.current | (1 << self.bit)
            
            self.bit += 1
            
            if self.bit == 8:
                self.bit = 0
                self.data.append(chr(self.current))
                self.current = 0
            
            bits -= 1
            value = value >> 1
    
    def __str__(self):
    
        if self.bit != 0:
            self.data.append(chr(self.current))
            self.bit = 0
            self.current = 0
        
        return marshal.dumps((self.header, "".join(self.data)))

class BitReaderError(Exception):
    pass

class BitReader:

    """Reads values with arbitrary numbers of bits from a sequence of bytes."""
    
    def __init__(self, data):
    
        self.current = 0
        self.bit = 0
        self.header, self.data = marshal.loads(data)
        
        self.root = []
        
        for (bits, value), character in self.header:
            self.storeCharacter(bits, value, character, self.root)
    
    def storeCharacter(self, bits, value, character, parent):
    
        ###
    
    def read(self):
    
        
            value = 0
            current = self.data[self.current]
            
            while bits > 0:
            
                if current & (1 << self.bit) != 0:
                    value = value | (1 << self.bit)
                
                self.bit += 1
                
                if self.bit == 8:
                    self.bit = 0
                    self.current += 1
                    current = self.data[self.current]
                
                bits -= 1
    
    def __str__(self):
    
        return "".join(map(chr, self.data))

def find_codes(node, current, bit, dictionary, reverse):

    # Descend the tree of nodes, assigning codes and the number of bits
    # required them to each node.
    
    if isinstance(node.less[1], Node):
        less_max_bits = find_codes(node.less[1], current, bit + 1, dictionary,
                                   reverse)
    else:
        code = current
        less_max_bits = bit + 1
        dictionary[(less_max_bits, code)] = node.less[1]
        reverse[node.less[1]] = code
    
    if isinstance(node.greater[1], Node):
        greater_max_bits = find_codes(node.greater[1], current | (1 << bit),
                                    bit + 1, dictionary, reverse)
    else:
        code = current | (1 << bit)
        greater_max_bits = bit + 1
        dictionary[(greater_max_bits, code)] = node.greater[1]
        reverse[node.greater[1]] = code
    
    return max(less_max_bits, greater_max_bits)

def encode(input_file, output_file):

    text = input_file.read()
    input_file.close()
    
    frequencies = {}
    for character in text:
        frequencies[character] = frequencies.get(character, 0) + 1
    
    table = map(lambda (character, frequency): (frequency, character), frequencies.items())
    table.sort()
    
    while table:
    
        # Take the two lowest frequency characters from the list.
        frequency1, character1 = table.pop(0)
        frequency2, character2 = table.pop(0)
        
        if frequency1 < frequency2:
            node = Node((frequency1, character1), (frequency2, character2))
        else:
            node = Node((frequency2, character2), (frequency1, character1))
        
        # If no more characters are left then break.
        if not table:
            break
        
        # Insert the new node into the list.
        i = 0
        weight = node.weight()
        for i in range(len(table)):
        
            frequency = table[i][0]
            
            if frequency > weight:
                table.insert(i, (weight, node))
                break
            else:
                i += 1
        else:
            table.append((weight, node))
    
    codes = {}
    reverse = {}
    max_bits = find_codes(node, 0, 0, codes, reverse)
    
    # Write table.
    #
    # Number of entries (1 byte).
    b = BitWriter()
    b.write(len(codes), 8)
    b.writeHeader(codes)
    
    #for item in range(len(codes)):
    #    try:
    #        character = codes[item]
    #    except KeyError:
    #        # Encode a branch node as a null byte.
    #        character = "\x00"
    #    b.write(ord(character), 8)
    #    print hex(item), repr(character)
    
    for c in text:
        b.write(reverse[c])
    
    output_file.write(str(b))

def decode(input_file, output_file):

    data = input_file.read()
    
    b = BitReader(data)
    

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
