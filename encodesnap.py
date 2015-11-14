#!/usr/bin/env python

import sys
import hencode, rlencode

template_file = "decode_template.oph"
start_address = 0x0000

def write_oph_data(data, f):

    i = 0
    while i < len(data):
        line = data[i:i + 24]
        f.write(".byte " + ", ".join(map(str, line)) + "\n")
        i += 24


if __name__ == "__main__":

    if len(sys.argv) != 3:
        sys.stderr.write("Usage: %s <snapshot file> <output file>\n" % sys.argv[0])
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    f = open(input_file, "rb")
    
    if f.read(8) != "ELKSNAP1":
        sys.stderr.write("Not an Elkulator snapshot file: '%s'\n" % input_file)
        sys.exit(1)
    
    # Skip the expansion records.
    f.seek(12, 1)
    
    # Read the 6502 state.
    a, x, y = map(ord, f.read(3))
    # NV1B DIZC
    flags = f.read(1)
    
    sp = f.read(1)
    pc_low, pc_high = map(ord, f.read(2))
    
    # Skip the NMI and IRQ states.
    nmi, irq = f.read(2)
    
    # Skip the cycle count.
    f.seek(4, 1)
    
    # Skip the ULA state.
    f.seek(41, 1)
    
    # Read the memory.
    memory = map(ord, f.read(32768))
    
    f.close()
    
    subst, rldata = rlencode.encode_data(memory)
    
    # Only Huffman encode the run-length encoded data.
    node_bits, node_array, type_array, output_data = hencode.encode_data(rldata)
    
    f = open(output_file, "wb")
    
    # Write the decoding routines.
    f.write(open(template_file).read())
    
    # Write the details of the original data, Huffman encoding and run-length
    # encoding.
    f.write(".alias start $%x\n" % start_address)
    f.write(".alias substitutions %i\n" % len(subst))
    f.write(".alias node_bits %i\n" % node_bits)
    f.write(".alias nodes %i\n" % len(node_array))
    
    f.write("subst_array:\n")
    write_oph_data(hencode.encode_bits(subst, 8), f)
    f.write("node_array:\n")
    write_oph_data(hencode.encode_bits(node_array, node_bits), f)
    f.write("\n")
    f.write("type_array:\n")
    write_oph_data(hencode.encode_bits(type_array, 1), f)
    f.write("\n")
    f.write("data:\n")
    write_oph_data(hencode.encode_bits(output_data, 8), f)
    f.write("end_data:\n")
    f.close()
    
    sys.exit()
