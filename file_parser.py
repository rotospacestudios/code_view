import lupa
from lupa import LuaRuntime
import os
import pandas as pd
import ast
import textwrap
class FileParser:
    def __init__(self, file_path):
        self.file_path = file_path

    def parse_file(self,file_path):
        try:
            with open(self.file_path, 'r') as file:
                lines = file.readlines()
        except Exception as e:
            print(f"Error reading file: {e}")
            return pd.DataFrame(columns=['FileName', 'Extension', 'Type', 'LiteralLine'])

        parsed_data = []
        for i, line in enumerate(lines, start=1):  
            name = f"{os.path.basename(self.file_path)}:{i}"  
            parsed_data.append((name, None, None, line))
        
        return pd.DataFrame(parsed_data, columns=['FileName', 'Extension', 'Type', 'LiteralLine'])

class CodeAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.variable_type = None

    def visit_FunctionDef(self, node):
        self.variable_type = 'f'
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        self.variable_type = 'af'
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        self.variable_type = 'c'
        self.generic_visit(node)

    def visit_Return(self, node):
        self.variable_type = 'r'
        self.generic_visit(node)

    def visit_Delete(self, node):
        self.variable_type = 'd'
        self.generic_visit(node)

    def visit_Assign(self, node):
        self.variable_type = 'a'
        self.generic_visit(node)

    def visit_AugAssign(self, node):
        self.variable_type = 'aa'
        self.generic_visit(node)

    def visit_AnnAssign(self, node):
        self.variable_type = 'an'
        self.generic_visit(node)

    def visit_For(self, node):
        self.variable_type = 'for'
        self.generic_visit(node)

    def visit_While(self, node):
        self.variable_type = 'w'
        self.generic_visit(node)

    def visit_If(self, node):
        self.variable_type = 'if'
        self.generic_visit(node)

    def visit_With(self, node):
        self.variable_type = 'with'
        self.generic_visit(node)

    def visit_Raise(self, node):
        self.variable_type = 'ra'
        self.generic_visit(node)

    def visit_Try(self, node):
        self.variable_type = 't'
        self.generic_visit(node)

    def visit_Assert(self, node):
        self.variable_type = 'as'
        self.generic_visit(node)

    def visit_Import(self, node):
        self.variable_type = 'im'
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        self.variable_type = 'imf'
        self.generic_visit(node)

    def visit_Global(self, node):
        self.variable_type = 'g'
        self.generic_visit(node)

    def visit_Nonlocal(self, node):
        self.variable_type = 'n'
        self.generic_visit(node)

    def visit_Expr(self, node):
        self.variable_type = 'e'
        self.generic_visit(node)

    def visit_Pass(self, node):
        self.variable_type = 'p'
        self.generic_visit(node)

    def visit_Break(self, node):
        self.variable_type = 'b'
        self.generic_visit(node)

    def visit_Continue(self, node):
        self.variable_type = 'co'
        self.generic_visit(node)


class Stack:
    def __init__(self):
        self.stack = []

    def push(self, variable_type):
        level = self.get_level() + 1
        self.stack.append((variable_type, level))

    def pop(self):
        if self.stack:
            self.stack.pop()

    def get_level(self):
        if self.stack:
            return self.stack[-1][1]
        else:
            return 0

    def get_top(self):
        if self.stack:
            return self.stack[-1][0]
        else:
            return None
    def is_empty(self):
        return len(self.stack) == 0
    

class PythonParser(FileParser):
    def __init__(self, file_path):
        super().__init__(file_path)

    def parse_file(self, file_path):
        with open(file_path, 'r') as file:
            lines = file.readlines()

        data = []
        stack = Stack()
        analyzer = CodeAnalyzer()

        for line_number, line in enumerate(lines, start=1):
            if not line.strip() or line.strip().startswith('#'):
                continue

            if '"""' in line or "'''" in line:
                continue  # Skip multiline strings

            try:
                tree = ast.parse(textwrap.dedent(line))
                analyzer.visit(tree)
                variable_type = analyzer.variable_type
            except Exception as e:
                print(f"Error determining variable type: {e}")
                variable_type = 'unknown'


            if variable_type == 'variable':
                variable_type = f'var(cs, {stack.get_level()})'
            else:
                variable_type = f'cs({variable_type}, {stack.get_level()})'

            name = f"{os.path.basename(self.file_path)}:{line_number}"
            data.append([name, ".py", variable_type, line])

            open_parentheses = line.count('(')
            close_parentheses = line.count(')')

            for _ in range(open_parentheses):
                stack.push(variable_type)

            for _ in range(close_parentheses):
                if not stack.is_empty():
                    stack.pop()

        return pd.DataFrame(data, columns=['FileName', 'Extension', 'Type', 'LiteralLine'])


class LuaFileParser(FileParser):
    def __init__(self, file_path):
        super().__init__(file_path)

    def parse_file(self, file_path):
        with open(file_path, 'r') as file:
            lines = file.readlines()

        data = []
        stack = Stack()
        for line_number, line in enumerate(lines, start=1):
            # Split the line into statements
            statements = line.split(';')

            for statement in statements:
                variable_type, stack = self.determine_variable_type(statement.strip(), stack)
                if variable_type is not None:
                    name = f"{os.path.basename(self.file_path)}:{line_number}"
                    data.append([name, ".lua", variable_type, line])

        return pd.DataFrame(data, columns=['FileName', 'Extension', 'Type', 'LiteralLine'])

    def determine_variable_type(self, line, stack):
        if 'function' in line:
            stack.push('function')
            return f'f (sl {stack.get_level()})', stack
        elif 'if' in line:
            stack.push('if')
            return f'if (sl {stack.get_level()})', stack
        elif 'elseif' in line:
            stack.pop()
            stack.push('elseif')
            return f'elseif (sl {stack.get_level()})', stack
        elif 'else' in line:
            stack.pop()
            stack.push('else')
            return f'else (sl {stack.get_level()})', stack
        elif 'end' in line:
            stack.pop()
            return f'end {stack.get_top()} (sl {stack.get_level()})', stack
        elif '{' in line and '}' in line:  # Table initialization in the same line
            return f'tb (sl {stack.get_level()})', stack
        elif '{' in line:
            stack.push('table')
            return f'tb (sl {stack.get_level()})', stack
        elif '}' in line:
            stack.pop()
            return f'eof tb (sl {stack.get_level()})', stack
        elif 'local' in line and '=' in line:
            return f'var (fsl {stack.get_level()})', stack
        elif 'require' in line:
            return f'require (sl {stack.get_level()})', stack
        elif 'for' in line:
            stack.push('for')
            return f'for (sl {stack.get_level()})', stack
        elif '(' in line:
            stack.push('parenthesis')
        elif ')' in line:
            stack.pop()

        return None, stack





class ParserManager:
    def __init__(self):
        self.parsers = {}

    def get_parser(self, file_extension, file_path):
        if file_extension in self.parsers:
            return self.parsers[file_extension]
        else:
            if file_extension == '.lua':
                self.parsers[file_extension] = LuaFileParser(file_path)
            elif file_extension == '.py':
                self.parsers[file_extension] = PythonParser(file_path)
            else:
                self.parsers[file_extension] = FileParser(file_path)
            return self.parsers[file_extension]
