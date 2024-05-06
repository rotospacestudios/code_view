import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog

from qt_delegates import ListExplorer
from file_type_explorer import FileTypeExplorer
from core_editor import CoreEditor
from file_parser import ParserManager, LuaFileParser, FileParser, CParser,CPlusPlusParser, PythonParser,FileParser
import os
from file_types_module import file_types
import atexit

class FileTypeExplorer(tk.Toplevel):
    def __init__(self, master, directory, file_types):
        super().__init__(master)

        self.directory = directory
        self.file_types = file_types

        self.checkboxes = []
        for file_type in self.get_file_types(directory):
            if file_type in self.file_types:
                checkbox = tk.Checkbutton(self, text=file_type)
                checkbox.pack(side='top', anchor='w')
                self.checkboxes.append(checkbox)

        self.ok_button = tk.Button(self, text="OK", command=self.confirm)
        self.ok_button.pack(side='top', pady=10)

        self.pack(fill='both', expand=True)  # Share layout horizontally

    def get_file_types(self, directory):
        file_types = set()
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_extension = os.path.splitext(file)[1]
                file_types.add(file_extension)
        return list(file_types)

    def confirm(self):
        selected_file_types = [checkbox.cget('text') for checkbox in self.checkboxes if checkbox.var.get()]
        self.master.on_file_types_selected(selected_file_types)
        self.destroy()



class MainApplication(tk.Tk):
    def __init__(self, file_types):
        super().__init__()
        
        self.file_types = file_types
        self.directory = filedialog.askdirectory(initialdir=os.path.dirname(os.path.realpath(__file__)))
        self.selected_files = self.get_files_from_directory(self.directory, self.file_types)


        self.core_editor = CoreEditor(None, self.selected_files, self.directory, self.file_types)
        self.core_editor.pack(side='top', fill='both', expand=True)
        self.geometry('800x600')  # Set the size of the window to 800x600 pixels

        atexit.register(self.core_editor.release_all_locks)
        
    def get_files_from_directory(self, directory, file_types):
        selected_files = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_extension = os.path.splitext(file)[1]
                if file_extension in file_types:
                    selected_files.append(os.path.join(root, file))
        return selected_files


if __name__ == "__main__":
    main_app = MainApplication(file_types)  # Pass the file_types variable as an argument
    main_app.mainloop()
