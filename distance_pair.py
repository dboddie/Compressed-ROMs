#!/usr/bin/env python

import sys

def compress(data, window = "output"):

    special = find_least_used(data)
    
    output = [special]
    
    i = 0
    while i < len(data):
    
        best = []
        b = 0
        
        # Compare strings in the window with upcoming input, starting at the
        # beginning of the window.
        if window == "output":
            k = max(0, i - 255)
            end = i
        else:
            k = max(0, len(output) - 255)
            end = len(output)
        
        while k < end:
        
            if window == "output":
                match = find_match(data, k, i)
            else:
                match = find_match_in_compressed(output, data, k, i)
            
            if len(match) > len(best):
                best = match
                b = k
            
            k += 1
        
        # If there is no match then just include the next byte in the window.
        if len(best) <= 3:
        
            # If the special byte occurs in the input, encode it using a
            # special sequence.
            if data[i] == special:
                output += [special, 0]
                i += 1
            else:
                output.append(data[i])
                i += 1
        
        # Otherwise, encode the special byte, offset from the end of the window
        # and length, skipping the corresponding number of matching bytes in
        # the input stream.
        else:
            # Store length - 1 to allow 256 to be used.
            if window == "output":
                output += [special, i - b, len(best) - 1]
            else:
                output += [special, len(output) - b, len(best) - 1]
            i += len(best)
    
    return output


def find_least_used(data):

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
    
    return special


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


def find_match_in_compressed(output, data, k, i):

    # Compare the bytes in the compressed data, starting at index k, with the
    # bytes in the upcoming data, starting at index i.
    #
    #          i
    # | data   |    ^   |
    #     k ------- j
    #     v
    # | output |
    
    match = []
    j = i
    
    while len(match) < 255 and k < len(output):
    
        if j == len(data) or output[k] != data[j]:
            return match
        
        match.append(output[k])
        
        k += 1
        j += 1
    
    return match


def decompress(data, window = "output"):

    special = data[0]
    output = []
    
    i = 1
    while i < len(data):
    
        b = data[i]
        
        if b != special:
            output.append(b)
            i += 1
        else:
            offset = data[i + 1]
            if offset == 0:
                output.append(special)
                i += 2
            else:
                count = data[i + 2] + 1
                
                if window == "compressed":
                    offset -= count
                
                while count > 0:
                    if window == "output":
                        output.append(output[-offset])
                    else:
                        output.append(data[i - offset - count])
                    count -= 1
            
                i += 3
    
    return output


def merge(data):

    # Take the lowest 4 bits of each byte and pack them together, then take
    # the highest 4 bits of each byte and pack them together. Append the last
    # byte in an odd-sized stream.
    output = []
    
    i = 0
    while i < len(data) - 1:
        output.append((data[i] & 0x0f) | ((data[i+1] & 0x0f) << 4))
        i += 2
    
    i = 0
    while i < len(data) - 1:
        output.append((data[i] & 0xf0) | ((data[i+1] & 0xf0) >> 4))
        i += 2
    
    if len(data) % 2 == 1:
        output.append(data[-1])
    
    return output


def unmerge(data):

    output = []
    
    i = 0
    hl = len(data)/2
    while i < hl:
        output.append(data[i] & 0x0f)
        output.append(data[i] >> 4)
        i += 1
    
    j = 0
    while i < hl*2:
        output[j] = output[j] | (data[i] & 0xf0)
        output[j+1] = output[j+1] | ((data[i] & 0x0f) << 4)
        i += 1
        j += 2
    
    if len(data) % 2 == 1:
        output.append(data[-1])
    
    return output


if __name__ == "__main__":

    args = sys.argv[:]
    
    if "--output" in args:
        mode = "output"
        args.remove("--output")
    elif "--compressed" in args:
        mode = "compressed"
        args.remove("--compressed")
    else:
        mode = "output"
    
    do_merge = "--merge" in args
    if do_merge:
        args.remove("--merge")
    
    if len(args) != 4:
        sys.stderr.write("Usage: %s --compress|--decompress [--output|--compressed] [--merge] <input file> <output file>\n" % sys.argv[0])
        sys.exit(1)
    
    command = sys.argv[1]
    in_f = open(sys.argv[2])
    out_f = open(sys.argv[3], "w")
    
    data = map(ord, in_f.read())
    
    if command == "--compress":
    
        print "Input size:", len(data)
        if do_merge:
            original_data = data
            data = merge(data)
        
        c = compress(data, mode)
        print "Compressed:", len(c)
        out_f.write("".join(map(chr, c)))
        
        d = decompress(c, mode)
        if do_merge:
            d = unmerge(d)
            data = original_data
        
        if data != d:
            i = 0
            while i < len(data) and i < len(d) and data[i] == d[i]:
                i += 1
            
            print "Data at %i compressed incorrectly." % i
    
    else:
        print "Input size:", len(data)
        d = decompress(data, mode)
        if do_merge:
            d = unmerge(d)
        print "Decompressed:", len(d)
        out_f.write("".join(map(chr, d)))
    
    sys.exit()
