#!/usr/bin/env python

import sys

class Node:

    def __init__(self, less, greater):
    
        self.less = less
        self.greater = greater
    
    def __str__(self):
    
        return "%i:\n%s %i:\n%s" % (
            self.less[0], self.less[1], self.greater[0], self.greater[1]
            )
    
    def weight(self):
    
        return self.less[0] + self.greater[0]

def find_codes(node, current, bit, dictionary):

    if isinstance(node.less[1], Node):
        find_codes(node.less[1], current, bit + 1, dictionary)
    else:
        dictionary[(current, bit + 1)] = node.less[1]
    
    if isinstance(node.greater[1], Node):
        find_codes(node.greater[1], current | (1 << bit), bit + 1, dictionary)
    else:
        dictionary[(current | (1 << bit), bit + 1)] = node.greater[1]

def bin(value, bits):

    output = ""
    
    while bits > 0:
        if value & 1 == 0:
            output += "0"
        else:
            output += "1"
        value = value >> 1
        bits -= 1
    
    return output


if __name__ == "__main__":

    if len(sys.argv) == 1:
    
        in_f = sys.stdin
        out_f = sys.stdout
    
    elif len(sys.argv) == 3:
    
        in_f = open(sys.argv[1], "rb")
        out_f = open(sys.argv[2], "wb")
    
    else:
        sys.stderr.write("Usage: %s [<input file> <output file>]\n" % sys.argv[0])
        sys.exit(1)
    
    text = in_f.read()
    in_f.close()
    
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
    find_codes(node, 0, 0, codes)
    
    for (code, bits), character in codes.items():
        print bin(code, bits), repr(character)
    
    sys.exit()
