 # Maasm

 MiniAlu ASeMbly is a program to tranform from assembly code to a
 verilog ROM module.

 ## Instalation

 To install maasm run
 ```shell
 setup.py install
 ```
 on the proyect root. This install the maasm command.

 ## Custom Instruction set

 Maasm uses by default the instruction set that was given with the
 MiniAlu code on the first lab's class. In order to use a different
 instruction set you must create a file which contain a python dict
 where each entry has the following format:

 ```python
 'INSTRUCTION': {'op': opcode, 'num': num_of_args, 'args': [args_type] }
 ```
Args type has three posible values:

- 'reg': a register
- 'zero': 8 zeros
- 'value': a inmediate value, constant or label

Example instruction set file:

```python
{
    'NOP': {'op': 0, 'num': 0, 'args': ['zero', 'zero', 'zero']},
    'LED': {'op': 2,  'num': 1, 'args': ['zero', 'arg', 'zero']},
    'BLE': {'op': 3, 'num': 3, 'args': ['arg', 'arg', 'arg']},
    'STO': {'op': 4, 'num': 2, 'args': ['arg', 'value']},
    'ADD': {'op': 5, 'num': 3, 'args': ['arg', 'arg', 'arg']},
    'JMP': {'op': 6, 'num': 1, 'args': ['value', 'zero', 'zero']},
    'SUB': {'op': 7, 'num': 3, 'args': ['arg', 'arg', 'arg']},
    'IMUL': {'op': 8, 'num': 2, 'args': ['zero', 'arg', 'arg']},
    'IMUL_4': {'op': 9, 'num': 2, 'args': ['zero', 'arg', 'arg']},
    'IMUL_LUT': {'op': 10, 'num': 2, 'args': ['zero', 'arg', 'arg']},
    'IMUL_GEN': {'op': 11, 'num': 2, 'args': ['zero', 'arg', 'arg']},
    'MOVE_UPP': {'op': 12, 'num': 1, 'args': ['arg', 'zero', 'zero']},
    'MOVE_DOWN': {'op': 13, 'num': 1, 'args': ['arg', 'zero', 'zero']}
}
```
To use the custom set pass the --asm-tree flag to the command
