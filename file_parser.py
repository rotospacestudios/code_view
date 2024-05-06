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
        self.variable_types = []
        self.stack = Stack()

    def get_line_type(self, line):
        try:
            tree = ast.parse(textwrap.dedent(line))
            self.visit(tree)
            return self.variable_types
        except Exception as e:
            print(f"Error determining variable type: {e}")
            return ['unknown']

    def visit_FunctionDef(self, node):
        self.stack.push('f')
        self.variable_types.append(f'f (sl {self.stack.get_level()})')
        self.generic_visit(node)
        self.stack.pop()

    # Add similar visit methods for other node types...

    def generic_visit(self, node):
        """Called if no explicit visitor function exists for a node."""
        for _, value in ast.iter_fields(node):
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, ast.AST):
                        self.visit(item)
            elif isinstance(value, ast.AST):
                self.visit(value)
    def visit_AsyncFunctionDef(self, node):
        self.variable_types.append('af')
        self.generic_visit(node)
        self.stack.pop()

    def visit_ClassDef(self, node):
        self.variable_types.append('c')
        self.generic_visit(node)
        self.stack.pop()

    def visit_Return(self, node):
        self.variable_types.append('r')
        self.generic_visit(node)
        self.stack.pop()

    def visit_Delete(self, node):
        self.variable_types.append('d')
        self.generic_visit(node)
        self.stack.pop()

    def visit_Assign(self, node):
        self.variable_types.append('a')
        self.generic_visit(node)
        self.stack.pop()

    def visit_AugAssign(self, node):
        self.variable_types.append('aa')
        self.generic_visit(node)
        self.stack.pop()

    def visit_AnnAssign(self, node):
        self.variable_types.append('an')
        self.generic_visit(node)
        self.stack.pop()

    def visit_For(self, node):
        self.variable_types.append('for')
        self.generic_visit(node)
        self.stack.pop()

    def visit_While(self, node):
        self.variable_types.append('w')
        self.generic_visit(node)
        self.stack.pop()

    def visit_If(self, node):
        self.variable_types.append('if')
        self.generic_visit(node)
        self.stack.pop()

    def visit_With(self, node):
        self.variable_types.append('with')
        self.generic_visit(node)
        self.stack.pop()

    def visit_Raise(self, node):
        self.variable_types.append('ra')
        self.generic_visit(node)
        self.stack.pop()

    def visit_Try(self, node):
        self.variable_types.append('t')
        self.generic_visit(node)
        self.stack.pop()

    def visit_Assert(self, node):
        self.variable_types.append('as')
        self.generic_visit(node)
        self.stack.pop()

    def visit_Import(self, node):
        self.variable_types.append('im')
        self.generic_visit(node)
        self.stack.pop()

    def visit_ImportFrom(self, node):
        self.variable_types.append('imf')
        self.generic_visit(node)
        self.stack.pop()

    def visit_Global(self, node):
        self.variable_types.append('g')
        self.generic_visit(node)
        self.stack.pop()

    def visit_Nonlocal(self, node):
        self.variable_types.append('n')
        self.generic_visit(node)
        self.stack.pop()

    def visit_Expr(self, node):
        self.variable_types.append('e')
        self.generic_visit(node)
        self.stack.pop()

    def visit_Pass(self, node):
        self.variable_types.append('p')
        self.generic_visit(node)
        self.stack.pop()

    def visit_Break(self, node):
        self.variable_types.append('b')
        self.generic_visit(node)
        self.stack.pop()

    def visit_Continue(self, node):
        self.variable_types.append('co')
        self.generic_visit(node)
        self.stack.pop()


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
        
    def get_variables(self, file_path):
        with open(file_path, 'r') as file:
            lines = file.readlines()

        variables = []
        for i, line in enumerate(lines, start=1):
            if '=' in line:  # Simple condition for variable assignment
                name = line.split('=')[0].strip()  # Get the variable name
                variables.append([f"{os.path.basename(self.file_path)}:{i}", None, None, line])

        return pd.DataFrame(variables, columns=['FileName', 'Extension', 'Type', 'LiteralLine'])

    def parse_file(self, file_path):
        with open(file_path, 'r') as file:
            lines = file.readlines()

        data = []
        analyzer = CodeAnalyzer()

        # Get the actual file extension
        _, extension = os.path.splitext(file_path)

        for line_number, line in enumerate(lines, start=1):
            line = line.strip()

            # Skip comments
            if line.startswith('#'):
                continue

            # Handle multiple statements on a single line
            statements = line.split(';')
            for statement in statements:
                statement = statement.strip()

                # Determine the type of the statement
                variable_types = analyzer.get_line_type(statement)
                for variable_type in variable_types:
                    name = f"{os.path.basename(file_path)}:{line_number}"
                    literal_line = statement.strip()
                    data.append([name, extension, variable_type, literal_line])

        df = pd.DataFrame(data, columns=['FileName', 'Extension', 'Type', 'LiteralLine'])
        return df


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
    

    def get_variables(self, file_path):
        with open(file_path, 'r') as file:
            lines = file.readlines()

        variables = []
        for i, line in enumerate(lines, start=1):
            if '=' in line:  # Simple condition for variable assignment
                name = line.split('=')[0].strip()  # Get the variable name
                variables.append([f"{os.path.basename(self.file_path)}:{i}", None, None, line])

        return pd.DataFrame(variables, columns=['FileName', 'Extension', 'Type', 'LiteralLine'])

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

        return None, stack

        return None, stack
    
class CParser(FileParser):
    def __init__(self, file_path):
        super().__init__(file_path)
        
    def get_variables(self, file_path):
        with open(file_path, 'r') as file:
            lines = file.readlines()

        variables = []
        in_multiline_assignment = False
        variable_name = None
        for i, line in enumerate(lines, start=1):
            if '=' in line and ';' in line:  # Simple condition for variable assignment
                name = line.split('=')[0].strip()  # Get the variable name
                variables.append([f"{os.path.basename(self.file_path)}:{i}", None, None, line])
            elif '=' in line:  # Start of a multiline variable assignment
                in_multiline_assignment = True
                variable_name = line.split('=')[0].strip()  # Get the variable name
            elif in_multiline_assignment and ';' in line:  # End of a multiline variable assignment
                in_multiline_assignment = False
                variables.append([f"{os.path.basename(self.file_path)}:{i}", None, None, variable_name + line])

        return pd.DataFrame(variables, columns=['FileName', 'Extension', 'Type', 'LiteralLine'])

    def parse_file(self, file_path):
        with open(file_path, 'r') as file:
            lines = file.readlines()

        data = []
        stack = Stack()

        # Get the actual file extension
        _, extension = os.path.splitext(file_path)

        in_multiline_statement = False
        for line_number, line in enumerate(lines, start=1):
            line = line.strip()

            # Determine the type of the line
            if ';' in line and '=' not in line:
                line_type = f"declaration({stack.get_level()})"
            elif '{' in line:
                stack.push('{')
                line_type = f"block_start({stack.get_level()})"
            elif '}' in line:
                stack.pop()
                line_type = f"block_end({stack.get_level()})"
            elif '=' in line and ';' in line:  # Simple condition for variable assignment
                line_type = f"assignment({stack.get_level()})"
            elif '=' in line:  # Start of a multiline variable assignment
                in_multiline_statement = True
                line_type = f"multiline_assignment_start({stack.get_level()})"
            elif in_multiline_statement and ';' in line:  # End of a multiline variable assignment
                in_multiline_statement = False
                line_type = f"multiline_assignment_end({stack.get_level()})"
            elif in_multiline_statement:  # Middle of a multiline variable assignment
                line_type = f"multiline_assignment({stack.get_level()})"
            else:
                line_type = f"unknown({stack.get_level()})"

            # Append the filename, extension, type, and literal line to the data list
            data.append([f"{os.path.basename(file_path)}:{line_number}", extension, line_type, line])

        return pd.DataFrame(data, columns=['FileName', 'Extension', 'Type', 'LiteralLine'])



    
class CPlusPlusParser(FileParser):
    def __init__(self, file_path):
        super().__init__(file_path)
        
    def get_variables(self, file_path):
        with open(file_path, 'r') as file:
            lines = file.readlines()

        variables = []
        in_multiline_assignment = False
        variable_name = None
        for i, line in enumerate(lines, start=1):
            if '=' in line and ';' in line:  # Simple condition for variable assignment
                name = line.split('=')[0].strip()  # Get the variable name
                variables.append([f"{os.path.basename(self.file_path)}:{i}", None, None, line])
            elif '=' in line:  # Start of a multiline variable assignment
                in_multiline_assignment = True
                variable_name = line.split('=')[0].strip()  # Get the variable name
            elif in_multiline_assignment and ';' in line:  # End of a multiline variable assignment
                in_multiline_assignment = False
                variables.append([f"{os.path.basename(self.file_path)}:{i}", None, None, variable_name + line])

        return pd.DataFrame(variables, columns=['FileName', 'Extension', 'Type', 'LiteralLine'])


    def parse_file(self, file_path):
        with open(file_path, 'r') as file:
            lines = file.readlines()

        data = []
        stack = Stack()

        # Get the actual file extension
        _, extension = os.path.splitext(file_path)

        in_multiline_statement = False
        for line_number, line in enumerate(lines, start=1):
            line = line.strip()

            # Determine the type of the line
            if ';' in line and '=' not in line:
                line_type = f"declaration({stack.get_level()})"
            elif '{' in line:
                stack.push('{')
                line_type = f"block_start({stack.get_level()})"
            elif '}' in line:
                stack.pop()
                line_type = f"block_end({stack.get_level()})"
            elif '=' in line and ';' in line:  # Simple condition for variable assignment
                line_type = f"assignment({stack.get_level()})"
            elif '=' in line:  # Start of a multiline variable assignment
                in_multiline_statement = True
                line_type = f"multiline_assignment_start({stack.get_level()})"
            elif in_multiline_statement and ';' in line:  # End of a multiline variable assignment
                in_multiline_statement = False
                line_type = f"multiline_assignment_end({stack.get_level()})"
            elif in_multiline_statement:  # Middle of a multiline variable assignment
                line_type = f"multiline_assignment({stack.get_level()})"
            else:
                line_type = f"unknown({stack.get_level()})"

            # Append the filename, extension, type, and literal line to the data list
            data.append([f"{os.path.basename(file_path)}:{line_number}", extension, line_type, line])

        return pd.DataFrame(data, columns=['FileName', 'Extension', 'Type', 'LiteralLine'])




class PascalParser(FileParser):
    def __init__(self, file_path):
        super().__init__(file_path)
        
    def get_variables(self, file_path):
        with open(file_path, 'r') as file:
            lines = file.readlines()

        variables = []
        in_multiline_assignment = False
        variable_name = None
        for i, line in enumerate(lines, start=1):
            if ':=' in line and ';' in line:  # Simple condition for variable assignment
                name = line.split(':=')[0].strip()  # Get the variable name
                variables.append([f"{os.path.basename(self.file_path)}:{i}", None, None, line])
            elif ':=' in line:  # Start of a multiline variable assignment
                in_multiline_assignment = True
                variable_name = line.split(':=')[0].strip()  # Get the variable name
            elif in_multiline_assignment and ';' in line:  # End of a multiline variable assignment
                in_multiline_assignment = False
                variables.append([f"{os.path.basename(self.file_path)}:{i}", None, None, variable_name + line])

        return pd.DataFrame(variables, columns=['FileName', 'Extension', 'Type', 'LiteralLine'])

    
    def parse_file(self, file_path):
        with open(file_path, 'r') as file:
            lines = file.readlines()

        data = []
        stack = Stack()
        in_comment = False
        in_string = False
        in_multiline_statement = False

        # Get the actual file extension
        _, extension = os.path.splitext(file_path)

        for line_number, line in enumerate(lines, start=1):
            line = line.strip()

            # Handle multiline comments
            if '{' in line:
                in_comment = True
            if '}' in line:
                in_comment = False
                continue  # Skip multiline comments

            if in_comment:
                continue

            # Handle strings
            if "'" in line:
                in_string = not in_string
            if in_string:
                continue  # Skip strings

            # Determine the type of the line
            if 'var' in line or ':' in line:
                line_type = f"declaration({stack.get_level()})"
            elif 'begin' in line:
                stack.push('begin')
                line_type = f"block_start({stack.get_level()})"
            elif 'end' in line:
                stack.pop()
                line_type = f"block_end({stack.get_level()})"
            elif ':=' in line and ';' in line:  # Simple condition for variable assignment
                line_type = f"assignment({stack.get_level()})"
            elif ':=' in line:  # Start of a multiline variable assignment
                in_multiline_statement = True
                line_type = f"multiline_assignment_start({stack.get_level()})"
            elif in_multiline_statement and ';' in line:  # End of a multiline variable assignment
                in_multiline_statement = False
                line_type = f"multiline_assignment_end({stack.get_level()})"
            elif in_multiline_statement:  # Middle of a multiline variable assignment
                line_type = f"multiline_assignment({stack.get_level()})"
            else:
                line_type = f"unknown({stack.get_level()})"

            # Append the filename, extension, type, and literal line to the data list
            data.append([f"{os.path.basename(file_path)}:{line_number}", extension, line_type, line])

        return pd.DataFrame(data, columns=['FileName', 'Extension', 'Type', 'LiteralLine'])




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
            elif file_extension == '.c':
                self.parsers[file_extension] = CParser(file_path)
            elif file_extension == '.cpp':
                self.parsers[file_extension] = CPlusPlusParser(file_path)
            elif file_extension == '.pas':
                self.parsers[file_extension] = PascalParser(file_path)
            else:
                self.parsers[file_extension] = FileParser(file_path)
            return self.parsers[file_extension]
