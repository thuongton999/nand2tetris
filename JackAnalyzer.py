from io import TextIOWrapper
import os
import re
import traceback
import sys
clearScreen = lambda: os.system('cls' if os.name == 'nt' else 'clear')

def enum(**enums):
    return type('Enum', (), enums)

TOKEN_TYPE = enum(KEYWORD='keyword', SYMBOL='symbol', IDENTIFIER='identifier', INT_CONST='integerConstant', STRING_CONST='stringConstant', COMMENT='comment')
# all tokens and its regex to match
TOKEN: dict = {
    TOKEN_TYPE.COMMENT: r'(\/\/.*)|(\/\*.*\*\/)|(\/\*[^*]*\*+(?:[^/*][^*]*\*+)*\/)',
    TOKEN_TYPE.KEYWORD: r'(class|constructor|function|method|field|static|var|int|char|boolean|void|true|false|null|this|let|do|if|else|while|return)',
    TOKEN_TYPE.IDENTIFIER: r'([a-zA-Z_][a-zA-Z0-9_]*)',
    TOKEN_TYPE.SYMBOL: r'(\{|\}|\(|\)|\[|\]|\.|,|;|\+|-|\*|\/|&|\||<|>|=|~)',
    TOKEN_TYPE.INT_CONST: r'([0-9]+)',
    TOKEN_TYPE.STRING_CONST: r'(".*")',
}

# Monad
class With:
    __input_args: tuple
    __input_kwargs: dict
    def __init__(self, *args, **kwargs) -> None:
        self.__input_args = args
        self.__input_kwargs = kwargs

    def do(self, action):
        try:
            return With(action(*self.__input_args, **self.__input_kwargs))
        except Exception as err:
            print(f"Error happened: {err}\n")
            traceback.print_exc()
    
    def get(self, index=None):
        if index is None:
            return self.__input_args
        return self.__input_args[index]

class XMLWriter:
    __output_file: TextIOWrapper
    __current_indent: int
    __tab: str
    __special_symbols: dict = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&apos;',
    }

    def __init__(self, output_file: TextIOWrapper) -> None:
        self.__output_file = output_file
        self.__current_indent = 0
        self.__tab = '\t'

    def open_tag(self, tag: str) -> None:
        self.__output_file.write(f"{self.__tab * self.__current_indent}<{tag}>\n")
        self.__current_indent += 1
    
    def close_tag(self, tag: str) -> None:
        self.__current_indent -= 1
        self.__output_file.write(f"{self.__tab * self.__current_indent}</{tag}>\n")
    
    def write_tag(self, tag: str, value: str = '') -> None:
        for symbol in self.__special_symbols:
            value = value.replace(symbol, self.__special_symbols[symbol])
        self.__output_file.write(f"{self.__tab * self.__current_indent}<{tag}>{value}</{tag}>\n")

    def close_file(self) -> None:
        self.__output_file.close()

class JackTokenizer:
    __input_file: TextIOWrapper
    __tokens: list
    __current_token_index: int

    def __init__(self, input_file: TextIOWrapper) -> None:
        self.__input_file = input_file
        self.__current_token_index = 0
        self.__tokens = JackTokenizer.extract_tokens(self.__input_file.read())

    def extract_tokens(cmd) -> list:
        tokens = []
        while cmd.strip():
            for token_type, regex in TOKEN.items():
                line = cmd.strip()
                match = re.match(f'^{regex}', line)
                if not match: continue
                cmd = line[match.end():]
                if token_type == TOKEN_TYPE.COMMENT: break
                tokens.append((match.group(), token_type))
                break
        return tokens

    def reset(self) -> None:
        self.__current_token_index = 0

    def has_more_tokens(self) -> bool:
        return self.__current_token_index < len(self.__tokens)

    def advance(self) -> None:
        self.__current_token_index += 1

    def token_type(self) -> TOKEN_TYPE:
        return With(self.__tokens[self.__current_token_index][1]).do(lambda token: token).get(0)

    def keyword(self) -> str:
        return With(self.__tokens[self.__current_token_index][0]).do(lambda token: token).get(0)

    def symbol(self) -> str:
        return With(self.__tokens[self.__current_token_index][0]).do(lambda token: token).get(0)

    def identifier(self) -> str:
        return With(self.__tokens[self.__current_token_index][0]).do(lambda token: token).get(0)

    def int_val(self) -> int:
        return With(self.__tokens[self.__current_token_index][0]).do(lambda token: int(token)).get(0)

    def string_val(self) -> str:
        return With(self.__tokens[self.__current_token_index][0]).do(lambda token: token[1:-1]).get(0)
    
    def token_value(self):
        getter_by_type = {
            TOKEN_TYPE.KEYWORD: self.keyword,
            TOKEN_TYPE.SYMBOL: self.symbol,
            TOKEN_TYPE.IDENTIFIER: self.identifier,
            TOKEN_TYPE.INT_CONST: self.int_val,
            TOKEN_TYPE.STRING_CONST: self.string_val,
        }
        getter = getter_by_type[self.token_type()]
        return getter()

class JackAnalyzer:
    __input_file: TextIOWrapper
    __tokens_xml: XMLWriter
    __parse_tree_xml: XMLWriter
    __tokenizer: JackTokenizer
    __STATEMENTS = ('let', 'if', 'while', 'do', 'return')
    __CLASS_VAR_DEC = ('static', 'field')
    def __init__(self, input_file, output_tokens_file: TextIOWrapper, output_parse_tree_file: TextIOWrapper) -> None:
        print(f"Compiling {input_file.name}")
        self.__input_file = input_file
        self.__tokens_xml = XMLWriter(output_tokens_file)
        self.__parse_tree_xml = XMLWriter(output_parse_tree_file)
        self.__tokenizer = JackTokenizer(self.__input_file)
        self.__write_tokens()

    def __write_tokens(self):
        self.__tokens_xml.open_tag("tokens")
        self.__tokenizer.reset()
        while self.__tokenizer.has_more_tokens():
            token_type = self.__tokenizer.token_type()
            token_value = self.__tokenizer.token_value()
            self.__tokens_xml.write_tag(token_type, f' {token_value} ')
            self.__tokenizer.advance()
        self.__tokenizer.reset()
        self.__tokens_xml.close_tag("tokens")
        self.__tokens_xml.close_file()

    def __expect_token(self, token_type: TOKEN_TYPE, *token_values: tuple) -> bool:
        if not self.__tokenizer.token_type() == token_type: return False
        if not self.__tokenizer.token_value() in token_values: return False
        self.__parse_tree_xml.write_tag(token_type, f' {self.__tokenizer.token_value()} ')
        if not self.__tokenizer.has_more_tokens(): return True
        self.__tokenizer.advance()
        return True
    
    def compile_class(self) -> None:
        self.__parse_tree_xml.open_tag('class')
        if not self.__expect_token(TOKEN_TYPE.KEYWORD, 'class'): return
        if not self.__expect_token(TOKEN_TYPE.IDENTIFIER, self.__tokenizer.identifier()): return
        if not self.__expect_token(TOKEN_TYPE.SYMBOL, '{'): return
        
        while self.__tokenizer.token_type() == TOKEN_TYPE.KEYWORD and self.__tokenizer.keyword() in self.__CLASS_VAR_DEC:
            self.compile_class_var_dec()

        while not self.__expect_token(TOKEN_TYPE.SYMBOL, '}'):
            self.compile_subroutine()
        
        self.__parse_tree_xml.close_tag('class')
    
    def compile_class_var_dec(self) -> None:
        self.__parse_tree_xml.open_tag('classVarDec')
        if not self.__expect_token(TOKEN_TYPE.KEYWORD, 'static', 'field'): return
        if not self.__expect_token(TOKEN_TYPE.KEYWORD, 'int', 'char', 'boolean'):
            if not self.__expect_token(TOKEN_TYPE.IDENTIFIER, self.__tokenizer.identifier()): return
        while self.__expect_token(TOKEN_TYPE.IDENTIFIER, self.__tokenizer.identifier()):
            if not self.__expect_token(TOKEN_TYPE.SYMBOL, ','): break
        if not self.__expect_token(TOKEN_TYPE.SYMBOL, ';'): return
        self.__parse_tree_xml.close_tag('classVarDec')

    def compile_subroutine(self) -> None:
        self.__parse_tree_xml.open_tag('subroutineDec')
        if not self.__expect_token(TOKEN_TYPE.KEYWORD, 'function', 'constructor', 'method'): return
        if not self.__expect_token(TOKEN_TYPE.KEYWORD, 'void', 'int', 'char', 'boolean'):
            if not self.__expect_token(TOKEN_TYPE.IDENTIFIER, self.__tokenizer.identifier()): return
        if not self.__expect_token(TOKEN_TYPE.IDENTIFIER, self.__tokenizer.identifier()): return
        if not self.__expect_token(TOKEN_TYPE.SYMBOL, '('): return
        self.compile_parameter_list()
        if not self.__expect_token(TOKEN_TYPE.SYMBOL, ')'): return
        self.compile_subroutine_body()
        self.__parse_tree_xml.close_tag('subroutineDec')

    def compile_parameter_list(self) -> None:
        self.__parse_tree_xml.open_tag('parameterList')
        while self.__expect_token(TOKEN_TYPE.KEYWORD, 'int', 'char', 'boolean'):
            if not self.__expect_token(TOKEN_TYPE.IDENTIFIER, self.__tokenizer.identifier()): break
            if not self.__expect_token(TOKEN_TYPE.SYMBOL, ','): break
        self.__parse_tree_xml.close_tag('parameterList')

    def compile_subroutine_body(self) -> None:
        self.__parse_tree_xml.open_tag('subroutineBody')
        if not self.__expect_token(TOKEN_TYPE.SYMBOL, '{'): return
        while (self.__tokenizer.token_type() == TOKEN_TYPE.KEYWORD) and (self.__tokenizer.keyword() == 'var'):
            self.compile_var_dec()
        self.compile_statements()
        if not self.__expect_token(TOKEN_TYPE.SYMBOL, '}'): return
        self.__parse_tree_xml.close_tag('subroutineBody')

    def compile_var_dec(self) -> None:
        self.__parse_tree_xml.open_tag('varDec')
        if not self.__expect_token(TOKEN_TYPE.KEYWORD, 'var'): return
        if not self.__expect_token(TOKEN_TYPE.KEYWORD, 'int', 'char', 'boolean'):
            if not self.__expect_token(TOKEN_TYPE.IDENTIFIER, self.__tokenizer.identifier()): return
        while self.__expect_token(TOKEN_TYPE.IDENTIFIER, self.__tokenizer.identifier()):
            if not self.__expect_token(TOKEN_TYPE.SYMBOL, ','): break
        if not self.__expect_token(TOKEN_TYPE.SYMBOL, ';'): return
        self.__parse_tree_xml.close_tag('varDec')

    def compile_statements(self) -> None:
        self.__parse_tree_xml.open_tag('statements')
        is_statement = lambda token_type, token_value: token_type == TOKEN_TYPE.KEYWORD and token_value in self.__STATEMENTS
        while is_statement(self.__tokenizer.token_type(), self.__tokenizer.token_value()):
            if self.__tokenizer.token_value() == 'let': self.compile_let()
            elif self.__tokenizer.token_value() == 'if': self.compile_if()
            elif self.__tokenizer.token_value() == 'while': self.compile_while()
            elif self.__tokenizer.token_value() == 'do': self.compile_do()
            elif self.__tokenizer.token_value() == 'return': self.compile_return()
            else: break
        self.__parse_tree_xml.close_tag('statements')

    def compile_let(self) -> None:
        self.__parse_tree_xml.open_tag('letStatement')
        if not self.__expect_token(TOKEN_TYPE.KEYWORD, 'let'): return
        if not self.__expect_token(TOKEN_TYPE.IDENTIFIER, self.__tokenizer.identifier()): return
        if self.__expect_token(TOKEN_TYPE.SYMBOL, '['):
            self.compile_expression()
            if not self.__expect_token(TOKEN_TYPE.SYMBOL, ']'): return
        if not self.__expect_token(TOKEN_TYPE.SYMBOL, '='): return
        self.compile_expression()
        if not self.__expect_token(TOKEN_TYPE.SYMBOL, ';'): return
        self.__parse_tree_xml.close_tag('letStatement')

    def compile_if(self) -> None:
        self.__parse_tree_xml.open_tag('ifStatement')
        if not self.__expect_token(TOKEN_TYPE.KEYWORD, 'if'): return
        if not self.__expect_token(TOKEN_TYPE.SYMBOL, '('): return
        self.compile_expression()
        if not self.__expect_token(TOKEN_TYPE.SYMBOL, ')'): return
        if not self.__expect_token(TOKEN_TYPE.SYMBOL, '{'): return
        self.compile_statements()
        if not self.__expect_token(TOKEN_TYPE.SYMBOL, '}'): return
        if self.__expect_token(TOKEN_TYPE.KEYWORD, 'else'):
            if not self.__expect_token(TOKEN_TYPE.SYMBOL, '{'): return
            self.compile_statements()
            if not self.__expect_token(TOKEN_TYPE.SYMBOL, '}'): return
        self.__parse_tree_xml.close_tag('ifStatement')

    def compile_while(self) -> None:
        self.__parse_tree_xml.open_tag('whileStatement')
        if not self.__expect_token(TOKEN_TYPE.KEYWORD, 'while'): return
        if not self.__expect_token(TOKEN_TYPE.SYMBOL, '('): return
        self.compile_expression()
        if not self.__expect_token(TOKEN_TYPE.SYMBOL, ')'): return
        if not self.__expect_token(TOKEN_TYPE.SYMBOL, '{'): return
        self.compile_statements()
        if not self.__expect_token(TOKEN_TYPE.SYMBOL, '}'): return
        self.__parse_tree_xml.close_tag('whileStatement')

    def compile_do(self) -> None:
        self.__parse_tree_xml.open_tag('doStatement')
        if not self.__expect_token(TOKEN_TYPE.KEYWORD, 'do'): return
        if not self.__expect_token(TOKEN_TYPE.IDENTIFIER, self.__tokenizer.identifier()): return
        if self.__expect_token(TOKEN_TYPE.SYMBOL, '.'):
            if not self.__expect_token(TOKEN_TYPE.IDENTIFIER, self.__tokenizer.identifier()): return
        if not self.__expect_token(TOKEN_TYPE.SYMBOL, '('): return
        self.compile_expression_list()
        if not self.__expect_token(TOKEN_TYPE.SYMBOL, ')'): return
        if not self.__expect_token(TOKEN_TYPE.SYMBOL, ';'): return
        self.__parse_tree_xml.close_tag('doStatement')

    def compile_return(self) -> None:
        self.__parse_tree_xml.open_tag('returnStatement')
        self.__expect_token(TOKEN_TYPE.KEYWORD, 'return')
        if self.__expect_token(TOKEN_TYPE.SYMBOL, ';'):
            pass
        else:
            self.compile_expression()
            self.__expect_token(TOKEN_TYPE.SYMBOL, ';')
        self.__parse_tree_xml.close_tag('returnStatement')

    def compile_expression(self) -> None:
        self.__parse_tree_xml.open_tag('expression')
        self.compile_term()
        while self.__expect_token(TOKEN_TYPE.SYMBOL, '+', '-', '*', '/', '&', '|', '<', '>', '='):
            self.compile_term()
        self.__parse_tree_xml.close_tag('expression')

    def compile_term(self) -> None:
        self.__parse_tree_xml.open_tag('term')
        if self.__expect_token(TOKEN_TYPE.SYMBOL, '('):
            self.compile_expression()
            self.__expect_token(TOKEN_TYPE.SYMBOL, ')')
        elif self.__expect_token(TOKEN_TYPE.IDENTIFIER, self.__tokenizer.identifier()):
            if self.__expect_token(TOKEN_TYPE.SYMBOL, '['):
                self.compile_expression()
                if not self.__expect_token(TOKEN_TYPE.SYMBOL, ']'): return
            elif self.__expect_token(TOKEN_TYPE.SYMBOL, '.'):
                if not self.__expect_token(TOKEN_TYPE.IDENTIFIER, self.__tokenizer.identifier()): return
                if not self.__expect_token(TOKEN_TYPE.SYMBOL, '('): return
                self.compile_expression_list()
                if not self.__expect_token(TOKEN_TYPE.SYMBOL, ')'): return
            elif self.__expect_token(TOKEN_TYPE.SYMBOL, '('):
                self.compile_expression_list()
                if not self.__expect_token(TOKEN_TYPE.SYMBOL, ')'): return
        elif self.__expect_token(TOKEN_TYPE.KEYWORD, 'true', 'false', 'null', 'this'): pass
        elif self.__expect_token(TOKEN_TYPE.SYMBOL, '~', '-'): self.compile_term()  # unary op
        elif self.__expect_token(TOKEN_TYPE.STRING_CONST, self.__tokenizer.token_value()): pass
        elif self.__expect_token(TOKEN_TYPE.INT_CONST, self.__tokenizer.token_value()): pass
        self.__parse_tree_xml.close_tag('term')

    def compile_expression_list(self) -> None:
        self.__parse_tree_xml.open_tag('expressionList')
        if not (self.__tokenizer.token_type() == TOKEN_TYPE.SYMBOL and self.__tokenizer.token_value() == ')'):
            self.compile_expression()
            while self.__expect_token(TOKEN_TYPE.SYMBOL, ','):
                self.compile_expression()
        self.__parse_tree_xml.close_tag('expressionList')

class Driver:
    def compile_file(input_file_name: str) -> None:
        input_file = open(input_file_name, 'r')
        output_file_name = input_file_name.rsplit('.jack', 1)[0]
        parse_tree_file = open(f'{output_file_name}.xml', 'w')
        tokens_file = open(f'{output_file_name}T.xml', 'w')

        With(input_file, tokens_file, parse_tree_file).do(JackAnalyzer).do(JackAnalyzer.compile_class)
        input_file.close()
        parse_tree_file.close()

    def compile_directory(input_dir: str) -> None:
        print(f"Compiling {input_dir}")
        for file_name in os.listdir(input_dir):
            if not file_name.endswith('.jack'): continue
            Driver.compile_file(f'{input_dir}/{file_name}')

def main(*sys_args) -> None:
    if os.path.isdir(sys_args[1]):
        With(sys_args[1]).do(Driver.compile_directory)#.do(CodeGenerator.generate_vm_file)
    else:
        With(sys_args[1]).do(Driver.compile_file)#.do(CodeGenerator.generate_vm_directory)
    
if __name__ == "__main__":
    clearScreen()
    With(*sys.argv).do(main)