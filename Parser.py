from dataclasses import dataclass
from fractions import Fraction
from typing import Union
from typing import Optional, NewType
from lexer import *
from eval import *


@dataclass
class Parser:
    tokens: lexer

    def call_parser(tokens):
        return Parser(tokens)

    def parse_primary(self):

        match self.tokens.peek_token():
            case Identifier(name):
                self.tokens.advance()
                return get(identifier(name))
            case Num(value):
                self.tokens.advance()
                return numeric_literal(value)
            # case Bool(value):
            #     self.tokens.advance()
            #     return bool_literal(value)
            case String(value):
                self.tokens.advance()
                return string_literal(value)

    def parse_power(self):
        left = self.parse_primary()
        while True:
        
            match self.tokens.peek_token():
                case Operator(op) if op in "^":
                    self.tokens.advance()
                    m = self.parse_power()
                    left = binary_operation(op, left, m)
                case _:
                    break
                
        return left

    def parse_unary(self):
        left = self.parse_power()
        while True:
            match self.tokens.peek_token():
                case Operator(op) if op in "!-":
                    self.tokens.advance()
                    m = self.parse_unary()
                    left = unary_operation(op, m)
                case _:
                    break
        return left

    def parse_mult(self):
        left = self.parse_unary()
        while True:
            
            match self.tokens.peek_token():
                case Operator(op) if op in "*/":
                    self.tokens.advance()
                    m = self.parse_mult()
                    left = binary_operation(op, left, m)
                case _:
                    break
        return left

    def parse_add(self):
        left = self.parse_mult()
        while True:
            
            match self.tokens.peek_token():
                
                case Operator(op) if op in "+-":
                    self.tokens.advance()
                    m = self.parse_add()
                    left = binary_operation(op, left, m)
                case _:
                    break
        return left

    def parse_comp(self):
        left = self.parse_add()
        match self.tokens.peek_token():
            case Operator(op) if op in "<>":
                self.tokens.advance()
                right = self.parse_add()
                return binary_operation(op, left, right)
        return left

    def parse_equal(self):
        left = self.parse_comp()
        match self.tokens.peek_token():
            case Operator(op) if op == "==" or op == "!=":
                self.tokens.advance()
                right = self.parse_comp()
                return binary_operation(op, left, right)
        return left

    def parse_logic(self):
        left = self.parse_equal()
        match self.tokens.peek_token():
            case Operator(op) if op == "&&" or op == "||":
                self.tokens.advance()
                right = self.parse_equal()
                return binary_operation(op, left, right)
        return left
    
    def parse_set(self):
        # print("hi")
        match self.tokens.peek_token():
            case Identifier(name):
                match self.tokens.next_token():
                    case Operator(op) if op in "=":
                        
                        # print("hi")
                        self.tokens.advance()
                        
                        while True:
                            value = self.parse_logic()
                            
                            match self.tokens.peek_token():
                                case Operator(op) if op in ";":
                                    break
                        if not value:
                            return None
                        
                        return set(identifier(name), value)
                    
                    case _:
                        return None
            case _:
                return None

    def parse_expr(self):
        match self.tokens.peek_token():
            case Keyword("let"):
                return self.parse_let()
            case Keyword("def"):
                return self.parse_function()
            case Keyword("for"):
                return self.parse_for()
            case Keyword("if"):
                return self.parse_if()
            case Keyword("while"):
                return self.parse_while()
            case Keyword("print"):
                return self.parse_print()
            case Keyword("List"):
                return self.parse_List()
            case Keyword("var"):
                return self.parse_declare()
            case functionName(name):
                return self.parse_function_call()
            case _:
                tree = self.parse_set()
                if tree == None:
                    tree = self.parse_logic()
                return tree
            
    def parse_function_call(self):
        match self.tokens.peek_token():
            case functionName(name):
                self.tokens.advance()
                match self.tokens.peek_token():
                    case Operator("("):
                        self.tokens.advance()
                        parameters = []
                        while self.tokens.peek_token() is not None:
                            
                            if isinstance(self.tokens.peek_token(), Identifier):
                                parameters.append(self.tokens.peek_token())
                                self.tokens.advance()
                                if isinstance(self.tokens.peek_token(), Operator) and self.tokens.peek_token().op == ")":
                                    self.tokens.advance()
                                    break
                                elif isinstance(self.tokens.peek_token(), Operator) and self.tokens.peek_token().op == ",":
                                    self.tokens.advance()
                                    continue
                                else:
                                    raise SyntaxError("Unexpected token")
                            elif isinstance(self.tokens.peek_token(), Operator) and self.tokens.peek_token().op == ";":
                                self.tokens.advance()
                                break
                            else:
                                raise SyntaxError("Unexpected token")
                        
                            
                        return FunctionCall(identifier(name), parameters)
                    
                    case _:
                        raise SyntaxError("Unexpected token")

    def parse_function(self):
        match self.tokens.peek_token():
            case Keyword("def"):
                self.tokens.advance()
                match self.tokens.peek_token():
                    case functionName(name):
                        self.tokens.advance()
                        match self.tokens.peek_token():
                            case Operator("("):
                                self.tokens.advance()
                                parameters = []
                                while self.tokens.peek_token() is not None:

                                    if isinstance(self.tokens.peek_token(), Identifier):
                                        parameters.append(self.tokens.peek_token())
                                        self.tokens.advance()
                                        if isinstance(self.tokens.peek_token(), Operator) and self.tokens.peek_token().op == ")":
                                            self.tokens.advance()

                                        elif isinstance(self.tokens.peek_token(), Operator) and self.tokens.peek_token().op == "{":
                                            self.tokens.advance()
                                            break

                                        elif isinstance(self.tokens.peek_token(), Operator) and self.tokens.peek_token().op == ",":
                                            self.tokens.advance()
                                            continue
                                        else:
                                            raise SyntaxError("Unexpected token")
                                    elif isinstance(self.tokens.peek_token(), Operator) and self.tokens.peek_token().op == "{":
                                        self.tokens.advance()
                                        break
                                    else:
                                        raise SyntaxError("Unexpected token")
                                
                                exprs = []

                                while True:
                                    exprs.append(self.parse_expr())
                                    match self.tokens.peek_token():
                                        case Keyword(word) if word in "return":
                                            self.tokens.advance()
                                            ret_expr = self.parse_logic()
                                            break
                                    
                                    self.tokens.match(Operator(";"))
                                
                                body = block(exprs)

                                return Function(identifier(name), parameters, body, ret_expr)
                            
                            case _:
                                raise SyntaxError("Unexpected token")
                    case _:
                        raise SyntaxError("Unexpected token")
            case _:
                return None
            
    
    def parse_while(self):
        self.tokens.match(Keyword("while"))
        c = self.parse_expr()
        self.tokens.match(Keyword("do"))
        b = self.parse_expr()
        self.tokens.match(Keyword("end"))
        return while_loop(c, b)
    
    def parse_if(self):
        self.tokens.match(Keyword("if"))
        c = self.parse_expr()
        self.tokens.match(Keyword("then"))
        t = self.parse_expr()
        self.tokens.match(Keyword("else"))
        f = self.parse_expr()
        self.tokens.match(Keyword("end"))
        self.tokens.match(Operator(";"))
        return if_statement(c, t, f)

    # for can be passed as while loop and some extra conditions
    def parse_for(self):
        self.tokens.match(Keyword("for"))
        iterator = self.parse_expr()
        self.tokens.match(Operator(";"))
        condition = self.parse_expr()
        self.tokens.match(Operator(";"))
        increment = self.parse_expr()
        self.tokens.match(Keyword("do"))
        body = self.parse_expr()
        self.tokens.match(Keyword("end"))
        self.tokens.match(Operator(";"))
        return for_loop(iterator, condition, increment, body)
    
    def parse_print(self):
        self.tokens.match(Keyword("print"))
        # if self.tokens.peek_token().matches("("):
        #     self.tokens.advance()
        exprs = []
        while True:
            # if self.tokens.peek_token().matches(")"):
            #     break
            exprs.append(self.parse_expr())
            match self.tokens.peek_token():
                case Operator(op) if op in ";":
                    break
            self.tokens.match(Operator(","))
        
        return print_statement(exprs)
    
    def parse_List(self):
        self.tokens.match(Keyword("List"))
        values = []
        while True:
            values.append(self.parse_expr())
            match self.tokens.peek_token():
                case Operator(op) if op in ";":
                    break
            self.tokens.match(Operator(","))
        return Lists(values)
        
    def parse_let(self):
        self.tokens.match(Keyword("let"))
        name = self.tokens.peek_token()
        self.tokens.advance()
        self.tokens.match(Operator("="))
        value = self.parse_expr()
        self.tokens.match(Keyword("in"))
        body = self.parse_expr()
        return let(name, value, body)

    def parse_declare(self) -> Optional[declare]:
        self.tokens.match(Keyword("var"))
        vari = self.tokens.peek_token().word
        self.tokens.advance()
        match self.tokens.peek_token():
            case Operator(op) if op != "=":
                return None
        self.tokens.advance()
        while True:
            # match self.tokens.peek_token():
            #     case Identifier(name):
            value = self.parse_expr()
            match self.tokens.peek_token():
                case Operator(op) if op in ";":
                    break
        if not value:
            return None

        return declare(identifier(vari), value)
    
    

@dataclass
class NumType:
    pass


@dataclass
class BoolType:
    pass


SimType = NumType | BoolType

AST = numeric_literal | bool_literal | string_literal | binary_operation | let_var | unary_operation | while_loop | if_statement 

TypedAST = NewType('TypedAST', AST)


class TypeError(Exception):
    pass


def test_parse():
    def parse(string):
        return Parser.parse_expr(
            Parser.call_parser(lexer.lexerFromStream(
                Stream.streamFromString(string)))
        )

    # You should parse, evaluate and see whether the expression produces the expected value in your tests.
    print(parse("for 1 ; 2 ; 3 do 4 end"))


# test_parse()  # Uncomment to see the created ASTs.

def test_parse1():
    def parse(string):
        return Parser.parse_expr(
            Parser.call_parser(lexer.lexerFromStream(
                Stream.streamFromString(string)))
        )
    
    eval_ast(parse("print 1, 2, 3;"), None, None)
    

def test_parse2():
    def parse(string):
        return Parser.parse_expr(
            Parser.call_parser(lexer.lexerFromStream(
                Stream.streamFromString(string)))
        )

    # You should parse, evaluate and see whether the expression produces the expected value in your tests.
    print(parse("let a = 1 in a + 2"))

def test_parse3():
    def parse(string):
        return Parser.parse_expr(
            Parser.call_parser(lexer.lexerFromStream(
                Stream.streamFromString(string)))
        )
    print(parse("1+2;"))

def test_parse4():
    def parse(string):
        return Parser.parse_expr (
            Parser.call_parser(lexer.lexerFromStream(Stream.streamFromString(string)))
        )
    
    # print(parse("a+b"))
    # You should parse, evaluate and see whether the expression produces the expected value in your tests.
    print(eval_ast(parse("6+7+8;")))
    
def test_parse5():
    def parse(string):
        return Parser.parse_expr(
            Parser.call_parser(lexer.lexerFromStream(
                Stream.streamFromString(string)))
        )
    
    # print(parse("var a = 2;"))
    # You should parse, evaluate and see whether the expression produces the expected value in your tests.
    print(eval_ast(parse("var a = 2+3;"),None, None))

def test_parse6():
    def parse(string):
        return Parser.parse_expr(
            Parser.call_parser(lexer.lexerFromStream(
                Stream.streamFromString(string)))
        )
    print(parse("a = 4+2;"))

def test_parse7():
    def parse(string):
        return Parser.parse_expr(
            Parser.call_parser(lexer.lexerFromStream(
                Stream.streamFromString(string)))
        )
    print(parse("a = w+c+d+e;"))


def test_parse8():
    def parse(string):
        return Parser.parse_expr(
            Parser.call_parser(lexer.lexerFromStream(
                Stream.streamFromString(string)))
        )
    print(eval_ast(parse("def fun(a, b){ a=c+d+e; i = 2; return a+b; }")))
    print(parse("def fun(a, b){ a=c+d+e; i = 2; return a+b; }"))

def test_parse9():
    def parse(string):
        return Parser.parse_expr(
            Parser.call_parser(lexer.lexerFromStream(
                Stream.streamFromString(string)))
        )
    print(parse("fun(a, b, c);"))

test_parse1()
test_parse2()
test_parse3()
test_parse4()
test_parse5()
test_parse6()
test_parse7()
test_parse8()
test_parse9()


