import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import os

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
        self.ok_button.pack(side='bottom')

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