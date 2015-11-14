#!/usr/bin/env python

import os, sys
import hencode, rlencode

template_file = "decode_template.oph"
version = "0.1"

def system(command):

    if os.system(command):
        sys.exit(1)

def write_oph_data(data, f):

    i = 0
    while i < len(data):
        line = data[i:i + 24]
        f.write(".byte " + ", ".join(map(str, line)) + "\n")
        i += 24


if __name__ == "__main__":

    if len(sys.argv) != 4:
        sys.stderr.write("Usage: %s <data file> <decode address> <ROM file>\n" % sys.argv[0])
        sys.exit(1)
    
    input_file = sys.argv[1]
    decode_address = int(sys.argv[2], 16)
    rom_file = sys.argv[3]
    
    f = open(input_file, "rb")
    data = map(ord, f.read())
    f.close()
    
    #subst, rldata = rlencode.encode_data(memory)
    
    # Only Huffman encode the run-length encoded data.
    node_bits, node_array, type_array, output_data = hencode.encode_data(data)
    
    f = open("temp.oph", "wb")
    
    # Write the decoding routines.
    f.write(open(template_file).read() % {"load address": decode_address})
    
    # Write the details of the original data, Huffman encoding and run-length
    # encoding.
    f.write(".alias start_address $%x\n" % decode_address)
    f.write(".alias end_address $%x\n" % (decode_address + len(data)))
    #f.write(".alias substitutions %i\n" % len(subst))
    f.write("\n")
    
    #f.write("subst_array:\n")
    #write_oph_data(hencode.encode_bits(subst, 8), f)
    f.write("node_array:\n")
    write_oph_data(hencode.encode_bits(node_array, 8), f)
    f.write("\n")
    f.write("type_array:\n")
    write_oph_data(hencode.encode_bits(type_array, 1), f)
    f.write("\n")
    f.write("data:\n")
    write_oph_data(hencode.encode_bits(output_data, 8), f)
    f.close()
    
    system("ophis temp.oph -o " + rom_file)
    
    rom = open(rom_file, "rb").read()
    rom += "\x00" * (16384 - len(rom))
    open(rom_file, "wb").write(rom)
    print "Written", rom_file
    
    sys.exit()
