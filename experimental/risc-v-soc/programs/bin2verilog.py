#!/usr/bin/env python3
"""
Convert binary file to Verilog hex initialization format
"""

import sys
import argparse

def bin_to_verilog(bin_file, output_file=None, start_addr=0):
    """Convert binary file to Verilog memory initialization"""

    with open(bin_file, 'rb') as f:
        data = f.read()

    # Pad to 4-byte boundary
    while len(data) % 4 != 0:
        data += b'\x00'

    # Convert to 32-bit words (little endian)
    words = []
    for i in range(0, len(data), 4):
        word = int.from_bytes(data[i:i+4], byteorder='little')
        words.append(word)

    # Generate Verilog initialization code
    output_lines = []
    output_lines.append("// Generated from: {}".format(bin_file))
    output_lines.append("// Total words: {}".format(len(words)))
    output_lines.append("")

    for i, word in enumerate(words):
        addr = start_addr + i
        output_lines.append("imem[{:3d}] = 32'h{:08x};  // addr 0x{:04x}".format(
            addr, word, addr * 4))

    # Write to output file or stdout
    output_text = '\n'.join(output_lines)

    if output_file:
        with open(output_file, 'w') as f:
            f.write(output_text)
        print(f"Generated {output_file}")
    else:
        print(output_text)

    return len(words)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert binary to Verilog hex format')
    parser.add_argument('input', help='Input binary file')
    parser.add_argument('-o', '--output', help='Output file (default: stdout)')
    parser.add_argument('-s', '--start', type=int, default=0,
                        help='Start address in imem (default: 0)')

    args = parser.parse_args()

    num_words = bin_to_verilog(args.input, args.output, args.start)
    print(f"Converted {num_words} words", file=sys.stderr)
