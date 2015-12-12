Compression Tools and Decompression Routines for 8-Bit Acorn Computers
======================================================================

This repository contains tools for compressing data on modern computers and
routines for decompressing the data on 8-bit Acorn computers. Compressed data
is stored as part of ROM images that also contain the necessary routines and
lookup tables for unpacking the data into memory.

Usage
-----

For the creation of ROM images containing compressed data, it is only necessary
to run the encodedata.py and encodesnap.py tools. These use a combination of
the algorithms in the compression modules to reduce the size of the compressed
data as much as possible before combining it with the decompression routines
and lookup tables required to unpack the data. The tools also add suitable
headers that are required for ROMs on 8-bit Acorn computers. The Ophis
assembler is used to create the final ROM files.

Before using the encodedata.py and encodesnap.py tools, edit the appropriate
template file (service_template.oph for service ROMs, language_template.oph for
language ROMs) to include a description of the compressed data in the following
way.

Update the title and version number to describe your version of the ROM code,
and append additional copyright information to the existing copyright string.
For example, if the compressed data is for version 2.1 of program "XYZ",
written by "A.N. Author" in the year 2016, update the strings accordingly:

  ; Title string
  .byte "Decoder for XYZ 2.1", 0

  ; Version string
  .byte "1.0", 0

  copyright_string:
  .byte "(C) 2015 David Boddie; XYZ is (C) 2016 A.N. Author", 0

Update the version string each time you need to repackage the same original
code or data (for example, "XYZ 2.1") and reset the version to 1.0 for each
new release of the original code or data (for example, "XYZ 2.2").

Compression
-----------

Compression is performed by two Python modules: hencode.py and rlencode.py.
These perform Huffman encoding and run-length encoding respectively. Both of
these modules can be run independently on files to compress and decompress
them.

Data is first compressed using run-length encoding, if possible. Afterwards, it
is compressed using Huffman encoding. If run-length encoding is not efficient,
the decompression routines for this algorithm are excluded from the ROM image,
saving space for data.

Decompression
-------------

Compressed data is decoded in stages into the memory area that the decompressed
data will occupy. Firstly, Huffman encoded data is decompressed into the top of
the memory area. Then, if the data was run-length encoded, the appropriate
routine is used to decompress the intermediate data into the full memory area,
starting at the lowest address. In this way, we use the memory area as a buffer
without overwriting intermediate data.

Limitations
-----------

The compressed data can have an arbitrary size. The compression tools will pad
the resulting ROM files to multiples of 16K. However, there is no provision for
accessing data beyond the first 16K in each ROM. Therefore, only data that will
fit into a 16K ROM along with the required routines and data tables will be
decompressed correctly.

Language ROMs generated using the language_template.oph do not currently work
correctly.

Licenses
--------

Both the assembly language routines and the Python modules and tools are
licensed under the GNU General Public License version 3 or later:

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

According to the GPL FAQ, an installer and the files it installs are considered
to be separate works:

  http://www.gnu.org/licenses/gpl-faq.html#GPLCompatInstaller

This means that compliance with the above license with respect to the routines
provided in this package is independent of compliance with the license of the
code or data you include in an assembled ROM file.

The code or data you include in an assembled ROM file will retain its original
copyright and license which must be handled accordingly. Including a work in an
assembled ROM file does not exempt you from any obligations you have under that
work's license.
