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
import traceback
from uuid import uuid4
import os
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

    def _standardize_arg(self, cmd: str) -> list:
        return cmd.split('//')[0].strip().split(' ')

    def has_more_commands(self) -> bool:
        try:
            self.__current_command = self._standardize_arg(next(self.__current_instruction))
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
    __scope: str
    __caller_count: dict
    def __init__(self, output_file: TextIOWrapper) -> None:
        self.__output_file = output_file
        self.__output_file_name = os.path.basename(output_file.name).replace('.asm', '')
        self.__scope = self.__output_file_name
        self.__caller_count = {}

    def set_file_name(self, file_name: str) -> None:
        self.__output_file_name = file_name
        self.__scope = file_name

    def write_init(self) -> None:
        self.__output_file.write("// bootstrap code\n")
        # pseudo-code:
        #   sp = 256
        #   call Sys.init
        self.__output_file.write('@256\nD=A\n@SP\nM=D\n')
        self.write_call('Sys.init', 0)

    def write_label(self, label: str, use_raw: bool = False) -> None:
        label_asm = label if use_raw else f'{self.__scope}${label}'
        self.__output_file.write(f'({label_asm})\n')
    
    def write_goto(self, label: str, use_raw: bool = False) -> None:
        label_asm = label if use_raw else f'{self.__scope}${label}'
        self.__output_file.write(f'@{label_asm}\n0;JMP\n')

    def write_if(self, label: str) -> None:
        # pseudo-code:
        #   sp--, if *sp == -1 goto label
        self.__output_file.write(f'// if-goto {label}\n')
        self.__output_file.write(f'@SP\nAM=M-1\nD=M\n@{self.__scope}${label}\nD;JNE\n')
    
    def write_function(self, function_name: str, num_vars: int) -> None:
        self.__output_file.write(f'// function {function_name} {num_vars}\n')
        # pseudo-code:
        #   label function-name
        #   repeat num_vars times:
        #       push 0
        self.__scope = function_name
        self.write_label(function_name, use_raw=True)
        for _ in range(num_vars):
            self.write_push_pop(CommandType.C_PUSH, 'constant', 0)

    def write_call(self, function_name: str, num_args: int) -> None:
        self.__output_file.write(f'// call {function_name} {num_args}\n')
        # pseudo-code:
        #   push return_address
        #   push LCL
        #   push ARG
        #   push THIS
        #   push THAT
        #   ARG = SP - num_args - 5
        #   LCL = SP
        #   goto function-name
        #   label return_address
        if function_name not in self.__caller_count:
            self.__caller_count[function_name] = 0
        return_address = f'{function_name}$ret.{self.__caller_count[function_name]}'
        self.__output_file.write(f'// push ret_adr\n@{return_address}\nD=A\n@SP\nA=M\nM=D\n@SP\nM=M+1\n')
        self.__output_file.write(f'// push LCL\n@LCL\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1\n')
        self.__output_file.write(f'// push ARG\n@ARG\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1\n')
        self.__output_file.write(f'// push THIS\n@THIS\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1\n')
        self.__output_file.write(f'// push THAT\n@THAT\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1\n')
        self.__output_file.write(f'// ARG=SP-num_args-5\n@SP\nD=M\n@{num_args}\nD=D-A\n@5\nD=D-A\n@ARG\nM=D\n')
        self.__output_file.write(f'// LCL=SP\n@SP\nD=M\n@LCL\nM=D\n')
        self.write_goto(function_name, use_raw=True)
        self.write_label(return_address, use_raw=True)
        self.__caller_count[function_name] += 1

    def write_return(self) -> None:
        self.__output_file.write('// return\n')
        # pseudo-code:
        #   endFrame = LCL // endframe is a temporary variable
        #   retAddr = *(endFrame – 5) // gets the return address
        #   *ARG = pop() // repositions the return value for the caller
        #   SP = ARG + 1 // repositions SP of the caller
        #   THAT = *(endFrame – 1) // restores THAT of the caller
        #   THIS = *(endFrame – 2) // restores THIS of the caller
        #   ARG = *(endFrame – 3) // restores ARG of the caller
        #   LCL = *(endFrame – 4) // restores LCL of the caller
        #   goto retAddr
        self.__output_file.write('@LCL\nD=M\n@R13\nM=D\n')
        self.__output_file.write('@5\nD=A\n@R13\nA=M-D\nD=M\n@R14\nM=D\n')
        self.__output_file.write('@SP\nAM=M-1\nD=M\n@ARG\nA=M\nM=D\n')
        self.__output_file.write('@ARG\nD=M\n@SP\nM=D+1\n')
        self.__output_file.write('@R13\nD=M\n@1\nD=D-A\nA=D\nD=M\n@THAT\nM=D\n')
        self.__output_file.write('@R13\nD=M\n@2\nD=D-A\nA=D\nD=M\n@THIS\nM=D\n')
        self.__output_file.write('@R13\nD=M\n@3\nD=D-A\nA=D\nD=M\n@ARG\nM=D\n')
        self.__output_file.write('@R13\nD=M\n@4\nD=D-A\nA=D\nD=M\n@LCL\nM=D\n')
        self.__output_file.write('@R14\nA=M\n0;JMP\n')

    def write_arithmetic(self, command: str) -> None:
        self.__output_file.write(f'// {command}\n')
        # pseudo-code:
        #   add: sp--, *(sp-1) = *sp + *(sp-1)
        #   sub: sp--, *(sp-1) = *sp - *(sp-1)
        #   neg: sp--, *(sp-1) = -*(sp-1)
        #   eq: sp--, *(sp-1) = *sp == *(sp-1)
        #   gt: sp--, *(sp-1) = *sp > *(sp-1)
        #   lt: sp--, *(sp-1) = *sp < *(sp-1)
        #   and: sp--, *(sp-1) = *sp & *(sp-1)
        #   or: sp--, *(sp-1) = *sp | *(sp-1)
        unique_id = uuid4()
        asm = {
            'add': '@SP\nAM=M-1\nD=M\nA=A-1\nM=M+D\n',
            'sub': '@SP\nAM=M-1\nD=M\nA=A-1\nM=M-D\n',
            'neg': '@SP\nA=M-1\nM=-M\n',
            'and': '@SP\nAM=M-1\nD=M\nA=A-1\nM=D&M\n',
            'or': '@SP\nAM=M-1\nD=M\nA=A-1\nM=D|M\n',
            'not': '@SP\nA=M-1\nM=!M\n',
            'eq': f"@SP\nAM=M-1\nD=M\nA=A-1\nM=M-D\nD=M\nM=-1\n@{unique_id}\nD;JEQ\n@SP\nA=M-1\nM=0\n({unique_id})\n",
            'gt': f"@SP\nAM=M-1\nD=M\nA=A-1\nM=M-D\nD=M\nM=-1\n@{unique_id}\nD;JGT\n@SP\nA=M-1\nM=0\n({unique_id})\n",
            'lt': f"@SP\nAM=M-1\nD=M\nA=A-1\nM=M-D\nD=M\nM=-1\n@{unique_id}\nD;JLT\n@SP\nA=M-1\nM=0\n({unique_id})\n"
        }
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

class Main:
    __sys_argv = sys.argv
    def __init__(self, *args) -> None:
        self.__sys_argv = args
        self.main()
    
    def __translate_file(self, vm_parser: Parser, vm_code_writer: CodeWriter) -> None:
        try:
            while vm_parser.has_more_commands():
                if vm_parser.command_type() == CommandType.C_ARITHMETIC:
                    vm_code_writer.write_arithmetic(vm_parser.get_command())
                elif vm_parser.command_type() in (CommandType.C_PUSH, CommandType.C_POP):
                    vm_code_writer.write_push_pop(vm_parser.command_type(), vm_parser.arg1(), vm_parser.arg2())
                elif vm_parser.command_type() == CommandType.C_LABEL:
                    vm_code_writer.write_label(vm_parser.arg1())
                elif vm_parser.command_type() == CommandType.C_GOTO:
                    vm_code_writer.write_goto(vm_parser.arg1())
                elif vm_parser.command_type() == CommandType.C_IF:
                    vm_code_writer.write_if(vm_parser.arg1())
                elif vm_parser.command_type() == CommandType.C_FUNCTION:
                    vm_code_writer.write_function(vm_parser.arg1(), vm_parser.arg2())
                elif vm_parser.command_type() == CommandType.C_CALL:
                    vm_code_writer.write_call(vm_parser.arg1(), vm_parser.arg2())
                elif vm_parser.command_type() == CommandType.C_RETURN:
                    vm_code_writer.write_return()
                vm_parser.advance()
        except FileNotFoundError:
            print(f'File {self.__sys_argv[1]} not found')
            print('Usage: python3 VMTranslator.py <file_name>')

    def __translate_directory(self, directory_name: str) -> None:
        try:
            if "Sys.vm" not in os.listdir(directory_name):
                raise FileNotFoundError("Sys.vm not found in directory")

            output_file = open(f'{directory_name}/{os.path.basename(directory_name)}.asm', 'w')
            vm_code_writer = CodeWriter(output_file)
            vm_code_writer.write_init()       
            for file_name in os.listdir(directory_name):
                if not file_name.endswith('.vm'): continue
                input_file = open(f'{directory_name}/{file_name}', 'r')
                vm_parser = Parser(input_file)
                vm_code_writer.set_file_name(file_name.replace('.vm', ''))
                self.__translate_file(vm_parser, vm_code_writer)
        except FileNotFoundError:
            print("Folder must contain Sys.vm\t(Sys.vm file must contain function Sys.init)")
            print("Usage:\tpython3 VMTranslator.py <directory_name>")
    
    def main(self) -> None:
        try:
            if os.path.isdir(self.__sys_argv[1]):
                self.__translate_directory(self.__sys_argv[1])
            else:
                vm_parser = Parser(open(self.__sys_argv[1], 'r'))
                vm_code_writer = CodeWriter(open(f"{self.__sys_argv[1].rsplit('.vm', 1)[0]}.asm", 'w'))
                self.__translate_file(vm_parser, vm_code_writer)
                vm_code_writer.close()
        except Exception as err:
            print(f"Error:\t {err}")
            traceback.print_exc()
        
if __name__ == "__main__":
    Main(*sys.argv)
