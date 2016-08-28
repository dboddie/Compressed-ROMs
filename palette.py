#!/usr/bin/env python

"""
Copyright (C) 2015 David Boddie <david@boddie.org.uk>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import sys

colours = {"black": (0, 0, 0),  "red":  (1, 0, 0), "green":   (0, 1, 0),
           "yellow": (1, 1, 0), "blue": (0, 0, 1), "magenta": (1, 0, 1),
           "cyan": (0, 1, 1), "white": (1, 1, 1)}

# 4 colour mode
# fe08: b3 b2 b1 b0 g3 g2  x  x
# fe09:  x  x g1 g0 r3 r2 r1 r0

modes = {
    #        Red          Green          Blue          Logical
    #     FE08  FE09    FE08  FE09    FE08  FE09       colours
    2: [((0xff, 0xfe), (0xff, 0xef), (0xef, 0xff)),  #    0
        ((0xff, 0xfb), (0xfb, 0xff), (0xbf, 0xff))], #    1

    4: [((0xff, 0xfe), (0xff, 0xef), (0xef, 0xff)),  #    0
        ((0xff, 0xfd), (0xff, 0xdf), (0xdf, 0xff)),  #    1
        ((0xff, 0xfb), (0xfb, 0xff), (0xbf, 0xff)),  #    2
        ((0xff, 0xf7), (0xf7, 0xff), (0x7f, 0xff))], #    3

    16: [((0xff, 0xfe), (0xff, 0xef), (0xef, 0xff)), #    0 (fe08,fe09)
         ((0xff, 0xfe), (0xff, 0xef), (0xef, 0xff)), #    1 (fe0e,fe0f)
         ((0xff, 0xfd), (0xff, 0xdf), (0xdf, 0xff)), #    2 (fe08,fe09)
         ((0xff, 0xfd), (0xff, 0xdf), (0xdf, 0xff)), #    3 (fe0e,fe0f)
         ((0xff, 0xfe), (0xff, 0xef), (0xef, 0xff)), #    4 (fe0a,fe0b)
         ((0xff, 0xfe), (0xff, 0xef), (0xef, 0xff)), #    5 (fe0c,fe0d)
         ((0xff, 0xfd), (0xff, 0xdf), (0xdf, 0xff)), #    6 (fe0a,fe0b)
         ((0xff, 0xfd), (0xff, 0xdf), (0xdf, 0xff)), #    7 (fe0c,fe0d)
         ((0xff, 0xfb), (0xfb, 0xff), (0xbf, 0xff)), #    8 (fe08,fe09)
         ((0xff, 0xfb), (0xfb, 0xff), (0xbf, 0xff)), #    9 (fe0e,fe0f)
         ((0xff, 0xf7), (0xf7, 0xff), (0x7f, 0xff)), #   10 (fe08,fe09)
         ((0xff, 0xf7), (0xf7, 0xff), (0x7f, 0xff)), #   11 (fe0e,fe0f)
         ((0xff, 0xfb), (0xfb, 0xff), (0xbf, 0xff)), #   12 (fe0a,fe0b)
         ((0xff, 0xfb), (0xfb, 0xff), (0xbf, 0xff)), #   13 (fe0c,fe0d)
         ((0xff, 0xf7), (0xf7, 0xff), (0x7f, 0xff)), #   14 (fe0a,fe0b)
         ((0xff, 0xf7), (0xf7, 0xff), (0x7f, 0xff))] #   15 (fe0c,fe0d)
    }

mode2_registers = [0xfe08, 0xfe0e, 0xfe08, 0xfe0e,
                   0xfe0a, 0xfe0c, 0xfe0a, 0xfe0c,
                   0xfe08, 0xfe0e, 0xfe08, 0xfe0e,
                   0xfe0a, 0xfe0c, 0xfe0a, 0xfe0c]

def rgb(standard_colour):

    r = standard_colour & 1
    g = (standard_colour >> 1) & 1
    b = (standard_colour >> 2) & 1
    return (r, g, b)

def get_entries(number_of_colours, colours):

    if number_of_colours < 16:
    
        fe08 = fe09 = 0xff
        
        for i in range(len(colours)):
            r, g, b = colours[i]
            masks = modes[number_of_colours][i]
            for component, mask in zip((r, g, b), masks):
                if component:
                    fe08 = fe08 & mask[0]
                    fe09 = fe09 & mask[1]
        
        return fe08, fe09
    
    else:
        values = [0xff] * 8
        
        for i in range(len(colours)):
            r, g, b = colours[i]
            masks = modes[number_of_colours][i]
            for component, mask in zip((r, g, b), masks):
                address = mode2_registers[i]
                if component:
                    j = address - 0xfe08
                    values[j] = values[j] & mask[0]
                    values[j + 1] = values[j + 1] & mask[1]
        
        return values

def palette(number):

    fe08 = fe09 = 0xff
    
    for i in range(4):
        colour = raw_input("Colour %i: " % i)
        r, g, b = colours[colour]
        masks = modes[number][i]
        for component, mask in zip((r, g, b), masks):
            if component:
                fe08 = fe08 & mask[0]
                fe09 = fe09 & mask[1]
    
    print "fe08: $%x" % fe08
    print "fe09: $%x" % fe09


if __name__ == "__main__":

    if len(sys.argv) == 2:
        rgb_list = map(lambda name: colours[name], sys.argv[1].split(","))
        fe08, fe09 = get_entries(4, rgb_list)
        print "fe08: $%x" % fe08
        print "fe09: $%x" % fe09
    else:
        palette(4)
