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
import distance_pair
from palette import rgb, get_entries

huffman_template_file = "decode_template.oph"
rl_template_file = "rldecode_template.oph"
dp_template_file = "dp_template.oph"

check_system_template = """
    ; Check the system in use.

    lda #129
    ldx #0
    ldy #255
    jsr $fff4
    cpx #1
    beq electron_os
    bne exit_rom

    electron_os:

"""

reentry_copy_template = """
    ; Copy the reentry code into RAM.

    lda #<reentry
    sta $70
    lda #>reentry
    sta $71
    lda #$%(reentry low)x
    sta $72
    lda #$%(reentry high)x
    sta $73

    ldy #[data - reentry]

    reentry_loop:
        dey

        lda ($70),y
        sta ($72),y

        cpy #0
        bne reentry_loop
"""

snapshot_end_template = reentry_copy_template + """
    ldx #$08
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

    %(palette code)s
    %(rom code)s

    ; Run the reentry code.
    jmp $%(reentry address)x

reentry:
    lda #$%(bank)x
    sta $f4
    sta $fe05

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

chain_end_template = reentry_copy_template + """
    ; Run the reentry code.
    jmp $%(reentry address)x

reentry:
    cli
    ldx #<[%(reentry address)i + next_rom - reentry]
    ldy #>[%(reentry address)i + next_rom - reentry]
    jsr $fff7

next_rom: .byte "%(next rom)s", 13
"""

data_end_template = """
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

def decode_flags(flags):

    s = ""
    for f in "NV1BDIZC":
        if flags & 0x80:
            s += f
        else:
            s += " "
        flags = (flags << 1) & 0xff
    
    return s

def usage():

    sys.stderr.write("Usage: %s [-s|-l] [-e <execution address>] "
        "[-d <decode address>] [-f <decode end address>] "
        "[-r <reentry address>] [-c <next rom command>] [-R] "
        "<snapshot file> <output file>\n" % sys.argv[0])
    sys.exit(1)

def get_arg(option, args, default):

    if option in args:
        i = args.index(option)
        value = args[i + 1]
        args.pop(i)
        args.pop(i)
        return value
    else:
        return default

if __name__ == "__main__":

    args = sys.argv[:]
    
    if "-s" in args:
        args.remove("-s")
        start_template = "service_template.oph"
    elif "-l" in args:
        args.remove("-l")
        start_template = "language_template.oph"
    else:
        start_template = "service_template.oph"
    
    exec_addr = int(get_arg("-e", args, "0"), 16)
    decode_address = int(get_arg("-d", args, "00d0"), 16)
    decode_end_address = int(get_arg("-f", args, "8000"), 16)
    reentry_address = int(get_arg("-r", args, "00b0"), 16)
    name = get_arg("-n", args, "MGRUN")
    chain = get_arg("-c", args, "")
    
    if "-c" in args:
        check_system = True
        args.remove("-c")
    else:
        check_system = False
    
    if "-R" in args:
        star_rom = True
        args.remove("-R")
    else:
        star_rom = False
    
    if len(args) != 3:
        usage()
    
    input_file = args[1]
    rom_file = args[2]
    
    f = open(input_file, "rb")
    
    if f.read(8) == "ELKSNAP1":
        make_snapshot = True
    else:
        make_snapshot = False
    
    if make_snapshot:
    
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
        
        print "sound:", ula[7]
        print "tape:", ula[9]
        print "tape out:", ula[10]
        
        # Read the palette.
        palette = ula[11:27]
        print "mode:", ula[8]
        print "palette:", palette
        
        # Read the memory.
        f.seek(decode_address, 1)
        memory = map(ord, f.read(decode_end_address - decode_address))
        
        f.close()
    
    else:
    
        f.seek(0, 0)
        memory = map(ord, f.read())
        f.close()
    
    #subst, rldata = rlencode.encode_data(memory)
    #hdecode_address = decode_address + len(memory) - len(rldata)
    
    # Only Huffman encode the run-length encoded data.
    #node_bits, node_array, type_array, output_data = hencode.encode_data(rldata)
    
    #if node_bits > 8:
    #    sys.stderr.write("Cannot encode node arrays with values requiring more than 8 bits.\n")
    #    sys.exit(1)
    
    output_data = distance_pair.compress(memory)
    
    f = open("temp.oph", "wb")
    f.write(open(start_template).read() % {"rom name string": name})
    
    # Write the decoding routines.
    #f.write(open(huffman_template_file).read())
    #
    #if subst:
    #    f.write(open(rl_template_file).read())
    
    f.write("decode_command:\n\n")
    
    if check_system:
        f.write(check_system_template)
    
    f.write(open(dp_template_file).read())
    
    if make_snapshot and not chain:
    
        mode = ula[8]
        if mode in (0, 3, 4, 6):
            colours = [rgb(palette[0]), rgb(palette[14])]
            registers = get_entries(2, colours)
        elif mode in (1, 5):
            colours = [rgb(palette[0]), rgb(palette[2]), rgb(palette[8]), rgb(palette[10])]
            registers = get_entries(4, colours)
        else:
            colours = [rgb(palette[0]), rgb(palette[14])]
            registers = get_entries(16, colours)
        
        palette_code = []
        v = 0xfe08
        for r in registers:
            palette_code += [
                "lda #$%x" % r,
                "sta $%x" % v
                ]
            v += 1
        
        palette_code = "\n    ".join(palette_code)
        
        if star_rom:
            rom_code = (
                "    lda #141\n"
                "    jsr $ffee"
                )
        else:
            rom_code = ""
        
        end_details = {"pc": pc,
                       "sp": sp,
                       "flags": flags,
                       "a": a, "x": x, "y": y,
                       "mode": (mode << 3) | 0x80,
                       "mode low": ula[2],
                       "mode high": ula[3],
                       "bank": ula[4],
                       "sound": ula[7],
                       "tape": ula[9],
                       "tapeout": ula[10],
                       "reentry address": reentry_address,
                       "reentry low": reentry_address & 0xff,
                       "reentry high": reentry_address >> 8,
                       "palette code": palette_code,
                       "rom code": rom_code}
        f.write(snapshot_end_template % end_details)
    
    elif chain:
        f.write(chain_end_template % {
            "next rom": chain,
            "reentry address": reentry_address,
            "reentry low": reentry_address & 0xff,
            "reentry high": reentry_address >> 8,
            })
    
    else:
        f.write(data_end_template)
    
    # Write the details of the original data, Huffman encoding and run-length
    # encoding.
    #f.write(".alias rl_decode_address $%x\n" % decode_address)
    #f.write(".alias huffman_decode_address $%x\n" % hdecode_address)
    #f.write(".alias end_address $%x\n" % (decode_address + len(memory)))
    #
    #if subst:
    #    f.write(".alias substitutions %i\n" % len(subst))
    #    f.write("\n")
    #    
    #    f.write("subst_array:\n")
    #    write_oph_data(hencode.encode_bits(subst, 8), f)
    #
    #f.write("\n")
    #
    #f.write("node_array:\n")
    #write_oph_data(hencode.encode_bits(node_array, 8), f)
    #f.write("\n")
    #f.write("type_array:\n")
    #write_oph_data(hencode.encode_bits(type_array, 1), f)
    #f.write("\n")
    #
    #f.write("data:\n")
    #write_oph_data(hencode.encode_bits(output_data, 8), f)
    #f.write("\n")
    #f.write("zero_page:\n")
    #write_oph_data(hencode.encode_bits(memory[0x70:0x7b], 8), f)
    #f.write("\n")
    
    f.write(".alias decode_address $%x\n" % decode_address)
    f.write(".alias end_address $%x\n" % (decode_address + len(memory)))
    
    f.write("data:\n")
    write_oph_data(output_data, f)
    f.write("\n")
    
    if make_snapshot:
        f.write("zero_page:\n")
        write_oph_data(hencode.encode_bits(memory[0x70:0x78], 8), f)
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
