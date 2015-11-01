#!/usr/bin/env python

import sys
import hencode

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
    
    node_bits, node_array, type_array, output_data = hencode.encode_data(memory)
    
    f = open(output_file, "wb")
    f.write(hencode.encode_write(len(memory), node_bits, node_array, type_array,
                                 output_data))
    
    sys.exit()
