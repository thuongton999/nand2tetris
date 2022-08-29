from io import TextIOWrapper
from JackAnalyzer import *
import sys
import os

KIND = enum(STATIC='static', FIELD='field', ARG='arg', VAR='var')
SEGMENT = enum(CONST='constant', ARG='argument', LOCAL='local', STATIC='static', THIS='this', THAT='that', POINTER='pointer', TEMP='temp')
ARITHMETIC = enum(ADD='add', SUB='sub', EQ='eq', GT='gt', LT='lt', AND='and', OR='or', NOT='not', NEG='neg')
KEYWORD = enum(CLASS='class', METHOD='method', FUNCTION='function', CONSTRUCTOR='constructor', INT='int', BOOLEAN='boolean', CHAR='char', VOID='void', VAR='var', STATIC='static', FIELD='field', LET='let', DO='do', IF='if', ELSE='else', WHILE='while', RETURN='return', TRUE='true', FALSE='false', NULL='null', THIS='this')
SYMBOL = enum(LEFT_PAREN='(', RIGHT_PAREN=')', LEFT_BRACE='{', RIGHT_BRACE='}', LEFT_BRACKET='[', RIGHT_BRACKET=']', COMMA=',', SEMICOLON=';', PERIOD='.', PLUS='+', MINUS='-', MULTIPLY='*', DIVIDE='/', AND='&', OR='|', NOT='~', EQ='=', LT='<', GT='>')
SEGMENT_BY_KIND = {
    KIND.STATIC: SEGMENT.STATIC, 
    KIND.FIELD: SEGMENT.THIS, 
    KIND.ARG: SEGMENT.ARG, 
    KIND.VAR: SEGMENT.LOCAL
}
ARITHMETIC_BY_SYMBOL = {
    SYMBOL.PLUS: ARITHMETIC.ADD,
    SYMBOL.MINUS: ARITHMETIC.SUB,
    SYMBOL.MULTIPLY: 'call Math.multiply 2',
    SYMBOL.DIVIDE: 'call Math.divide 2',
    SYMBOL.AND: ARITHMETIC.AND,
    SYMBOL.OR: ARITHMETIC.OR,
    SYMBOL.EQ: ARITHMETIC.EQ,
    SYMBOL.LT: ARITHMETIC.LT,
    SYMBOL.GT: ARITHMETIC.GT,
}

class OperatorStack:
    __scopes: list
    def __init__(self) -> None:
        self.__scopes = []

    def start_stack(self) -> None:
        self.__scopes.append([])

    def close_stack(self) -> None:
        self.__scopes.pop()

    def push(self, operator) -> None:
        self.__scopes[-1].append(operator)

    def pop(self):
        return self.__scopes[-1].pop()
    
    def is_empty(self) -> bool:
        if not self.__scopes: return True
        return len(self.__scopes[-1]) == 0

    def top(self) -> str:
        return self.__scopes[-1][-1]

class SymbolTable:
    __class_scope: dict
    __subroutine_scope: dict
    __var_counter: dict
    def __init__(self) -> None:
        self.__class_scope = {}
        self.__subroutine_scope = {}
        self.__var_counter = {KIND.STATIC: 0, KIND.FIELD: 0, KIND.ARG: 0, KIND.VAR: 0}

    def start_subroutine(self) -> None:
        self.__subroutine_scope = {}
        self.__var_counter[KIND.ARG] = 0
        self.__var_counter[KIND.VAR] = 0

    def define(self, name: str, type: str, kind: KIND) -> None:
        new_var = {'type': type, 'kind': kind, 'index': self.__var_counter[kind]}
        self.__var_counter[kind] += 1
        if kind == KIND.STATIC or kind == KIND.FIELD:
            self.__class_scope[name] = new_var
        else:
            self.__subroutine_scope[name] = new_var

    def var_count(self, kind: KIND) -> int:
        return self.__var_counter[kind]
    
    def kind_of(self, name: str) -> KIND:
        if name in self.__subroutine_scope: return self.__subroutine_scope[name]['kind']
        if name in self.__class_scope: return self.__class_scope[name]['kind']
        return None 

    def type_of(self, name: str) -> str:
        if name in self.__subroutine_scope: return self.__subroutine_scope[name]['type']
        if name in self.__class_scope: return self.__class_scope[name]['type']
        return None

    def index_of(self, name: str) -> int:
        if name in self.__subroutine_scope: return self.__subroutine_scope[name]['index']
        if name in self.__class_scope: return self.__class_scope[name]['index']
        return None
    
    def __str__(self) -> str:
        output = 'name\ttype\tkind\tindex\n'
        output += '\nClass Scope\n'
        for key in self.__class_scope:
            output += f'|{key}\t|{self.__class_scope[key]["type"]}\t|{self.__class_scope[key]["kind"]}\t|{self.__class_scope[key]["index"]}\t|\n'
        output += '\nSubroutine Scope\n'
        for key in self.__subroutine_scope:
            output += f'|{key}\t|{self.__subroutine_scope[key]["type"]}\t|{self.__subroutine_scope[key]["kind"]}\t|{self.__subroutine_scope[key]["index"]}\t|\n'
        return output

class VMWriter:
    __output_file: TextIOWrapper
    def __init__(self, output_file: TextIOWrapper) -> None:
        self.__output_file = output_file

    def write_push(self, segment: SEGMENT, index: int) -> None:
        self.__output_file.write(f'push {segment} {index}\n')

    def write_pop(self, segment: SEGMENT, index: int) -> None:
        self.__output_file.write(f'pop {segment} {index}\n')

    def write_arithmetic(self, command: ARITHMETIC) -> None:
        self.__output_file.write(f'{command}\n')
    
    def write_label(self, label: str) -> None:
        self.__output_file.write(f'label {label}\n')

    def write_goto(self, label: str) -> None:
        self.__output_file.write(f'goto {label}\n')

    def write_if(self, label: str) -> None:
        self.__output_file.write(f'if-goto {label}\n')

    def write_call(self, name: str, n_args: int) -> None:
        self.__output_file.write(f'call {name} {n_args}\n')

    def write_function(self, name: str, n_locals: int) -> None:
        self.__output_file.write(f'function {name} {n_locals}\n')

    def write_return(self) -> None:
        self.__output_file.write('return\n')

    def close(self) -> None:
        self.__output_file.close()

class JackCompiler:
    __tokenizer: JackTokenizer
    __symbol_table: SymbolTable
    __vm_writer: VMWriter
    __CLASS_VAR_DECS: tuple
    __STATEMENTS: tuple
    __OPERATORS: tuple
    __UNARY_OPERATORS: tuple

    __class_name: str
    __current_subroutine_name: str
    __current_subroutine_kind: KEYWORD
    __current_subroutine_type: str
    __operator_stack: OperatorStack
    __label_counter: dict
    def __init__(self, input_file: TextIOWrapper, output_file: TextIOWrapper) -> None:
        self.__symbol_table = SymbolTable()
        self.__tokenizer = JackTokenizer(input_file)
        self.__vm_writer = VMWriter(output_file)
        self.__operator_stack = OperatorStack()
        self.__CLASS_VAR_DECS = (KEYWORD.STATIC, KEYWORD.FIELD)
        self.__STATEMENTS = (KEYWORD.LET, KEYWORD.IF, KEYWORD.WHILE, KEYWORD.DO, KEYWORD.RETURN)
        self.__OPERATORS = (SYMBOL.PLUS, SYMBOL.MINUS, SYMBOL.MULTIPLY, SYMBOL.DIVIDE, SYMBOL.AND, SYMBOL.OR, SYMBOL.EQ, SYMBOL.LT, SYMBOL.GT)
        self.__UNARY_OPERATORS = (SYMBOL.MINUS, SYMBOL.NOT)
        self.__label_counter = {}

    def __current_scope(self) -> str:
        return f"{self.__class_name}.{self.__current_subroutine_name}"
    
    def __close(self) -> None:
        self.__vm_writer.close()
        self.__tokenizer.close()

    def __expect(self, token_type: TOKEN_TYPE, *token_values: tuple, advance=True) -> bool:
        if not self.__tokenizer.token_type() == token_type: return False
        if not self.__tokenizer.token_value() in token_values and token_values: return False
        if not self.__tokenizer.has_more_tokens() or not advance:  return True
        self.__tokenizer.advance()
        return True

    def __get_new_label(self, name: str) -> str:
        if name not in self.__label_counter: self.__label_counter[name] = 0
        self.__label_counter[name] += 1
        return f'{self.__current_scope()}${name}{self.__label_counter[name]}'

    def compile_class(self) -> None:
        if not self.__expect(TOKEN_TYPE.KEYWORD, KEYWORD.CLASS): return
        if not self.__expect(TOKEN_TYPE.IDENTIFIER, advance=False): return
        self.__class_name = self.__tokenizer.identifier()
        self.__tokenizer.advance()
        if not self.__expect(TOKEN_TYPE.SYMBOL, SYMBOL.LEFT_BRACE): return
        is_keyword = lambda token_type: token_type == TOKEN_TYPE.KEYWORD
        get_token_type = lambda: self.__tokenizer.token_type()
        get_keyword = lambda: self.__tokenizer.keyword()

        while is_keyword(get_token_type()) and get_keyword() in self.__CLASS_VAR_DECS:
            self.compile_class_var_dec()
        
        while not self.__expect(TOKEN_TYPE.SYMBOL, SYMBOL.RIGHT_BRACE):
            self.compile_subroutine() 
                
        self.__close()

    def compile_class_var_dec(self) -> None:
        var_type: str
        var_kind: KIND
        if not self.__expect(TOKEN_TYPE.KEYWORD, *self.__CLASS_VAR_DECS, advance=False): return
        var_kind = self.__tokenizer.keyword()
        self.__tokenizer.advance()
        if self.__expect(TOKEN_TYPE.IDENTIFIER, advance=False):
            var_type = self.__tokenizer.identifier()
            self.__tokenizer.advance()
        elif self.__expect(TOKEN_TYPE.KEYWORD, KEYWORD.INT, KEYWORD.CHAR, KEYWORD.BOOLEAN, advance=False):
            var_type = self.__tokenizer.keyword()
            self.__tokenizer.advance()
        else: return
        
        while self.__expect(TOKEN_TYPE.IDENTIFIER, advance=False):
            self.__symbol_table.define(self.__tokenizer.identifier(), var_type, var_kind)
            self.__tokenizer.advance()
            if not self.__expect(TOKEN_TYPE.SYMBOL, SYMBOL.COMMA): break
        self.__expect(TOKEN_TYPE.SYMBOL, SYMBOL.SEMICOLON)

    def compile_subroutine(self) -> None:
        self.__symbol_table.start_subroutine()
        if not self.__expect(TOKEN_TYPE.KEYWORD, KEYWORD.CONSTRUCTOR, KEYWORD.FUNCTION, KEYWORD.METHOD, advance=False): return
        self.__current_subroutine_kind = self.__tokenizer.keyword()
        self.__tokenizer.advance()
        if self.__current_subroutine_kind == KEYWORD.METHOD:
            self.__symbol_table.define('this', self.__class_name, KIND.ARG)
        if self.__expect(TOKEN_TYPE.IDENTIFIER, advance=False):
            self.__current_subroutine_type = self.__tokenizer.identifier()
            self.__tokenizer.advance()
        elif self.__expect(TOKEN_TYPE.KEYWORD, KEYWORD.VOID, KEYWORD.INT, KEYWORD.CHAR, KEYWORD.BOOLEAN, advance=False):
            self.__current_subroutine_type = self.__tokenizer.keyword()
            self.__tokenizer.advance()
        else: return
        if not self.__expect(TOKEN_TYPE.IDENTIFIER, advance=False): return
        self.__current_subroutine_name = self.__tokenizer.identifier()
        self.__tokenizer.advance()
        if not self.__expect(TOKEN_TYPE.SYMBOL, SYMBOL.LEFT_PAREN): return
        self.compile_parameter_list()
        if not self.__expect(TOKEN_TYPE.SYMBOL, SYMBOL.RIGHT_PAREN): return
        self.compile_subroutine_body()

    def compile_parameter_list(self) -> None:
        var_type: str
        while self.__expect(TOKEN_TYPE.IDENTIFIER, advance=False) or self.__expect(TOKEN_TYPE.KEYWORD, KEYWORD.INT, KEYWORD.CHAR, KEYWORD.BOOLEAN, advance=False):
            var_type = self.__tokenizer.keyword() if self.__tokenizer.token_type() == TOKEN_TYPE.KEYWORD else self.__tokenizer.identifier()
            self.__tokenizer.advance()
            if not self.__expect(TOKEN_TYPE.IDENTIFIER, advance=False): return
            self.__symbol_table.define(self.__tokenizer.identifier(), var_type, KIND.ARG)
            self.__tokenizer.advance()
            if not self.__expect(TOKEN_TYPE.SYMBOL, SYMBOL.COMMA): break

    def compile_subroutine_body(self) -> None:
        if not self.__expect(TOKEN_TYPE.SYMBOL, SYMBOL.LEFT_BRACE): return
        while self.__expect(TOKEN_TYPE.KEYWORD, KEYWORD.VAR, advance=False):
            self.compile_var_dec()
        # generate vm code for subroutine body
        self.__vm_writer.write_function(self.__current_scope(), self.__symbol_table.var_count(KIND.VAR))
        if self.__current_subroutine_kind == KEYWORD.CONSTRUCTOR:
            self.__vm_writer.write_push(SEGMENT.CONST, self.__symbol_table.var_count(KIND.FIELD))
            self.__vm_writer.write_call('Memory.alloc', 1)  # allocate memory for object
            self.__vm_writer.write_pop(SEGMENT.POINTER, 0)  # set 'this' to point to the argument 0
        elif self.__current_subroutine_kind == KEYWORD.METHOD:
            self.__vm_writer.write_push(SEGMENT.ARG, 0) 
            self.__vm_writer.write_pop(SEGMENT.POINTER, 0)  # set 'this' to point to the argument 0

        self.compile_statements()
        self.__expect(TOKEN_TYPE.SYMBOL, SYMBOL.RIGHT_BRACE)

    def compile_var_dec(self) -> None:
        var_type: str
        if not self.__expect(TOKEN_TYPE.KEYWORD, KEYWORD.VAR): return
        if self.__expect(TOKEN_TYPE.IDENTIFIER, advance=False):
            var_type = self.__tokenizer.identifier()
            self.__tokenizer.advance()
        elif self.__expect(TOKEN_TYPE.KEYWORD, KEYWORD.INT, KEYWORD.CHAR, KEYWORD.BOOLEAN, advance=False):
            var_type = self.__tokenizer.keyword()
            self.__tokenizer.advance()
        else: return
        while self.__expect(TOKEN_TYPE.IDENTIFIER, advance=False):
            self.__symbol_table.define(self.__tokenizer.identifier(), var_type, KIND.VAR)
            self.__tokenizer.advance()
            if not self.__expect(TOKEN_TYPE.SYMBOL, SYMBOL.COMMA): break
        self.__expect(TOKEN_TYPE.SYMBOL, SYMBOL.SEMICOLON)

    def compile_statements(self) -> None:
        while self.__expect(TOKEN_TYPE.KEYWORD, *self.__STATEMENTS, advance=False):
            if self.__tokenizer.keyword() == KEYWORD.LET: self.compile_let()
            elif self.__tokenizer.keyword() == KEYWORD.IF: self.compile_if()
            elif self.__tokenizer.keyword() == KEYWORD.WHILE: self.compile_while()
            elif self.__tokenizer.keyword() == KEYWORD.DO: self.compile_do()
            elif self.__tokenizer.keyword() == KEYWORD.RETURN: self.compile_return()
            else: return

    def compile_let(self) -> None:
        if not self.__expect(TOKEN_TYPE.KEYWORD, KEYWORD.LET): return
        if not self.__expect(TOKEN_TYPE.IDENTIFIER, advance=False): return
        var_name = self.__tokenizer.identifier()
        var_segment = SEGMENT_BY_KIND[self.__symbol_table.kind_of(var_name)]
        var_index = self.__symbol_table.index_of(var_name)
        is_array = False
        self.__tokenizer.advance()
        if self.__expect(TOKEN_TYPE.SYMBOL, SYMBOL.LEFT_BRACKET):
            is_array = True
            self.compile_expression()
            if not self.__expect(TOKEN_TYPE.SYMBOL, SYMBOL.RIGHT_BRACKET): return
            self.__vm_writer.write_push(var_segment, var_index)
            self.__vm_writer.write_arithmetic(ARITHMETIC.ADD)
        if not self.__expect(TOKEN_TYPE.SYMBOL, SYMBOL.EQ): return
        self.compile_expression()
        self.__expect(TOKEN_TYPE.SYMBOL, SYMBOL.SEMICOLON)

        if is_array:
            self.__vm_writer.write_pop(SEGMENT.TEMP, 0)     # pop the value to temp 0
            self.__vm_writer.write_pop(SEGMENT.POINTER, 1)  # set the 'that' to point to the top stack value
            self.__vm_writer.write_push(SEGMENT.TEMP, 0)    # push temp 0 to the stack
            self.__vm_writer.write_pop(SEGMENT.THAT, 0)     # pop the value to the 'that'
        else:
            self.__vm_writer.write_pop(var_segment, var_index)

    def compile_if(self) -> None:
        if not self.__expect(TOKEN_TYPE.KEYWORD, KEYWORD.IF): return
        if not self.__expect(TOKEN_TYPE.SYMBOL, SYMBOL.LEFT_PAREN): return
        else_label = self.__get_new_label(KEYWORD.ELSE)
        end_label = self.__get_new_label('exitIf')
        self.compile_expression()
        if not self.__expect(TOKEN_TYPE.SYMBOL, SYMBOL.RIGHT_PAREN): return
        if not self.__expect(TOKEN_TYPE.SYMBOL, SYMBOL.LEFT_BRACE): return
        self.__vm_writer.write_arithmetic(ARITHMETIC.NOT)
        self.__vm_writer.write_if(else_label)
        self.compile_statements()
        if not self.__expect(TOKEN_TYPE.SYMBOL, SYMBOL.RIGHT_BRACE): return
        self.__vm_writer.write_goto(end_label)
        self.__vm_writer.write_label(else_label)
        if self.__expect(TOKEN_TYPE.KEYWORD, KEYWORD.ELSE):
            if not self.__expect(TOKEN_TYPE.SYMBOL, SYMBOL.LEFT_BRACE): return
            self.compile_statements()
            if not self.__expect(TOKEN_TYPE.SYMBOL, SYMBOL.RIGHT_BRACE): return
        self.__vm_writer.write_label(end_label)

    def compile_while(self) -> None:
        if not self.__expect(TOKEN_TYPE.KEYWORD, KEYWORD.WHILE): return
        if not self.__expect(TOKEN_TYPE.SYMBOL, SYMBOL.LEFT_PAREN): return
        while_label = self.__get_new_label(KEYWORD.WHILE)
        end_label = self.__get_new_label('exitWhile')
        self.__vm_writer.write_label(while_label)
        self.compile_expression()
        self.__vm_writer.write_arithmetic(ARITHMETIC.NOT)
        self.__vm_writer.write_if(end_label)
        if not self.__expect(TOKEN_TYPE.SYMBOL, SYMBOL.RIGHT_PAREN): return
        if not self.__expect(TOKEN_TYPE.SYMBOL, SYMBOL.LEFT_BRACE): return
        self.compile_statements()
        if not self.__expect(TOKEN_TYPE.SYMBOL, SYMBOL.RIGHT_BRACE): return
        self.__vm_writer.write_goto(while_label)
        self.__vm_writer.write_label(end_label)

    def compile_do(self) -> None:
        caller: str
        arg_count = 0
        if not self.__expect(TOKEN_TYPE.KEYWORD, KEYWORD.DO): return
        if not self.__expect(TOKEN_TYPE.IDENTIFIER, advance=False): return
        caller = self.__tokenizer.identifier()
        caller_type = self.__symbol_table.type_of(caller)
        if caller_type is None: caller_type = caller
        self.__tokenizer.advance()
        if self.__expect(TOKEN_TYPE.SYMBOL, SYMBOL.PERIOD):
            if not self.__expect(TOKEN_TYPE.IDENTIFIER, advance=False): return
            method = self.__tokenizer.identifier()
            caller_kind = self.__symbol_table.kind_of(caller)
            if caller_kind is not None:
                arg_count = 1
                method_segment = SEGMENT_BY_KIND[caller_kind]
                method_index = self.__symbol_table.index_of(caller)
                self.__vm_writer.write_push(method_segment, method_index)
            caller = f'{caller_type}.{method}'
            self.__tokenizer.advance()
        else:
            arg_count = 1
            self.__vm_writer.write_push(SEGMENT.POINTER, 0)
            caller = f'{self.__class_name}.{caller}'
        if not self.__expect(TOKEN_TYPE.SYMBOL, SYMBOL.LEFT_PAREN): return
        arg_count += self.compile_expression_list()
        if not self.__expect(TOKEN_TYPE.SYMBOL, SYMBOL.RIGHT_PAREN): return
        self.__expect(TOKEN_TYPE.SYMBOL, SYMBOL.SEMICOLON)
        
        # generate vm code for do statement
        self.__vm_writer.write_call(caller, arg_count)
        self.__vm_writer.write_pop(SEGMENT.TEMP, 0)

    def compile_return(self) -> None:
        if not self.__expect(TOKEN_TYPE.KEYWORD, KEYWORD.RETURN): return
        if self.__current_subroutine_type == KEYWORD.VOID:
            self.__expect(TOKEN_TYPE.SYMBOL, SYMBOL.SEMICOLON)
            # generate vm code for return
            self.__vm_writer.write_push(SEGMENT.CONST, 0)
            self.__vm_writer.write_return()
            return

        self.compile_expression()
        self.__expect(TOKEN_TYPE.SYMBOL, SYMBOL.SEMICOLON)

        # generate vm code for return expression
        self.__vm_writer.write_return()

    def compile_expression(self) -> None:
        self.__operator_stack.start_stack()
        self.compile_term()
        while self.__expect(TOKEN_TYPE.SYMBOL, *self.__OPERATORS, advance=False):
            while not self.__operator_stack.is_empty() and self.__operator_stack.top() in self.__OPERATORS:
                self.__vm_writer.write_arithmetic(ARITHMETIC_BY_SYMBOL[self.__operator_stack.pop()])
            self.__operator_stack.push(self.__tokenizer.symbol())
            self.__tokenizer.advance()
            self.compile_term()

        while not self.__operator_stack.is_empty():
            self.__vm_writer.write_arithmetic(ARITHMETIC_BY_SYMBOL[self.__operator_stack.pop()])
        self.__operator_stack.close_stack()

    def compile_term(self):
        if self.__expect(TOKEN_TYPE.SYMBOL, SYMBOL.LEFT_PAREN):
            self.compile_expression()
            self.__expect(TOKEN_TYPE.SYMBOL, SYMBOL.RIGHT_PAREN)
        elif self.__expect(TOKEN_TYPE.IDENTIFIER, advance=False):
            caller = self.__tokenizer.identifier()
            caller_type = self.__symbol_table.type_of(caller)
            if caller_type is None: caller_type = caller
            self.__tokenizer.advance()
            if self.__expect(TOKEN_TYPE.SYMBOL, SYMBOL.LEFT_BRACKET):   # array
                caller_segment = SEGMENT_BY_KIND[self.__symbol_table.kind_of(caller)]
                caller_index = self.__symbol_table.index_of(caller)
                self.__vm_writer.write_push(caller_segment, caller_index)
                self.compile_expression()
                if not self.__expect(TOKEN_TYPE.SYMBOL, SYMBOL.RIGHT_BRACKET): return
                self.__vm_writer.write_arithmetic(ARITHMETIC.ADD)
                self.__vm_writer.write_pop(SEGMENT.POINTER, 1)  # pop array index from stack and put it into 'that'
                self.__vm_writer.write_push(SEGMENT.THAT, 0)    # push 'that' onto stack
            elif self.__expect(TOKEN_TYPE.SYMBOL, SYMBOL.PERIOD):
                if not self.__expect(TOKEN_TYPE.IDENTIFIER, advance=False): return
                subroutine_name = self.__tokenizer.identifier()
                self.__tokenizer.advance()
                if not self.__expect(TOKEN_TYPE.SYMBOL, SYMBOL.LEFT_PAREN): return
                arg_count = 0
                caller_kind = self.__symbol_table.kind_of(caller)
                if caller_kind is not None:
                    arg_count = 1
                    caller_segment = SEGMENT_BY_KIND[caller_kind]
                    caller_index = self.__symbol_table.index_of(caller)
                    self.__vm_writer.write_push(caller_segment, caller_index)
                arg_count += self.compile_expression_list()
                if not self.__expect(TOKEN_TYPE.SYMBOL, SYMBOL.RIGHT_PAREN): return
                self.__vm_writer.write_call(f'{caller_type}.{subroutine_name}', arg_count)
            elif self.__expect(TOKEN_TYPE.SYMBOL, SYMBOL.LEFT_PAREN):
                arg_count = self.compile_expression_list() + 1
                if not self.__expect(TOKEN_TYPE.SYMBOL, SYMBOL.RIGHT_PAREN): return
                self.__vm_writer.write_push(SEGMENT.POINTER, 0)
                self.__vm_writer.write_call(f'{self.__class_name}.{caller}', arg_count)
            else:
                caller_segment = SEGMENT_BY_KIND[self.__symbol_table.kind_of(caller)]
                caller_index = self.__symbol_table.index_of(caller)
                self.__vm_writer.write_push(caller_segment, caller_index)
        elif self.__expect(TOKEN_TYPE.KEYWORD, KEYWORD.TRUE, KEYWORD.FALSE, KEYWORD.NULL, KEYWORD.THIS, advance=False):
            token_keyword = self.__tokenizer.keyword()
            self.__tokenizer.advance()
            if token_keyword == KEYWORD.TRUE:
                self.__vm_writer.write_push(SEGMENT.CONST, 0)
                self.__vm_writer.write_arithmetic(ARITHMETIC.NOT)
            elif token_keyword == KEYWORD.FALSE or token_keyword == KEYWORD.NULL:
                self.__vm_writer.write_push(SEGMENT.CONST, 0)
            elif token_keyword == KEYWORD.THIS:
                self.__vm_writer.write_push(SEGMENT.POINTER, 0)
        elif self.__expect(TOKEN_TYPE.SYMBOL, *self.__UNARY_OPERATORS, advance=False): 
            un_op = self.__tokenizer.symbol()
            self.__tokenizer.advance()
            self.compile_term()
            if un_op == SYMBOL.MINUS: self.__vm_writer.write_arithmetic(ARITHMETIC.NEG)
            else: self.__vm_writer.write_arithmetic(ARITHMETIC.NOT)
        elif self.__expect(TOKEN_TYPE.STRING_CONST, advance=False):
            string_val = self.__tokenizer.string_val()
            self.__vm_writer.write_push(SEGMENT.CONST, len(string_val))
            self.__vm_writer.write_call('String.new', 1)
            for char in string_val:
                self.__vm_writer.write_push(SEGMENT.CONST, ord(char))
                self.__vm_writer.write_call('String.appendChar', 2)
            self.__tokenizer.advance()
        elif self.__expect(TOKEN_TYPE.INT_CONST, advance=False): 
            self.__vm_writer.write_push(SEGMENT.CONST, self.__tokenizer.int_val())
            self.__tokenizer.advance()

    def compile_expression_list(self) -> int:
        if self.__expect(TOKEN_TYPE.SYMBOL, SYMBOL.RIGHT_PAREN, advance=False): return 0
        arg_count = 1
        self.compile_expression()
        while self.__expect(TOKEN_TYPE.SYMBOL, SYMBOL.COMMA):
            self.compile_expression()
            arg_count += 1
        return arg_count

class Driver:
    def compile(file_name: str) -> None:
        input_file = open(file_name, 'r')
        output_file = open(f"{file_name.rsplit('.jack', 1)[0]}.vm", 'w')
        With(input_file, output_file).do(JackCompiler).do(JackCompiler.compile_class)

    def compile_directory(dir_name: str) -> None:
        print(f'Compiling directory {dir_name}')
        for file_name in os.listdir(dir_name):
            if not file_name.endswith('.jack'): continue
            Driver.compile(os.path.join(dir_name, file_name))

    def main(*sys_args) -> None:
        clear_screen()
        path = sys_args[0]
        if os.path.isfile(path):
            Driver.compile(path)
        elif os.path.isdir(path):
            Driver.compile_directory(path)

if __name__ == '__main__':
    With(*sys.argv[1:]).do(Driver.main)