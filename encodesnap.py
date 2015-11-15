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
    ldx #$0a
    zero_page_loop:
        lda zero_page,x
        sta $70,x
        dex
        bpl zero_page_loop

    lda #$%(mode)x
    sta $fe07
    lda #$%(mode low)x
    sta $fe02
    lda #$%(mode high)x
    sta $fe03

    ldx #$%(sp)x
    txs
    lda #$%(flags)x
    pha
    plp
    ldy #$%(y)x
    ldx #$%(x)x
    lda #$%(a)x
    jmp $%(pc)x

; Data follows this line:
"""

decode_address = 0x0100

def system(command):

    if os.system(command):
        sys.exit(1)

def write_oph_data(data, f):

    i = 0
    while i < len(data):
        line = data[i:i + 24]
        f.write(".byte " + ", ".join(map(str, line)) + "\n")
        i += 24

def decode_flags(flags):

    s = ""
    for f in "NV1BDIZC":
        if flags & 0x80:
            s += f
        else:
            s += " "
        flags = (flags << 1) & 0xff
    
    return s

if __name__ == "__main__":

    if not 3 <= len(sys.argv) <= 4:
        sys.stderr.write("Usage: %s <snapshot file> <output file> [-s|-l]\n" % sys.argv[0])
        sys.exit(1)
    
    input_file = sys.argv[1]
    rom_file = sys.argv[2]
    
    if len(sys.argv) == 4:
        if sys.argv[3] == "-s":
            start_template = "service_template.oph"
        elif sys.argv[3] == "-l":
            start_template = "language_template.oph"
        else:
            sys.stderr.write("Usage: %s <snapshot file> <output file> [-s|-l]\n" % sys.argv[0])
            sys.exit(1)
    else:
        start_template = "service_template.oph"
    
    f = open(input_file, "rb")
    
    if f.read(8) != "ELKSNAP1":
        sys.stderr.write("Not an Elkulator snapshot file: '%s'\n" % input_file)
        sys.exit(1)
    
    # Skip the expansion records.
    f.seek(12, 1)
    
    # Read the 6502 state.
    a, x, y = map(ord, f.read(3))
    # NV1B DIZC
    flags = ord(f.read(1))
    print "flags:", decode_flags(flags)
    
    sp = ord(f.read(1))
    pc_low, pc_high = map(ord, f.read(2))
    pc = pc_low | (pc_high << 8)
    print "pc:", hex(pc)
    
    # Skip the NMI and IRQ states.
    nmi, irq = f.read(2)
    
    # Skip the cycle count.
    f.seek(4, 1)
    
    # Skip the ULA state.
    ula = map(ord, f.read(41))
    print "rom bank:", hex(ula[4])
    
    # Read the memory.
    f.seek(decode_address, 1)
    memory = map(ord, f.read(32768 - decode_address))
    
    f.close()
    
    subst, rldata = rlencode.encode_data(memory)
    hdecode_address = decode_address + len(memory) - len(rldata)
    
    # Only Huffman encode the run-length encoded data.
    node_bits, node_array, type_array, output_data = hencode.encode_data(rldata)
    
    if node_bits > 8:
        sys.stderr.write("Cannot encode node arrays with values requiring more than 8 bits.\n")
        sys.exit(1)
    
    f = open("temp.oph", "wb")
    f.write(open(start_template).read())
    
    # Write the decoding routines.
    f.write(open(huffman_template_file).read() % {"load address": decode_address})
    
    if subst:
        f.write(open(rl_template_file).read())
    
    end_details = {"pc": pc,
                   "sp": sp,
                   "flags": flags,
                   "a": a, "x": x, "y": y,
                   "mode": ula[8] << 3,
                   "mode low": ula[2],
                   "mode high": ula[3]}
    f.write(end_template % end_details)

    # Write the details of the original data, Huffman encoding and run-length
    # encoding.
    f.write(".alias rl_decode_address $%x\n" % decode_address)
    f.write(".alias huffman_decode_address $%x\n" % hdecode_address)
    f.write(".alias end_address $%x\n" % (decode_address + len(memory)))
    
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
    f.write("\n")
    f.write("zero_page:\n")
    write_oph_data(hencode.encode_bits(memory[0x70:0x7b], 8), f)
    f.write("\n")
    
    f.close()
    
    system("ophis temp.oph -o " + rom_file)
    #os.remove("temp.oph")
    
    if os.stat(rom_file).st_size > 16384:
        sys.stderr.write("Warning: ROM file '%s' is larger than 16K.\n" % rom_file)
        sys.exit(1)
    
    rom = open(rom_file, "rb").read()
    rom += "\x00" * (16384 - len(rom))
    open(rom_file, "wb").write(rom)
    print "Written", rom_file
    
    sys.exit()
