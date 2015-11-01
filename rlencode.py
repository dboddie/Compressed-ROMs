#!/usr/bin/env python

import sys

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
        
        if len(new_data) >= length:
            break
        else:
            # Replace the data with the encoded data.
            data = new_data
            subst.append(c)
            # Update the length to improve on and try the next value.
            length = len(data)
            i -= 1
    
    return subst, data

def decode_data(subst, input_data):

    data = input_data[:]
    
    # Apply the substitutions in reverse order.
    for c in subst[::-1]:
    
        new_data = []
        
        j = 0
        while j < len(data):
        
            if data[j] == c:
                span = data[j + 1] + 1
                new_data += [c] * span
                j += 1
            else:
                new_data.append(data[j])
            
            j += 1
        
        data = new_data
    
    return data
