import sys
import os

def get_assembly():
    if len(sys.argv) != 2:
        print("Usage: python assembler.py <filename>")
        exit()
    return {
        "folder": os.path.dirname(sys.argv[1]),
        "filename": os.path.basename(sys.argv[1]),
        "content": open(sys.argv[1], "r").read()
    }

class IntegerConverter:
    def decimal_to_binary(self, number: int):
        return bin(number)[2:]
    def binary_to_decimal(self, binary_string: str):
        return int(binary_string, 2)

class InstructionsParser:
    def __init__(self, assembly: str):
        self.assembly = assembly

    def __get_instruction(self, line: str) -> str:
        # remove comments and whitespace
        return line.split('//')[0].strip()

    def get_instructions(self) -> list:
        instructions = []
        for line in self.assembly.split('\n'):
            instruction = self.__get_instruction(line)
            if not instruction: continue
            instructions.append(instruction)
        return instructions

class AddressParser:
    __labels = {}
    __symbols = {}
    __instructions = []
    __builtin_addresses = {
        'R0': 0,
        'R1': 1,
        'R2': 2,
        'R3': 3,
        'R4': 4,
        'R5': 5,
        'R6': 6,
        'R7': 7,
        'R8': 8,
        'R9': 9,
        'R10': 10,
        'R11': 11,
        'R12': 12,
        'R13': 13,
        'R14': 14,
        'R15': 15,
        'SCREEN': 16384,
        'KBD': 24576,
        'SP': 0,
        'LCL': 1,
        'ARG': 2,
        'THIS': 3,
        'THAT': 4
    }
    __closed_addresses = []

    def __init__(self, instructions: list):
        self.__instructions = instructions
        self.__parse()
    
    def __is_label(self, instruction: str) -> bool:
        return instruction.startswith('(') and instruction.endswith(')')
    def __get_label_name(self, instruction: str) -> str:
        if not self.__is_label(instruction): return None
        return instruction[1:-1]
    def __get_symbol_name(self, instruction):
        if not instruction.startswith('@'): return None
        if not instruction[1:].isdigit(): return instruction[1:]
        return None
    def __get_free_address(self) -> int:
        start = 16  # RAM[16] is the first free address
        end = 16384  # RAM[16384-1] is the last free address
        for address in range(start, end):
            if address in self.__closed_addresses: continue
            self.__closed_addresses.append(address)
            return address
        return None

    def __parse_labels(self):
        for instruction_index in range(len(self.__instructions)):
            instruction = self.__instructions[instruction_index]
            if not self.__is_label(instruction): continue
            label_name = self.__get_label_name(instruction)
            self.__labels[label_name] = instruction_index-len(self.__labels)

    def __parse_symbols(self):
        for instruction in self.__instructions:
            symbol = self.__get_symbol_name(instruction)
            if symbol is None: continue
            if symbol in self.__symbols: continue
            if symbol in self.__builtin_addresses: continue
            if symbol in self.__labels: continue
            self.__symbols[symbol] = self.__get_free_address()

    def __parse(self):
        self.__parse_labels()
        self.__parse_symbols()
    
    def __to_address(self, symbol: str) -> str:
        return "@%d" % symbol
        
    def get_address(self, symbol: str) -> str:
        if symbol is None: return None
        if symbol in self.__builtin_addresses: return self.__to_address(self.__builtin_addresses[symbol])
        if symbol in self.__labels: return self.__to_address(self.__labels[symbol])
        if symbol in self.__symbols: return self.__to_address(self.__symbols[symbol])
        return None

class Assembler:
    __instructions = []
    __addresses = None
    __integer_converter = IntegerConverter()
    def __init__(self, assembly: str):
        self.assembly = assembly
        self.__instructions = InstructionsParser(self.assembly).get_instructions()
        self.__addresses = AddressParser(self.__instructions)
    
    def __get_symbol_name(self, instruction):
        if not instruction.startswith('@'): return None
        if not instruction[1:].isdigit(): return instruction[1:]
        return None
    def __is_label(self, instruction: str) -> bool:
        return instruction.startswith('(') and instruction.endswith(')')
    
    def __get_destination(self, instruction: str) -> str:
        if self.__is_label(instruction): return None
        if instruction.startswith('@'): return None
        if '=' not in instruction: return None
        return instruction.split('=')[0].strip()
    def __get_comp(self, instruction: str) -> str:
        if self.__is_label(instruction): return None
        if instruction.startswith('@'): return None
        if '=' not in instruction: return instruction.split(';')[0].strip()
        return instruction.split('=')[1].strip()
    def __get_jump(self, instruction: str) -> str:
        if self.__is_label(instruction): return None
        if instruction.startswith('@'): return None
        if ';' not in instruction: return None
        return instruction.split(';')[1].strip()

    def __get_A_binary_instruction(self, address_value: int) -> str:
        # A-instruction
        #   symbolic: @symbol
        #   binary: 0(15bits value)
        return "0%s" % self.__integer_converter.decimal_to_binary(address_value).zfill(15)

    def __get_C_binary_instruction(self, dest: str, comp: str, jump: str) -> str:
        # C-instruction
        #   symbolic: dest=comp;jump
        #   binary: 1  1  1  a  c1 c2 c3 c4 c5 c6 d1 d2 d3 j1 j2 j3
        #          (15 14 13 12 11 10 9  8  7  6  5  4  3  2  1  0)
        comp_table = {
            '0': '0101010',
            '1': '0111111',
            '-1': '0111010',
            'D': '0001100',
            'A': '0110000',
            'M': '1110000',
            '!D': '0001101',
            '!A': '0110001',
            '!M': '1110001',
            '-D': '0001111',
            '-A': '0110011',
            '-M': '1110011',
            'D+1': '0011111',
            'A+1': '0110111',
            'M+1': '1110111',
            'D-1': '0001110',
            'A-1': '0110010',
            'M-1': '1110010',
            'D+A': '0000010',
            'D+M': '1000010',
            'D-A': '0010011',
            'D-M': '1010011',
            'A-D': '0000111',
            'M-D': '1000111',
            'D&A': '0000000',
            'D&M': '1000000',
            'D|A': '0010101',
            'D|M': '1010101',
        }
        dest_table = {
            None: '000',
            'M': '001',
            'D': '010',
            'MD': '011',
            'A': '100',
            'AM': '101',
            'AD': '110',
            'AMD': '111',
        }
        jump_table = {
            None: '000',
            'JGT': '001',
            'JEQ': '010',
            'JGE': '011',
            'JLT': '100',
            'JNE': '101',
            'JLE': '110',
            'JMP': '111',
        }
        return "111%s%s%s" % (comp_table[comp], dest_table[dest], jump_table[jump])

    def __to_binary_instruction(self, instruction: str) -> str:
        isAInstruction = instruction.startswith('@')
        if isAInstruction:
            address_value = int(instruction[1:])
            return self.__get_A_binary_instruction(address_value)
        destination = self.__get_destination(instruction)
        comp = self.__get_comp(instruction)
        jump = self.__get_jump(instruction)
        return self.__get_C_binary_instruction(destination, comp, jump)
    
    def __to_symbol_less_instruction(self, instruction: str) -> str:
        symbol = self.__get_symbol_name(instruction)
        if symbol is None and not self.__is_label(instruction):
            return instruction
        address = self.__addresses.get_address(symbol)
        if address is None: return ''
        return address
    
    def get_symbol_less_program(self) -> list:
        notEmpty = lambda instruction: instruction
        return filter(notEmpty, [self.__to_symbol_less_instruction(instruction) for instruction in self.__instructions])
        
    def get_binary_program(self) -> list:
        symbol_less_instructions = self.get_symbol_less_program()
        return [self.__to_binary_instruction(instruction) for instruction in symbol_less_instructions]
    
if __name__ == "__main__":
    # clear screen
    os.system('cls' if os.name == 'nt' else 'clear')
    try:
        assembly = get_assembly()
        assembler = Assembler(assembly["content"])
        with open("%s/%s.hack" % (assembly["folder"], assembly["filename"].split('.')[0]), "w") as output:
            for instruction in assembler.get_binary_program():
                output.write(instruction + '\n')
        output_file = "%s/%s.hack" % (assembly["folder"], assembly["filename"].split('.')[0])
        print("Successfully assembled %s!" % assembly["filename"])
        print("Output file: %s" % os.path.abspath(output_file))
    except Exception as err:
        print("Error: Could not assemble the file due to the following error:", err)
    
