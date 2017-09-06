#!/bin/usr/python3
import re
from jinja2 import Template
import click
BIN = "28'b"
ZEROS = '00000000'
INS = {
    'NOP': "0",
    'LED': "0010",
    'BLE': "0010",
    'STO': "0011",
    'ADD': "0100",
    'JMP': "0101",
    'SUB': "0110",
    'IMUL': "0111",
    'IMUL_4': "1000",
    'IMUL_LUT': "1001",
    'IMUL_GEN': "1010",
    'MOVE_UPP': "1011",
    'MOVE_DOWN': "1100"
}
TAGS = {}

ROM_TEMPLATE = Template('''/*
This module was out generated using asm.py, MiniAlu's assembler
report any bug to javinachop@gmail.com

asm.py is distributed under GNU GPL see <http://www.gnu.org/licenses/>
*/

`timescale 1ns / 1ps
module ROM(
	   input wire [7:0] iAddress,
	   output reg [27:0] oInstruction
	   );
 always @ ( iAddress )
     begin
	case (iAddress)
          {% for i in range(asm|length) %}
           {{i}}: oInstruction = {{asm[i]}};
          {% endfor %}
	  default:
	    oInstruction = { 4'b0010 ,  24'b10101010 };		//NOP
	endcase
     end

endmodule
''')


def map_reg(reg):
    try:

        return '{0:08b}'.format(int(reg.split('R', 1)[1]))
    except:
        raise Exception('Error parsing reg {}'.format(reg))


def map_inmd(val):
    if val in TAGS:
        return '{0:08b}'.format(TAGS[val])
    else:
        return '{0:016b}'.format(int(val))

@click.command()
@click.argument('filename', type=click.File('rb'))
@click.argument('output', type=click.File('wb'))
def main(filename, output):
    asm = []
    text = filename.read().decode('utf-8')
    text = re.sub(r'(?m)^ *#.*\n?', '', text).replace(' ', '').strip().splitlines()
    text = [line for line in text if line.strip() != '']
    for i in range(len(text)):
        match = re.match('(\w*):', text[i])
        if match:
            TAGS[match.group(1)] = i-len(TAGS)

    for line in text:
        ins = line.split('#', 1)[0]
        if ins:
            ins = ins.split(',')
            if re.match(r'(\w*):', ins[0]):
                continue
            if ins[0] in INS:
                if ins[0] == 'NOP':
                    asm.append(BIN+INS['NOP'])
                elif ins[0] == 'LED':
                    src1 = map_reg(ins[1])
                    asm.append(BIN+INS['LED']+ZEROS+src1+ZEROS)
                elif ins[0] == 'BLE':
                    dest = map_reg(ins[1])
                    src1 = map_reg(ins[2])
                    src0 = map_reg(ins[3])
                    asm.append(BIN+INS[ins[0]]+dest+src1+src0)
                elif ins[0] == 'STO':
                    dest = map_reg(ins[1])
                    inmd_val = map_inmd(ins[2])
                    asm.append(BIN+INS[ins[0]]+dest+inmd_val)
                elif ins[0] == 'ADD':
                    dest = map_reg(ins[1])
                    src1 = map_reg(ins[2])
                    src0 = map_reg(ins[3])
                    asm.append(BIN+INS[ins[0]]+dest+src1+src0)
                elif ins[0] == 'JMP':
                    inmd_val = map_inmd(ins[1])
                    asm.append(BIN+INS[ins[0]]+inmd_val+ZEROS+ZEROS)
                elif ins[0] == 'SUB':
                    dest = map_reg(ins[1])
                    src1 = map_reg(ins[2])
                    src0 = map_reg(ins[3])
                    asm.append(BIN+INS[ins[0]]+dest+src1+src0)
                elif ins[0] == 'IMUL':
                    src1 = map_reg(ins[1])
                    src0 = map_reg(ins[2])
                    asm.append(BIN+INS[ins[0]]+ZEROS+src1+src0)
                elif ins[0] == 'IMUL_4':
                    src1 = map_reg(ins[1])
                    src0 = map_reg(ins[2])
                    asm.append(BIN+INS[ins[0]]+ZEROS+src1+src0)
                elif ins[0] == 'IMUL_LUT':
                    src1 = map_reg(ins[1])
                    src0 = map_reg(ins[2])
                    asm.append(BIN+INS[ins[0]]+ZEROS+src1+src0)
                elif ins[0] == 'IMUL_GEN':
                    src1 = map_reg(ins[1])
                    src0 = map_reg(ins[2])
                    asm.append(BIN+INS[ins[0]]+ZEROS+src1+src0)
                elif ins[0] == 'MOVE_UPP':
                    dest = map_reg(ins[1])
                    asm.append(BIN+INS[ins[0]]+dest+ZEROS+ZEROS)
                elif ins[0] == 'MOVE_DOWN':
                    dest = map_reg(ins[1])
                    asm.append(BIN+INS[ins[0]]+dest+ZEROS+ZEROS)
            else:
                raise Exception('Invalid instruction: {}, on line {}'.format(ins[0]), line)

    output.write(ROM_TEMPLATE.render(asm=asm).encode('utf-8'))


if __name__ == '__main__':
    main()
