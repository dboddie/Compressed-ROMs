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

version = "0.1"

import os, sys
import hencode, rlencode

huffman_template_file = "decode_template.oph"
rl_template_file = "rldecode_template.oph"
end_template = """
    cli
    clc
    rts

; Data follows this line:
"""
exec_template = """
    cli
    jmp $%(address)x

; Data follows this line:
"""

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

    if len(sys.argv) != 4 and len(sys.argv) != 6:
        sys.stderr.write("Usage: %s <data file> <decode address> <ROM file> [-e <address>]\n" % sys.argv[0])
        sys.exit(1)
    
    input_file = sys.argv[1]
    decode_address = int(sys.argv[2], 16)
    rom_file = sys.argv[3]
    
    if len(sys.argv) == 6:
        if sys.argv[4] == "-e":
            exec_addr = int(sys.argv[5], 16)
        else:
            sys.stderr.write("Usage: %s <data file> <decode address> <ROM file> [-e <address>]\n" % sys.argv[0])
            sys.exit(1)
    else:
        exec_addr = None
    
    f = open(input_file, "rb")
    data = map(ord, f.read())
    f.close()
    
    subst, rldata = rlencode.encode_data(data)
    hdecode_address = decode_address + len(data) - len(rldata)
    
    # Only Huffman encode the run-length encoded data.
    node_bits, node_array, type_array, output_data = hencode.encode_data(rldata)
    
    if node_bits > 8:
        sys.stderr.write("Cannot encode node arrays with values requiring more than 8 bits.\n")
        sys.exit(1)
    
    f = open("temp.oph", "wb")
    
    # Write the decoding routines.
    f.write(open(huffman_template_file).read() % {"load address": decode_address})
    
    if subst:
        f.write(open(rl_template_file).read())
    
    if exec_addr is None:
        f.write(end_template)
    else:
        f.write(exec_template % {"address": exec_addr})

    # Write the details of the original data, Huffman encoding and run-length
    # encoding.
    f.write(".alias rl_decode_address $%x\n" % decode_address)
    f.write(".alias huffman_decode_address $%x\n" % hdecode_address)
    f.write(".alias end_address $%x\n" % (decode_address + len(data)))
    
    if subst:
        f.write(".alias substitutions %i\n" % len(subst))
        f.write("\n")
        
        f.write("subst_array:\n")
        write_oph_data(hencode.encode_bits(subst, 8), f)
    
    f.write("\n")
    
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
    #os.remove("temp.oph")
    
    rom = open(rom_file, "rb").read()
    rom += "\x00" * (16384 - len(rom))
    open(rom_file, "wb").write(rom)
    print "Written", rom_file
    
    sys.exit()
