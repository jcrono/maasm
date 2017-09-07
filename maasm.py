#!/bin/usr/python3
import re
from jinja2 import Template
import click
INS = {
    'NOP': {'op': 0, 'num': 0, 'args': ['zero', 'zero', 'zero']},
    'LED': {'op': 2,  'num': 1, 'args': ['zero', 'arg', 'zero']},
    'BLE': {'op': 3, 'num': 3, 'args': ['arg', 'arg', 'arg']},
    'STO': {'op': 4, 'num': 2, 'args': ['arg', 'value']},
    'ADD': {'op': 5, 'num': 3, 'args': ['arg', 'arg', 'arg']},
    'JMP': {'op': 6, 'num': 1, 'args': ['value', 'zero', 'zero']},
    'SUB': {'op': 7, 'num': 3, 'args': ['arg', 'arg', 'arg']},
    'IMUL': {'op': 8, 'num': 2, 'args': ['zero' 'arg', 'arg']},
    'IMUL_4': {'op': 9, 'num': 2, 'args': ['zero', 'arg', 'arg']},
    'IMUL_LUT': {'op': 10, 'num': 2, 'args': ['zero', 'arg', 'arg']},
    'IMUL_GEN': {'op': 11, 'num': 2, 'args': ['zero', 'arg', 'arg']},
    'MOVE_UPP': {'op': 12, 'num': 1, 'args': ['arg', 'zero', 'zero']},
    'MOVE_DOWN': {'op': 13, 'num': 1, 'args': ['arg', 'zero', 'zero']}
}
TAGS = {}
CONSTANTS = {}

ROM_TEMPLATE = Template('''/*
This module was out generated using maasm, MiniAlu's assembler
report any bug to javinachop@gmail.com

maasm is distributed under GNU GPL see <http://www.gnu.org/licenses/>
*/
`ifndef ROM_A
`define ROM_A


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
`endif //ROM_A
''')


def map_args(arg):
    try:
        if re.match('R\d{1,2}', arg):
            return '{0:08b}'.format(int(arg.split('R', 1)[1]))
        elif arg in TAGS:
            return '{0:08b}'.format(TAGS[arg])
        elif arg in CONSTANTS:
            return '{0:08b}'.format(CONSTANTS[arg])
        else:
            return '{0:016b}'.format(int(arg))
    except:
        raise Exception('Invalid argument {}'.format(arg))

@click.command()
@click.argument('filename', type=click.File('rb'))
@click.argument('output', type=click.File('wb'))
def main(filename, output):
    asm = []
    text = filename.read().decode('utf-8')
    text = re.sub(r'(?m)^ *#.*\n?', '', text) \
             .replace(' ', '').replace('\t', '').splitlines()
    text = [line for line in text if line.strip() != '']
    for i in range(len(text)):
        match = re.match('(\w*):', text[i])
        if match:
            TAGS[match.group(1)] = i-len(TAGS)
        elif re.match(r'\w*=\d*', text[i]):
            line = text[i].split('=')
            CONSTANTS[line[0]] = line[1]

    for line in text:
        ins = line.split('#', 1)[0]
        if ins:
            ins = ins.split(',')
            if re.match(r'(\w*):', ins[0]) or re.match(r'\w*=\d*', ins[0]):
                continue
            elif ins[0] in INS:
                if len(ins) == (INS[ins[0]]['num'] + 1):

                    asm_line = [
                        "28'b",
                        '{0:04b}'.format(INS[ins[0]]['op']),
                    ]
                    iter_args = iter(ins[1:])
                    for arg in INS[ins[0]]['args']:
                        if arg == 'zero':
                            asm_line.append('00000000')
                        else:
                            try:
                                asm_line.append(map_args(next(iter_args)))
                            except Exception as err:
                                raise Exception(
                                    'Unable to parse'
                                    ' args on instruction: {}'.format(line)
                                ) from err
                    asm.append(''.join(asm_line))

                else:
                    raise Exception(
                        'Wrong number of'
                        ' arguments on instruction {}'.format(line)
                    )

            else:
                raise Exception(
                    'Invalid operation'
                    ' on instruction {}'.format(line)
                )

    output.write(ROM_TEMPLATE.render(asm=asm).encode('utf-8'))


if __name__ == '__main__':
    main()
