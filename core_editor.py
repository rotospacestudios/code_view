import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import os
import subprocess
import traceback
from file_parser import ParserManager, LuaFileParser, FileParser, CParser,CPlusPlusParser, PythonParser
import pandas as pd
import msvcrt
import atexit

class ApplyChangesDialog(simpledialog.Dialog):
    def body(self, master):
        self.num_changes = len(self.master.change_manager.file_changes)
        self.num_files = len(self.master.change_manager.file_changes)

        self.label = ttk.Label(master, text=f'Number of changes: {self.num_changes}\nNumber of affected files: {self.num_files}')
        self.label.pack()

        self.skip_var = tk.IntVar()
        self.skip_checkbutton = tk.Checkbutton(master, text="Don't ask me again", variable=self.skip_var)
        self.skip_checkbutton.pack()

        self.confirm_button = ttk.Button(master, text='Confirm', command=self.on_confirm_clicked)
        self.confirm_button.pack()

        self.reject_button = ttk.Button(master, text='Reject', command=self.on_reject_clicked)
        self.reject_button.pack()

    def on_confirm_clicked(self):
        skip_dialogs = self.skip_var.get()
        if not skip_dialogs:
            self.master.change_manager.resolve_changes()
        self.destroy()

    def on_reject_clicked(self):
        self.destroy()
        
        
class Change:
    def __init__(self, line_number, old_content, new_content, change_type):
        self.line_number = line_number
        self.old_content = old_content
        self.new_content = new_content
        self.change_type = change_type  # 'insert', 'delete', or 'edit'

class FileChange:
    def __init__(self, file_path):
        self.file_path = file_path
        self.changes = {}  # Dictionary to store changes by line number

def write_to_file(file_path, data):
    with open(file_path, 'w') as file:
        msvcrt.locking(file.fileno(), msvcrt.LK_LOCK, 1)
        file.write(data)
        msvcrt.locking(file.fileno(), msvcrt.LK_UNLCK, 1)
        
class ChangeManager:
    def __init__(self):
        self.file_changes = {}  # Dictionary to store FileChange objects by file path

    def add_change(self, file_path, line_number, old_content, new_content, change_type):
        if file_path not in self.file_changes:
            self.file_changes[file_path] = FileChange(file_path)
        change = Change(line_number, old_content, new_content, change_type)
        self.file_changes[file_path].changes[line_number] = change
        

    def rename_variable(self, old_name, new_name, file_paths):
        for file_path in file_paths:
            if file_path not in self.file_changes:
                self.file_changes[file_path] = FileChange(file_path)
            with open(file_path, 'r') as file:
                lines = file.readlines()
            for i, line in enumerate(lines):
                if old_name in line:
                    new_line = line.replace(old_name, new_name)
                    change = Change(i, line, new_line, 'edit')
                    self.file_changes[file_path].changes[i] = change

    def phantom_resolve(self, file_path):
        # Check if there are any changes for the given file
        file_change = self.file_changes.get(file_path)
        if file_change is None:
            return None

        # Read the file lines into a dictionary
        with open(file_path, 'r') as file:
            lines = {i: line for i, line in enumerate(file.readlines())}

        # Apply the changes to the dictionary
        for line_number, change in sorted(file_change.changes.items()):
            if change.change_type == 'delete':
                lines[line_number] = '\n'  # Replace the content with a newline
            elif change.change_type == 'insert':
                lines[line_number] = change.new_content
            else:  # 'edit'
                lines[line_number] = change.new_content

        # Return the final record
        return lines
    def insert_line(self, line_number, new_line, file_path):
        if file_path not in self.file_changes:
            self.file_changes[file_path] = FileChange(file_path)
        change = Change(line_number, None, new_line, 'insert')
        self.file_changes[file_path].changes[line_number] = change
        
    def resolve_changes(self, master):
        skip_dialogs = False
        for file_change in self.file_changes.values():
            if not skip_dialogs:
                dialog = ApplyChangesDialog(master, file_change.file_path)
                master.wait_window(dialog)
                if dialog.result is None:  # The dialog was closed without clicking Yes or No
                    continue
                save, skip_dialogs = dialog.result
                if not save:
                    continue
            with open(file_change.file_path, 'r') as file:
                lines = file.readlines()
            for line_number, change in sorted(file_change.changes.items()):
                if change.change_type == 'delete':
                    lines[line_number] = '\n'  # Replace the content with a newline
                elif change.change_type == 'insert':
                    lines.insert(line_number, change.new_content)
                else:  # 'edit'
                    lines[line_number] = change.new_content
            with open(file_change.file_path, 'w') as file:
                msvcrt.locking(file.fileno(), msvcrt.LK_LOCK, 1)
                file.writelines(lines)
                msvcrt.locking(file.fileno(), msvcrt.LK_UNLCK, 1)


class DirectoryAndFileTypesDialog(simpledialog.Dialog):
    def body(self, master):
        self.master = master;
        print(self.master)
        self.directory_label = ttk.Label(master, text="Directory:")
        self.directory_label.grid(row=0, column=0)
        self.directory_entry = ttk.Entry(master)
        self.directory_entry.grid(row=0, column=1)

        self.file_types_label = ttk.Label(master, text="File types:")
        self.file_types_label.grid(row=1, column=0)
        self.file_types_listbox = tk.Listbox(master, selectmode='multiple')
        self.file_types_listbox.grid(row=1, column=1)
        self.file_types_listbox.bind('<Button-1>', self.on_file_types_listbox_clicked)
        self.file_types_listbox.bind('<<ListboxSelect>>', self.on_file_types_listbox_clicked)

        for file_type in self.master.file_types:
            self.file_types_listbox.insert('end', file_type)

        # Create a frame for the buttons
        self.button_frame = ttk.Frame(master)
        self.button_frame.grid(row=2, column=0, columnspan=2)
        
    def destroy(self):
        if self.master is not None:
            for c in list(self.master.children.values()):
                c.destroy()
        super().destroy()

    def validate(self):
        directory = self.directory_entry.get()
        file_types = self.file_types_listbox.curselection()

        if not directory:
            messagebox.showerror("Error", "Please enter a directory.")
            return False

        if not os.path.isdir(directory):
            messagebox.showerror("Error", "The entered directory does not exist.")
            return False

        if not file_types:
            messagebox.showerror("Error", "Please select at least one file type.")
            return False

        return True

    def on_file_types_listbox_clicked(self, event):
        self.file_types_listbox.selection_clear(0, 'end')
    def apply(self):
        self.directory = self.directory_entry.get()
        print(f"Directory: {self.directory}")  # Print the directory

        self.file_types = set()
        for dirpath, dirnames, filenames in os.walk(self.directory):
            for filename in filenames:
                file_extension = os.path.splitext(filename)[1]
                if file_extension in self.master.file_types:
                    self.file_types.add(file_extension)
        self.file_types = list(self.file_types)
        print(f"File types: {self.file_types}")  # Print the file types

        self.master.on_directory_and_file_types_selected(self.directory, self.file_types)
        self.destroy()
    def ok(self, event=None):
        if not self.validate():
            self.initial_focus.focus_set()  # put focus back
            return

        self.apply()



class CoreEditor(tk.Frame):
    def __init__(self, master, selected_files, directory, file_types):
        super().__init__(master)

        self.master = master

        self.files = selected_files  # Use selected_files instead of files
        self.directory = directory
        self.file_types = file_types
        self.records = []
        self.parser_manager = ParserManager()  # Create an instance of ParserManager
        self.change_manager = ChangeManager()
    
        self.file_paths = {}  # Dictionary to store file paths by item ID
        self.tree_view = ttk.Treeview(self, selectmode='extended')
        self.tree_view.grid(row=0, column=0, sticky='nsew')
        self.tree_view.bind('<<TreeviewSelect>>', self.on_tree_view_clicked)

        self.create_table()
        
        # Create a frame for the buttons and set its layout to vertical stacking
        self.button_frame = ttk.Frame(self)
        self.button_frame.grid(row=1, column=0, columnspan=2, sticky='ew')

        
        # Add the Change Root button to the frame
        self.change_root_button = ttk.Button(self.button_frame, text='Change Root', command=self.show_dialog)
        self.change_root_button.pack(side='left')
        
        # Add the Run Script button to the frame
        self.run_script_button = ttk.Button(self.button_frame, text='Run Script', command=self.on_run_script_clicked)
        self.run_script_button.pack(side='left', padx=(0, 10))

        # Add the Show Records button to the frame
        self.show_records_button = ttk.Button(self.button_frame, text='Show Records', command=self.on_show_records_clicked)
        self.show_records_button.pack(side='left', padx=(0, 10))

        self.apply_changes_button = ttk.Button(self.button_frame, text='Apply Changes to Records', command=self.on_apply_changes_clicked)
        self.apply_changes_button.pack(side='left', padx=(0, 10))

        # Configure the grid to distribute extra space equally among columns and rows
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.populate_tree_view(self.directory)
    def release_all_locks(self):
        for file_change in self.change_manager.file_changes.values():
            with open(file_change.file_path, 'a') as file:  # Open the file in append mode
                msvcrt.locking(file.fileno(), msvcrt.LK_UNLCK, 1)

    def save(self):
        self.change_manager.resolve_changes(self)


    def show_dialog(self):
        dialog = DirectoryAndFileTypesDialog(self)
        # Wait for the dialog to be destroyed before accessing its attributes
        self.wait_window(dialog)
        self.on_directory_and_file_types_selected(dialog.directory, dialog.file_types)
        self.directory = dialog.directory
        self.file_types = dialog.file_types
        self.populate_tree_view(self.directory)

    def on_directory_and_file_types_selected(self, directory, file_types):
        self.directory = directory
        self.file_types = file_types
        if os.path.isfile(self.directory):
            self.populate_tree_view_with_file(self.directory)
        else:
            self.populate_tree_view(self.directory)
    
    def populate_tree_view(self, directory):
        for dirpath, dirnames, filenames in os.walk(directory):
            for filename in filenames:
                file_extension = os.path.splitext(filename)[1]
                if file_extension in self.file_types:
                    relative_path = os.path.relpath(os.path.join(dirpath, filename), directory)
                    file_path = os.path.join(dirpath, filename)
                    item_id = self.tree_view.insert('', 'end', text=relative_path)
                    self.file_paths[item_id] = file_path  # Store the file path in the dictionary

    def on_edit_field(self, new_value, column_name):
        # Get all selected items from the tree_view
        selected_items = self.tree_view.selection()
        for selected_item in selected_items:
            # Set the new value for each selected item
            self.tree_view.set(selected_item, column=column_name, value=new_value)

    def on_show_records_clicked(self):
        changes_str = '\n'.join([f'{change.index} {change.file_path} {change.old_content} {change.new_content}' for change in self.change_manager.changes])
        messagebox.showinfo('Changes', changes_str)
        
        
    def on_apply_changes_clicked(self):
        self.core_editor.save()
        
    def populate_table(self, filename):
        for i in self.table_widget.get_children():
            self.table_widget.delete(i)

        file_path = os.path.join(self.directory, filename)
        file_extension = os.path.splitext(filename)[1]
        parser = self.parser_manager.get_parser(file_extension, file_path)

        parsed_data = parser.parse_file(file_path)  # Pass the file_path argument


        print(f"Parsed data: {parsed_data}")  # Add this line

        if file_extension not in self.parser_manager.parsers:
            parsed_data = pd.DataFrame([('', '', '', '')], columns=['FileName', 'Extension', 'Type', 'LiteralLine'])
        else:
            parsed_data = pd.DataFrame(parsed_data, columns=['FileName', 'Extension', 'Type', 'LiteralLine'])

        for index, row in parsed_data.iterrows():
            self.table_widget.insert('', 'end', values=row.tolist())
            
    def on_tree_view_clicked(self, event):
        selected_items = self.tree_view.selection()
        print(f"Selected items: {selected_items}")  # Print the selected items
        if len(selected_items) == 1:
            selected_item = selected_items[0]
            file_path = self.file_paths.get(selected_item)  # Retrieve the file path from the dictionary
            print(f"Selected item: {selected_item}, File path: {file_path}")  # Print the selected item and file path
            if file_path:
                self.change_manager.resolve_changes(file_path)  # Resolve changes for the selected file
                self.populate_table(file_path)  # Call populate_table when a single item is selected
        elif len(selected_items) > 1:
            for selected_item in selected_items:
                file_path = self.file_paths.get(selected_item)  # Retrieve the file path from the dictionary
                print(f"Selected item: {selected_item}, File path: {file_path}")  # Print the selected item and file path
                if file_path:
                    self.change_manager.resolve_changes(file_path)  # Resolve changes for the selected file
                    self.populate_table_with_variables(file_path)  # Call populate_table_with_variables when multiple items are selected
        else:
            print("No item selected in the tree view.")



    def on_tree_view_right_click(self, event):
        self.context_menu.post(event.x_root, event.y_root)

        # Remove the following line to prevent creating changes
        # change_type = "your_change_type"  # Provide the appropriate change type
        # self.change_manager.add_change(filename, old_content, new_content, change_type)

    def get_file_content(self, filename, apply_soft_changes=True):
        file_path = os.path.join(self.directory, filename)
        file_extension = os.path.splitext(filename)[1]
        parser = self.parser_manager.get_parser(file_extension, file_path)

        parsed_data = parser.parse_file(file_path)  # Parse the file using the parser

        content = ""
        if apply_soft_changes:
            changes = self.change_manager.file_changes.get(file_path)

            if changes:
                for line_number, change in sorted(changes.changes.items()):
                    if change.change_type == 'delete':
                        parsed_data[line_number] = '\n'  # Replace the content with a newline
                    elif change.change_type == 'insert':
                        parsed_data.insert(line_number, change.new_content)
                    else:  # 'edit'
                        parsed_data[line_number] = change.new_content

            for line in parsed_data:
                content += line + "\n"  # Concatenate each line with a newline character
        else:
            with open(file_path, 'r') as file:
                content = file.read()

        return content


    def style_rows(self, filename):
        for change in self.change_manager.changes:
            if change.file_path == filename:
                item_id = self.tree_view.get_children()[change.line_number]
                if change.change_type == 'insert':
                    self.tree_view.item(item_id, tags='insert')
                elif change.change_type == 'delete':
                    self.tree_view.item(item_id, tags='delete')
                else:  # 'edit'
                    self.tree_view.item(item_id, tags='edit')

        self.tree_view.tag_configure('insert', background='green')
        self.tree_view.tag_configure('delete', background='red')
        self.tree_view.tag_configure('edit', background='yellow')

    def on_table_widget_right_click(self, event):
        # Identify the row of the right-click event
        row_id = self.table_widget.identify_row(event.y)
        # Select the row
        self.table_widget.selection_set(row_id)
        # Create the context menu
        self.create_context_menu()
        # Show the context menu
        self.context_menu.post(event.x_root, event.y_root)
        
    def create_context_menu(self):
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Insert Line Above", command=self.insert_line_above)
        self.context_menu.add_command(label="Insert Line Below", command=self.insert_line_below)
        self.context_menu.add_command(label="Edit Line", command=self.edit_line)
        self.context_menu.add_command(label="Delete Line", command=self.delete_line)

        # Bind the right-click event to the table_widget instead of the tree_view
        self.table_widget.bind("<Button-3>", self.show_context_menu)
    def populate_table_with_variables(self, file_path):
        # Clear the table
        for i in self.table_widget.get_children():
            self.table_widget.delete(i)

        file_extension = os.path.splitext(file_path)[1]
        parser = self.parser_manager.get_parser(file_extension, file_path)
        variables = parser.get_variables(file_path)  # Get the variables from the file

        # Get the phantom record for the file
        phantom_record = self.change_manager.phantom_resolve(file_path)
        if phantom_record is not None:
            for line_number, new_content in phantom_record.items():
                variables[line_number] = new_content

        for _, variable in variables.iterrows():
            # Add the variable to the table
            self.table_widget.insert('', 'end', values=(variable['FileName'], variable['Extension'], variable['Type'], variable['LiteralLine']))
    

    def populate_table(self, file_path):
        # Clear the table
        for i in self.table_widget.get_children():
            self.table_widget.delete(i)

        file_extension = os.path.splitext(file_path)[1]
        parser = self.parser_manager.get_parser(file_extension, file_path)
        parsed_data = parser.parse_file(file_path)  # Get the parser output

        # Get the final record using phantom_resolve
        final_record = self.change_manager.phantom_resolve(file_path)
        if final_record is not None:
            for line_number, new_content in final_record.items():
                parsed_data[line_number] = new_content

        for _, data in parsed_data.iterrows():
            # Add the data to the table
            self.table_widget.insert('', 'end', values=(data['FileName'], data['Extension'], data['Type'], data['LiteralLine']))


    def show_context_menu(self, event):
        # Get the selected item from the table_widget
        self.selected_item = self.table_widget.selection()[0]
        self.context_menu.post(event.x_root, event.y_root)

    def insert_line_above(self):
        selected_items = self.tree_view.selection()
        for selected_item in selected_items:
            file_path = self.file_paths.get(selected_item)  # Retrieve the file path from the dictionary
            selected_index = self.tree_view.index(selected_item)
            new_item_id = self.tree_view.insert('', selected_index, text='New Line')
            self.file_paths[new_item_id] = file_path  # Store the file path in the dictionary

    def insert_line_below(self):
        selected_items = self.tree_view.selection()
        for selected_item in selected_items:
            file_path = self.file_paths.get(selected_item)  # Retrieve the file path from the dictionary
            selected_index = self.tree_view.index(selected_item)
            new_item_id = self.tree_view.insert('', selected_index + 1, text='New Line')
            self.file_paths[new_item_id] = file_path  # Store the file path in the dictionary

    def edit_line(self):
        # Get the selected item from the table_widget
        selected_item = self.table_widget.selection()[0]
        # Get the values of the selected item
        item_values = self.table_widget.item(selected_item, 'values')
        # The column name is always "LiteralLine"
        column_name = "LiteralLine"
        # Get the new value. This depends on your application. For example, you can ask the user to enter the new value.
        new_value = simpledialog.askstring("Input", "Enter the new value:")
        # Call on_edit_field with the new value and column name
        self.on_edit_field(new_value, column_name)
    def delete_line(self):
        selected_item = self.tree_view.selection()[0]
        self.tree_view.delete(selected_item)



    def create_table(self):
        self.table_widget = ttk.Treeview(self, columns=("FileName", "Extension", "Type", "LiteralLine"))
        self.table_widget['show'] = 'headings'
        self.table_widget.column("FileName", width=50)
        self.table_widget.column("Extension", width=50)
        self.table_widget.column("Type", width=50)
        self.table_widget.column("LiteralLine", width=150)
        self.table_widget.column("FileName", stretch=False)
        self.table_widget.column("Extension", stretch=False)
        self.table_widget.column("Type", stretch=False)
        self.table_widget.column("LiteralLine", stretch=False)
        self.table_widget.heading("FileName", text="File Name")
        self.table_widget.heading("Extension", text="Extension")
        self.table_widget.heading("Type", text="Type")
        self.table_widget.heading("LiteralLine", text="Literal Line")
        self.table_widget.grid(row=0, column=1, sticky='nsew')
        self.table_widget.bind("<Button-3>", self.on_table_widget_right_click)
    def report_callback_exception(self, exc, val, tb):
        # Print the exception to the console
        print(f"Caught exception: {exc} {val}")
        traceback.print_tb(tb)

        # Show an error message to the user
        messagebox.showerror("Error", "An error occurred. Please see the console for details.")
    def on_run_script_clicked(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            subprocess.run(['python', file_path])

    def on_calculate_size_clicked(self):
        dir_path = filedialog.askdirectory()
        if dir_path:
            total_size = self.get_dir_size(dir_path)
            messagebox.showinfo('Total Size', f'Total size: {total_size} bytes')

    def on_show_records_clicked(self):
        records_str = '\n'.join([f'{record[0]} {record[1]} {record[2]} {record[3]}' for record in self.records])
        messagebox.showinfo('Records', records_str)

    def get_dir_size(self, dir_path):
        total = 0
        for dirpath, dirnames, filenames in os.walk(dir_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                total += os.path.getsize(fp)
        return total
