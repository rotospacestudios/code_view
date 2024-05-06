import ast
import sys
import importlib.metadata
import tkinter as tk
from tkinter import filedialog
import subprocess

def select_python_file():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(filetypes=[('Python Files', '*.py')])
    return file_path

def is_package_installed(package_name):
    packages = importlib.metadata.packages_distributions()
    return not package_name in packages

def modify_python_file(file_path):
    with open(file_path, 'r') as f:
        content = f.read()
        tree = ast.parse(content)
        imports = [node.names[0].name for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]

    core_modules = list(sys.builtin_module_names)
    external_modules = [module for module in imports if module not in core_modules and module not in ['sys', 'subprocess'] and is_package_installed(module)]
    external_modules = ' '.join([f'"{module}"' for module in external_modules])

    with open(file_path, 'w') as f:
        f.write(f'import subprocess\n'
                f'import sys\n'
                f'subprocess.check_call([sys.executable, "-m", "pip", "install", {external_modules}])\n'
                f'{content}\n')

def create_executable(script_path):
    subprocess.run(['pyinstaller', '--onefile', script_path])

def main():
    print("Rotospace Studios Packager")
    script_path = select_python_file()
    modify_python_file(script_path)
    create_executable(script_path)

if __name__ == "__main__":
    main()
