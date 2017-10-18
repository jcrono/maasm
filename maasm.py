 #!/usr/bin/python3
import re
from jinja2 import Template
from collections import OrderedDict
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
        'args': [('zero', 8), ('arg',8), ('zero', 8)]
    },
    'BLE': {
        'op': 3,
        'num': 3,
        'args': [('arg', 8), ('arg', 8), ('arg', 8)]
    },
    'STO': {
        'op': 4,
        'num': 2,
        'args': [('arg', 8), ('value', 16)]
    },
    'ADD': {
        'op': 5,
        'num': 3,
        'args': [('arg', 8), ('arg', 8), ('arg', 8)]
    },
    'JMP': {
        'op': 6,
        'num': 1,
        'args': [('value', 16), ('zero', 8), ('zero', 8)]
    },
    '_config': {
        'ins_len': 28,
        'opcode_len': 4,
    }
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
        elif re.match(r'\d', arg):
            return '{{0:0{}b}}'.format(length).format(str2int(arg))
        else:
            raise Exception('Undefined Symbol: {}').format(arg)

    elif kind == 'reg':
        if re.match(r'R\d{1,2}', arg):
            return '{{0:0{}b}}'.format(length).format(
                int(arg.split('R', 1)[1])
            )
        else:
            raise Exception('Malformed register expression {}'.fromat(arg))

    else:
        raise Exception('Invaild type {}').format(kind)


def expand_macro(text, macros_dict):
    expanded_text = list(text)
    for i in range(len(text)):
        line = text[i].split('#', 1)[0]
        if re.match(r'(\w*):', line[0]) or re.match(r'\w*=\d*', line[0]):
            continue
        else:
            ins = line.split[',']
        if ins[0] in macros_dict:
            expanded_text[i] = macros_dict[ins[0]]['func'](ins[1:])
    return [item for sublist in expanded_text[i] for item in sublist]


def resolve_symbols(text):
    whitelines = len([line for line in text if line.strip() == ''])
    for i in range(len(text)):
        if re.match(r'\w*=\d*(\s*#\s*\w*)?', text[i]):
            line = text[i].split('#', 1)[0].split('=')
            try:
                CONSTANTS[line[0]] = str2int(line[1])
            except Exception as err:
                raise Exception(
                    '{}: Unable to parse'
                    ' constant expression {}'.format(text[i])
                ) from err

    for i in range(len(text)):
        match = re.match('(\w*):(\s*#\s*\w*)?', text[i])
        if match:
            TAGS[match.group(1)] = i-len(TAGS)-len(CONSTANTS)-whitelines


def asemble(text, asm_def):
    bytecode = []
    for index, line in enumerate(text):
        if line == '':
            continue

        ins = line.split('#', 1)[0]
        if ins:
            ins = ins.split(',')
            if re.match(r'(\w*):', ins[0]) or re.match(r'\w*=\d*', ins[0]):
                continue

            elif ins[0] in asm_def:
                if len(ins) == (asm_def[ins[0]]['num'] + 1):

                    # FIXME: Make length configurable
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
    text = re.sub(r'(?m)^\s*#.*\n?', '', text).splitlines()
    clean_text = []
    for line in text:
        clean_text.append(re.sub(r'\s', '', line))
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
    output.write(ROM_TEMPLATE.render(asm=bytecode).encode('utf-8'))


if __name__ == '__main__':
    main()
