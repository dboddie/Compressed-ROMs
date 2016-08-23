#!/usr/bin/env python

import sys

def compress(data):

    freq = [0] * 256
    
    for b in data:
        freq[b] += 1
    
    try:
        # Try to find an unused byte value.
        special = freq.index(0)
    except ValueError:
        # Find the least used byte value.
        pairs = map(lambda i: (freq[i], i), range(len(freq)))
        pairs.sort()
        special = pairs.pop(0)[1]
    
    output = [special]
    
    i = 0
    while i < len(data):
    
        best = []
        b = 0
        
        # Compare strings in the window with upcoming input, starting at the
        # beginning of the window.
        k = max(0, i - 256)
        while k < i:
        
            match = find_match(data, k, i)
            if len(match) > len(best):
                best = match
                b = k
            
            k += 1
        
        # If there is no match then just include the next byte in the window.
        if len(best) < 3:
        
            # If the special byte occurs in the input, encode it using a
            # special sequence.
            if data[i] == special:
                output += [special, 0, 0]
                i += 1
            else:
                output.append(data[i])
                i += 1
        
        # Otherwise, encode the special byte, offset from the end of the window
        # and length, skipping the corresponding number of matching bytes in
        # the input stream.
        else:
            # Store length - 1 to allow 256 to be used for both.
            output += [special, i - b, len(best) - 1]
            i += len(best)
    
    return output


def find_match(data, k, i):

    # Compare the bytes in the window, starting at index k, with the bytes in
    # the upcoming data, starting at index i.
    #
    # | data   i        |
    #          v
    # | window |        |
    #   ^           ^
    #   k --------- j
    
    match = []
    j = i
    
    while len(match) < 255:
    
        if j == len(data) or data[k] != data[j]:
            return match
        
        match.append(data[k])
        
        k += 1
        j += 1
    
    return match


def decompress(data):

    special = data[0]
    output = []
    
    i = 1
    while i < len(data):
    
        b = data[i]
        
        if b != special:
            output.append(b)
            i += 1
        else:
            offset, count = data[i + 1:i + 3]
            if offset == 0:
                output.append(special)
            else:
                count += 1
                while count > 0:
                    output.append(output[-offset])
                    count -= 1
            
            i += 3
    
    return output


if __name__ == "__main__":

    if len(sys.argv) != 2:
        sys.stderr.write("Usage: %s <input file>\n" % sys.argv[0])
        sys.exit(1)
    
    in_f = open(sys.argv[1])
    data = map(ord, in_f.read())
    print "Input size:", len(data)
    c = compress(data)
    print "Compressed:", len(c)
    d = decompress(c)
    print "Decompressed:", len(d)
    #print " ".join(map(lambda x: "%02x" % x, d))
    if data != d:
        i = 0
        while i < len(data) and i < len(d) and data[i] == d[i]:
            i += 1
        
        print " ".join(map(lambda x: "%02x" % x, data[i-10:i+10]))
        #print " ".join(map(lambda x: "%02x" % x, c[:10]))
        print " ".join(map(lambda x: "%02x" % x, d[i-10:i+10]))
