 #!/usr/bin/python3
import re
import collections
from jinja2 import Template
import click
DEFAULT_INS = {
    'NOP': {
        'op': 0,
        'num': 0,
        'args': [('zero', 24)]
    },
    'LED': {
        'op': 2,
        'num': 1,
        'args': [('zero', 8), ('reg',8), ('zero', 8)]
    },
    'BLE': {
        'op': 3,
        'num': 3,
        'args': [('reg', 8), ('reg', 8), ('reg', 8)]
    },
    'STO': {
        'op': 4,
        'num': 2,
        'args': [('reg', 8), ('value', 16)]
    },
    'ADD': {
        'op': 5,
        'num': 3,
        'args': [('reg', 8), ('reg', 8), ('reg', 8)]
    },
    'JMP': {
        'op': 6,
        'num': 1,
        'args': [('value', 16), ('zero', 8)]
    },
    '_config': {
                'addr_len': 8,
                'ins_len': 28,
                'opcode_len': 4,
    }
}
REGS = {
    '$0': 0,
    '$1': 1,
    '$2': 2,
    '$3': 3,
    '$4': 4,
    '$5': 5,
    '$6': 6,
    '$7': 7,
    '$8': 8,
    '$9': 9,
    '$10': 10,
    '$11': 11,
    '$12': 12,
    '$13': 13,
    '$14': 14,
    '$15': 15,
    '$16': 16,
    '$17': 17,
    '$18': 18,
    '$19': 19,
    '$20': 20,
    '$21': 21,
    '$22': 22,
    '$23': 23,
    '$24': 24,
    '$25': 25,
    '$26': 26,
    '$27': 27,
    '$28': 28,
    '$29': 29,
    '$30': 30,
    '$31': 31,
    '$zero': 0,
    '$r0': 0,
    '$at': 1,
    '$v0': 2,
    '$v1': 3,
    '$a0': 4,
    '$a1': 5,
    '$a2': 6,
    '$a3': 7,
    '$t0': 8,
    '$t1': 9,
    '$t2': 10,
    '$t3': 11,
    '$t4': 12,
    '$t5': 13,
    '$t6': 14,
    '$t7': 15,
    '$s0': 16,
    '$s1': 17,
    '$s2': 18,
    '$s3': 19,
    '$s4': 20,
    '$s5': 21,
    '$s6': 22,
    '$s7': 23,
    '$t8': 24,
    '$t9': 25,
    '$k0': 26,
    '$k1': 27,
    '$gp': 28,
    '$sp': 29,
    '$fp': 30,
    '$ra': 31
}
TAGS = {}
CONSTANTS = {}

COMMENT_REGEX= r'#|\.'
ROM_TEMPLATE = Template('''/*
This module was out generated using maasm, MiniAlu's assembler
report any bug to javinachop@gmail.com

maasm is distributed under GNU GPL see <http://www.gnu.org/licenses/>
*/
`ifndef ROM_A
`define ROM_A


`timescale 1ns / 1ps
module ROM(
	   input wire [{{addr_len}}:0] iAddress,
	   output reg [{{ins_len}}:0] oInstruction
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


def flatten(l):
    for el in l:
        if isinstance(el, collections.Iterable) and not isinstance(
                                el, (str, bytes)):
            yield from flatten(el)
        else:
            yield el


def str2int(num):
            try:
                return int(num)
            except:
                pass
            try:
                return int(num, 2)
            except:
                pass
            try:
                return int(num, 6)
            except:
                pass
            try:
                return int(num, 8)
            except:
                raise Exception(
                    'Unable to parse experssion {} to int '.format(num)
                )


def map_args(kind, length, arg=None):
    if kind == 'zero':
        return '{{0:0{}b}}'.format(length).format(0)

    elif kind == 'value':
        if arg in TAGS:
            return '{{0:0{}b}}'.format(length).format(TAGS[arg])
        elif arg in CONSTANTS:
            return '{{0:0{}b}}'.format(length).format(CONSTANTS[arg])
        elif re.match(r'-?\d', arg):
            return '{{0:0{}b}}'.format(length).format(str2int(arg))
        else:
            raise Exception('Undefined Symbol: {}'.format(arg))

    elif kind == 'reg':
        if arg in REGS:
            return '{{0:0{}b}}'.format(length).format(REGS[arg])
        else:
            raise Exception('Malformed register expression {}'.format(arg))

    else:
        raise Exception('Invaild type {}'.format(kind))


def expand_macro(text, macros_dict):
    expanded_text = text
    for i in range(len(text)):
        line = re.split(COMMENT_REGEX, text[i], 1)[0]
        if re.match(r'(\$?\w*):', line[0]) or re.match(r'\$?\w*=\d*', line[0]):
            continue
        else:
            ins = list(filter(None, re.split('[\s,]', line)))
        if ins[0] in macros_dict:
            expanded_text[i] = macros_dict[ins[0]]['func'](ins[1:])
    return list(flatten(expanded_text))


def resolve_symbols(text):
    whitelines = 0
    for i in range(len(text)):
        if text[i].strip() == '':
            whitelines += 1
        elif re.match(r'\w*=\d*(\s*#\s*\w*)?', text[i]):
            line = text[i].split('#', 1)[0].split('=')
            try:
                CONSTANTS[line[0]] = str2int(line[1])
            except Exception as err:
                raise Exception(
                    '{}: Unable to parse'
                    ' constant expression {}'.format(text[i])
                ) from err

    whitelines = 0
    for i in range(len(text)):
        match = re.match('(\$?\w*):(\s*#\s*\w*)?', text[i])
        if match:
            TAGS[match.group(1)] = i-len(TAGS)-len(CONSTANTS)-whitelines
        elif text[i].strip() == '':
            whitelines += 1


def asemble(text, asm_def):
    bytecode = []
    for index, line in enumerate(text):
        if line == '':
            continue

        ins = line.split('#', 1)[0]
        if ins:
            ins = list(filter(None, re.split('[\s,]', ins)))
            if re.match(r'(\$?\w*):', ins[0]) or re.match(r'\w*=\d*', ins[0]):
                continue

            elif ins[0] in asm_def:
                if len(ins) == (asm_def[ins[0]]['num'] + 1):
                    if ins[0] in ['sw', 'lw']:
                        ins[2], ins[3] = ins[3], ins[2]
                    bytecode_line = [
                        '{{0:0{}b}}'.format(
                            asm_def['_config']['opcode_len']
                        ).format(asm_def[ins[0]]['op']),
                    ]
                    iter_args = iter(ins[1:])
                    for arg in asm_def[ins[0]]['args']:
                        kind = arg[0]
                        length = arg[1]
                        if kind == 'zero':
                            bytecode_line.append(map_args(kind, length))
                        else:
                            try:
                                bytecode_line.append(
                                    map_args(kind, length, next(iter_args))
                                )
                            except Exception as err:
                                raise Exception(
                                    '{}: Unable to parse'
                                    ' args on instruction: {}'.format(
                                        index, line
                                    )
                                ) from err
                    if len(''.join(bytecode_line)) \
                       != asm_def['_config']['ins_len']:
                                raise Exception(
                                            ('{}: Instruction has different '
                                             'size than expected, '
                                             'line {}').format(index, line))
                    bytecode.append(''.join(bytecode_line))

                else:
                    raise Exception(
                        '{}: Wrong number of'
                        ' arguments on instruction {}'.format(index, line)
                    )

            else:
                raise Exception(
                    '{}: Invalid operation'
                    ' on instruction {}'.format(index, line)
                )
    return bytecode


def generate_rom(text):
    pass


@click.command()
@click.argument('filename', type=click.File('rb'))
@click.argument('output', type=click.File('wb'))
@click.option(
    '--asm-dict', default=None, type=click.File('rb'),
    help='File containing a python dictionary with the asm instructions set')
@click.option(
    '--macros', default=None,
    help='File containing a python module with macro definitions')
def main(filename, output, asm_dict, macros):
    ''' Transforms from MiniAlu assembly to a verilog ROM module

    FILENAME: Input asm file

    OUTPUT: Output verilog ROM module file
'''
    if macros:
        import sys
        import os.path
        from importlib import import_module
        m_path = os.path.abspath(
            os.path.expandvars(
                os.path.expanduser(
                    macros
                )
            )
        )
        m_dir = os.path.dirname(m_path)
        sys.path.insert(0, m_dir)
        m_name = os.path.basename(m_path).split('.')[0]
        macro_module = import_module(m_name)
        macros_dict = macro_module.init_macros()

    if asm_dict:
        asm_tree = eval(asm_dict.read().decode('utf-8'))
    else:
        asm_tree = DEFAULT_INS

    text = filename.read().decode('utf-8')
    text = re.sub(r'(?m)^\s*(#|\.).*\n?', '', text).splitlines()
    clean_text = text
    if macros:
        expanded_text = expand_macro(clean_text, macros_dict)
    else:
        expanded_text = clean_text
    resolve_symbols(expanded_text)
    bytecode = asemble(expanded_text, asm_tree)
    bytecode = [
        ''.join(
            ["{}'b".format(asm_tree['_config']['ins_len']), line]
        ) for line in bytecode
    ]

    output.write(ROM_TEMPLATE.render(
                asm=bytecode,
                addr_len=asm_tree['_config']['addr_len']-1,
                ins_len=asm_tree['_config']['ins_len']-1
    ).encode('utf-8'))


if __name__ == '__main__':
    main()
