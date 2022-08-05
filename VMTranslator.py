# VM Language:
# Arithemetic commands: add, sub, neg, eq, gt, lt, and, or, not
# Memory access commands: 
#   push <segment> <index>
#   pop <segment> <index>
# Branch commands: 
#   label <label>
#   goto <label>
#   if-goto <label>
# Function commands: 
#   function <functionName> <nVars>
#   call <functionName> <nArgs>
#   return
from enum import Enum
from io import TextIOWrapper
from itertools import islice
import ntpath
from operator import eq
import sys

CommandType = Enum('CommandType', 'NotACommand C_ARITHMETIC C_PUSH C_POP C_LABEL C_GOTO C_IF C_FUNCTION C_CALL C_RETURN')
Syntax = {
    'add': CommandType.C_ARITHMETIC,
    'sub': CommandType.C_ARITHMETIC,
    'neg': CommandType.C_ARITHMETIC,
    'eq': CommandType.C_ARITHMETIC,
    'gt': CommandType.C_ARITHMETIC,
    'lt': CommandType.C_ARITHMETIC,
    'and': CommandType.C_ARITHMETIC,
    'or': CommandType.C_ARITHMETIC,
    'not': CommandType.C_ARITHMETIC,
    'push': CommandType.C_PUSH,
    'pop': CommandType.C_POP,
    'label': CommandType.C_LABEL,
    'goto': CommandType.C_GOTO,
    'if-goto': CommandType.C_IF,
    'function': CommandType.C_FUNCTION,
    'call': CommandType.C_CALL,
    'return': CommandType.C_RETURN
}
Segment = {
    'local': 'LCL',
    'argument': 'ARG',
    'this': 'THIS',
    'that': 'THAT',
    'temp': 'R5',
    'constant': '',
    'static': '',
    'pointer': ''
}

class Parser:
    __instructions: TextIOWrapper
    __current_instruction: object
    __current_command: list

    def __init__(self, input_file: TextIOWrapper) -> None:
        self.__instructions = input_file
        self.__current_instruction = islice(self.__instructions, 1)

    def has_more_commands(self) -> bool:
        try:
            self.__current_command = next(self.__current_instruction).replace('\n', '').split(' ')
            return True
        except StopIteration:
            return False
    def advance(self) -> None:
        self.__current_instruction = islice(self.__instructions, 1)
    def command_type(self) -> CommandType:
        try:
            return Syntax[self.__current_command[0]]
        except KeyError:
            return CommandType.NotACommand
    def get_command(self) -> str:
        return self.__current_command[0]
    def arg1(self) -> str:
        return self.__current_command[1]
    def arg2(self) -> int:
        return int(self.__current_command[2])

class CodeWriter:
    __output_file: TextIOWrapper
    __output_file_name: str
    __used_labels: dict
    def __init__(self, output_file: TextIOWrapper) -> None:
        self.__output_file = output_file
        self.__output_file_name = ntpath.basename(output_file.name).replace('.asm', '')
        self.__used_labels = {'eq': 0, 'gt': 0, 'lt': 0}
    def write_arithmetic(self, command: str) -> None:
        self.__output_file.write(f'// {command}\n')
        # pseudo-code:
        #   add: sp--, *(sp-1) = *sp + *(sp-1)
        #   sub: sp--, *(sp-1) = *sp - *(sp-1)
        asm = {
            'add': '@SP\nM=M-1\nA=M\nD=M\nA=A-1\nM=M+D\n',
            'sub': '@SP\nM=M-1\nA=M\nD=M\nA=A-1\nM=M-D\n',
            'neg': '@SP\nA=M-1\nM=-M\n',
            'and': '@SP\nM=M-1\nA=M\nD=M\nA=A-1\nM=D&M\n',
            'or': '@SP\nM=M-1\nA=M\nD=M\nA=A-1\nM=D|M\n',
            'not': '@SP\nA=M-1\nM=!M\n',
            'eq': f"@SP\nM=M-1\nA=M\nD=M\nA=A-1\nM=M-D\nD=M\nM=-1\n@StackTest_eq{self.__used_labels['eq']}\nD;JEQ\n@SP\nA=M-1\nM=0\n(StackTest_eq{self.__used_labels['eq']})\n",
            'gt': f"@SP\nM=M-1\nA=M\nD=M\nA=A-1\nM=M-D\nD=M\nM=-1\n@StackTest_gt{self.__used_labels['gt']}\nD;JGT\n@SP\nA=M-1\nM=0\n(StackTest_gt{self.__used_labels['gt']})\n",
            'lt': f"@SP\nM=M-1\nA=M\nD=M\nA=A-1\nM=M-D\nD=M\nM=-1\n@StackTest_lt{self.__used_labels['lt']}\nD;JLT\n@SP\nA=M-1\nM=0\n(StackTest_lt{self.__used_labels['lt']})\n"
        }
        if command in self.__used_labels:
            self.__used_labels[command] += 1
        self.__output_file.write(asm[command])
        
    def write_push_pop(self, command_type: CommandType, segment: str, index: int) -> None:
        self.__output_file.write(f'// {command_type.name} {segment} {index}\n')
        # pseudo-code:
        #   push: *sp = segment[index], sp++
        #   pop: sp--, segment[index] = *sp
        try:
            asm = {
                'constant': {
                    CommandType.C_PUSH: f'@{index}\nD=A\n@SP\nA=M\nM=D\n@SP\nM=M+1\n'
                },
                'temp': {
                    CommandType.C_PUSH: f'@{Segment[segment]}\nD=A\n@{index}\nA=D+A\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1\n',
                    CommandType.C_POP: f'@{index}\nD=A\n@{Segment[segment]}\nA=D+A\nD=A\n@R13\nM=D\n@SP\nM=M-1\nA=M\nD=M\n@R13\nA=M\nM=D\n'
                },
                'pointer': {
                    CommandType.C_PUSH: f'@{index and "THAT" or "THIS"}\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1\n',
                    CommandType.C_POP: f'@SP\nM=M-1\nA=M\nD=M\n@{index and "THAT" or "THIS"}\nM=D\n'
                },
                'static': {
                    CommandType.C_PUSH: f'@{self.__output_file_name}.{index}\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1\n',
                    CommandType.C_POP: f'@SP\nM=M-1\nA=M\nD=M\n@{self.__output_file_name}.{index}\nM=D\n'
                }
            }
            self.__output_file.write(asm[segment][command_type])
        except KeyError:
            asm = {
                CommandType.C_PUSH: f'@{Segment[segment]}\nD=M\n@{index}\nA=D+A\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1\n',
                CommandType.C_POP: f'@{index}\nD=A\n@{Segment[segment]}\nA=D+M\nD=A\n@R13\nM=D\n@SP\nM=M-1\nA=M\nD=M\n@R13\nA=M\nM=D\n'
            }
            self.__output_file.write(asm[command_type])
            
    def close(self) -> None:
        self.__output_file.write('(END)\n@END\n0;JMP\n')

def main(*args):
    try:
        input_file = open(args[1], 'r')
        output_file_name = '.asm'.join(args[1].rsplit('.vm', 1))
        output_file = open(output_file_name, 'w')
        
        vm_parser = Parser(input_file)
        vm_code_writer = CodeWriter(output_file)
        while vm_parser.has_more_commands():
            if vm_parser.command_type() == CommandType.C_ARITHMETIC:
                vm_code_writer.write_arithmetic(vm_parser.get_command())
            elif vm_parser.command_type() in (CommandType.C_PUSH, CommandType.C_POP):
                vm_code_writer.write_push_pop(vm_parser.command_type(), vm_parser.arg1(), vm_parser.arg2())
            elif vm_parser.command_type() == CommandType.C_LABEL:
                pass
            elif vm_parser.command_type() == CommandType.C_GOTO:
                pass
            elif vm_parser.command_type() == CommandType.C_IF:
                pass
            elif vm_parser.command_type() == CommandType.C_FUNCTION:
                pass
            elif vm_parser.command_type() == CommandType.C_CALL:
                pass
            elif vm_parser.command_type() == CommandType.C_RETURN:
                pass
            vm_parser.advance()
        vm_code_writer.close()
    except FileNotFoundError:
        print('File not found! Please check the file name.')
        print("Usage:\tpython3 VMTranslator.py <inputFileName>.vm")
    except Exception as err:
        print(f"Error:\t {err}")

if __name__ == "__main__":
    main(*sys.argv)
