#!/usr/bin/env python

import struct, sys

def encode(input_file, output_file):

    data = []
    
    while True:
    
        ch = input_file.read(1)
        if not ch:
            break
        
        i = ord(ch)
        data.append(i)
    
    subst, output_data = encode_data(data)
    output_file.write(encode_write(subst, output_data))

def encode_write(subst, output_data):

    # Write the size of the substitution value list.
    output_buf = ""
    output_buf += struct.pack("<B", len(subst))
    
    # Write the substitution values.
    for value in subst:
        output_buf += chr(value)
    
    # Write the encoded data.
    output_buf += "".join(map(chr, output_data))
    
    return output_buf

def find_spans(c, data):

    new_data = []
    span = 0
    
    for j in data:
    
        if j == c:
            # The value is the one we are encoding so increase the span.
            span += 1
            
            # Only allow spans of up to 256 values in length.
            if span == 256:
                new_data += [c, span - 1]
                span = 0
        else:
            # Add the pending span to the output.
            if span > 0:
                new_data += [c, span - 1]
            
            # Add the new value to the output.
            new_data.append(j)
            span = 0
    
    if span > 0:
        new_data += [c, span - 1]
    
    return new_data

def encode_spans(subst, data):

    new_data = []
    span = 0
    c = None
    
    for j in data:
    
        if j in subst:
        
            if c == j:
                span += 1
                if span == 256:
                    new_data += [c, span - 1]
                    span = 0
            else:
                if span > 0:
                    new_data += [c, span - 1]
                c = j
                span = 1
        else:
            if span > 0:
                new_data += [c, span - 1]
            
            new_data.append(j)
            c = j
            span = 0
    
    if span > 0:
        new_data += [c, span - 1]
    
    return new_data

def encode_data(input_data):

    count = [0] * 256
    
    for c in input_data:
        count[c] += 1
    
    values = []
    i = 0
    while i < 256:
        values.append((count[i], i))
        i += 1
    
    # Discard values that didn't occur.
    values = filter(lambda (n, i): n != 0, values)
    # Sort the values in increasing order of frequency.
    values.sort()
    
    data = input_data[:]
    length = len(data)
    i = len(values) - 1
    
    # Try performing run length encoding on certain common values.
    subst = []
    
    while i >= 0:
    
        n, c = values[i]
        new_data = find_spans(c, data)
        
        if len(new_data) + 1 < length - 32:
            # If the length of the new data plus the byte needed to store the
            # substitution is less than the original length minus an arbitrary
            # amount then record the substitution value.
            subst.append(c)
        else:
            break
        
        i -= 1
    
    data = encode_spans(subst, data)
    
    return subst, data

def decode_data(subst, input_data):

    # Apply the substitutions.
    data = []
    j = 0
    
    while j < len(input_data):
    
        c = input_data[j]
        
        if c in subst:
            span = input_data[j + 1] + 1
            data += [c] * span
            j += 1
        else:
            data.append(c)
        
        j += 1
    
    return data

def decode(input_file, output_file):

    # Read the number of substitutions.
    n = struct.unpack("<B", input_file.read(1))[0]
    
    # Read the substitutions themselves.
    subst = []
    while len(subst) < n:
        subst.append(ord(input_file.read(1)))
    
    # Read the encoded data.
    data = map(ord, input_file.read())
    
    decoded_data = decode_data(subst, data)
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
