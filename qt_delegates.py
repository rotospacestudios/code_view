import tkinter as tk
from tkinter import ttk, filedialog
import atexit
import os
import hashlib
import tempfile
from PIL import Image, ImageTk
import ctypes
import json
class FileTree(ttk.Treeview):
    def __init__(self, parent=None, directory=None, file_types=None):
        super().__init__(parent)
        self.directory = directory
        self.file_types = file_types
        self['show'] = 'tree'
        self.tag_configure('enabled', font=('Arial', 10, 'bold italic'))
        self.bind('<Double-1>', self.on_double_click)
        self.bind('<<TreeviewOpen>>', self.on_open)
        self.bind('<<TreeviewClose>>', self.on_close)

        # Create the context menu
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Discover", command=self.discover_selected_folder)
        self.bind('<Button-3>', self.show_context_menu)

        # Preload the icons

        self.populate_tree(self.directory)

    def populate_tree(self, node, parent=''):
        node_id = hashlib.md5(node.encode()).hexdigest()  # Use the hash of the node as the item ID
        if os.path.isdir(node):
            text = f"(F) {os.path.basename(node)}"
        elif node.endswith('.py'):
            text = f"(Python) {os.path.basename(node)}"
        elif node.endswith('.java'):
            text = f"(Java) {os.path.basename(node)}"
        # Add more elif statements for other file types
        else:
            text = os.path.basename(node)

        if not self.exists(node_id):

            self.insert(parent, 'end', node_id, text=text, open=False, values=[node, False])
            if os.path.isdir(node):
                for entry in sorted(os.scandir(node), key=lambda e: (not e.is_dir(), e.name)):
                    self.populate_tree(entry.path, node_id)
        else:
            self.item(node_id, text=text)

        if parent == '':
            self.item(node_id, open=True)

    def show_context_menu(self, event):
        self.context_menu.post(event.x_root, event.y_root)

    def discover_selected_folder(self):
        selected_item = self.selection()[0]
        folder_path = self.item(selected_item)['values'][0]
        print(f"Discovering folder: {folder_path}")
        # Add your discovery code here
        
    def on_double_click(self, event):
        item = self.selection()[0]
        # Toggle the 'checked' field
        node, checked = self.item(item, 'values')
        self.item(item, values=[node, not checked])
        # Update the image to represent the new check state
        self.item(item, image=self.checked_icon if not checked else self.unchecked_icon)

        
    def on_open(self, event):
        item = self.selection()[0]
        self.populate_tree(self.item(item)['values'][0], item)

    def on_close(self, event):
        pass  # Do nothing when a node is closed


    def populate_node(self, node):
        # Clear the node
        self.delete(*self.get_children(node))

        # Populate the node
        for root, dirs, files in os.walk(node):
            parent = self.insert(node, 'end', text=root, open=True)
            for dir in dirs:
                self.insert(parent, 'end', text=dir, image=self.folder_icon)
            for file in files:
                self.insert(parent, 'end', text=file, image=self.file_icon)


    def get_total_size(self, directory):
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(directory):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if not os.path.islink(fp):
                    total_size += os.path.getsize(fp)
        total_size /= 1024 * 1024  # Convert to MB
        if total_size < 1024:
            return f"{total_size:.2f} MB"
        else:
            return f"{total_size / 1024:.2f} GB"
        


class ListExplorer(ttk.Treeview):
    def __init__(self, parent=None, directory=None, file_types=None, on_folder_selected=None):
        super().__init__(parent)
        self.directory = directory
        self.file_types = file_types
        self.on_folder_selected = on_folder_selected
        self.path = None  # Initialize the path attribute
        self.selected_directories = []  # Initialize the selected directories list
        self.selected_files = set()  # Add this line
        self.json_paths = {}  # Initialize the json_paths attribute

        self.checked_icon = self.load_image("checked_icon.png")
        self.unchecked_icon = self.load_image("unchecked_icon.png")       
        self.init_ui()
        
    def load_image(self, image_path):
        try:
            image = Image.open(image_path)
            return ImageTk.PhotoImage(image)
        except FileNotFoundError:
            # Provide a fallback image or handle the error gracefully
            # For example, you can return a default icon image
            default_icon_path = os.path.join(os.path.dirname(__file__), "default_icon.png")
            default_image = Image.open(default_icon_path)
            return ImageTk.PhotoImage(default_image)

    def init_ui(self):
        self.paned_window = tk.PanedWindow(self, orient='horizontal')
        self.paned_window.pack(fill='both', expand=True)

        self.tree = FileTree(self.paned_window, self.directory, self.file_types)
        self.tree.pack(side='top', fill='both', expand=True)
        self.tree['selectmode'] = 'extended'

        self.tree.bind('<<TreeviewSelect>>', self.on_tree_clicked)
        self.tree.bind('<Button-3>', self.show_context_menu)

        self.json_output = tk.Text(self.paned_window)
        self.json_output.pack(side='top', fill='both', expand=True)

        self.paned_window.add(self.tree)
        self.paned_window.add(self.json_output)

        self.button_frame = tk.Frame(self)
        self.button_frame.pack(side='bottom', fill='x')

        self.ok_button = tk.Button(self.button_frame, text="OK", command=self.confirm)
        self.ok_button.pack(side='left')

        self.cancel_button = tk.Button(self.button_frame, text="Cancel", command=self.cancel)
        self.cancel_button.pack(side='right')
    
        self.pop_out_button = tk.Button(self.button_frame, text="Pop Out", command=self.pop_out)
        self.pop_out_button.pack(side='right')
        self.change_root_button = tk.Button(self.button_frame, text="Change Root", command=self.change_root)
        self.change_root_button.pack(side='right')


        
    def on_tree_clicked(self, event):
        selected_items = self.tree.selection()
        if selected_items:
            selected_item = selected_items[0]
            file_path = self.tree.item(selected_item, 'values')[0]  # Get the file path
            if os.path.isdir(file_path):  # Use the file path instead of the item ID
                if file_path in self.selected_directories:  # Use the file path instead of the item ID
                    self.selected_directories.remove(file_path)  # Use the file path instead of the item ID
                else:
                    self.selected_directories.append(file_path)  # Use the file path instead of the item ID
                self.update_shopping_cart()  # Update the shopping cart


    def show_context_menu(self, event):
        selected_item = self.tree.identify_row(event.y)
        file_path = self.tree.item(selected_item, 'values')[0]  # Get the file path
        menu = tk.Menu(self, tearoff=0)
        if file_path in self.selected_files:  # Use the file path instead of the item ID
            menu.add_command(label="Disable", command=lambda: self.toggle_selection(file_path))  # Use the file path instead of the item ID
        else:
            menu.add_command(label="Enable", command=lambda: self.toggle_selection(file_path))  # Use the file path instead of the item ID
        menu.post(event.x_root, event.y_root)


    def change_root(self):
        directory = filedialog.askdirectory()
        if directory:
            self.directory = directory
            self.tree.populate_tree(directory)

    def toggle_selection(self, file_path):
        # Calculate the hash of the file path
        node_id = hashlib.md5(file_path.encode()).hexdigest()

        # Check if the item exists in the tree view
        if self.tree.exists(node_id):
            # If the item exists, toggle its selection
            # If the item exists, toggle its selection
            if file_path in self.selected_files:
                self.selected_files.remove(file_path)
                self.tree.item(node_id, tags='')  # Use the node ID instead of the file path
                # Remove the file path from the JSON object
                del self.json_paths[file_path]
            else:
                self.selected_files.add(file_path)
                self.tree.item(node_id, tags='enabled')  # Use the node ID instead of the file path
                # Add the file path to the JSON object
                self.json_paths[file_path] = os.path.abspath(file_path)
        else:
            # If the item doesn't exist, print an error message
            print(f"Error: The item with the file path '{file_path}' doesn't exist in the tree view.")

    def navigate(self):
        selected_item = self.tree.selection()[0]
        if os.path.isdir(selected_item):
            self.directory = selected_item
            self.tree.delete(*self.tree.get_children())
            self.tree.populate_tree()

    def pop_out(self):
        self.tree.populate_tree(self.tree.directory)
        
    def update_shopping_cart(self):
        # Clear the shopping cart
        self.json_output.delete('1.0', tk.END)

        # Add the selected directories to the shopping cart
        for directory in self.selected_directories:
            self.json_output.insert(tk.END, f"{directory}\n")
        # Add the selected files to the shopping cart
        for file in self.selected_files:
            self.json_output.insert(tk.END, f"{file}\n")
        # Update the JSON output with the JSON paths
        self.json_output.insert(tk.END, json.dumps(self.json_paths, indent=4))

    def confirm(self):
        if messagebox.askyesno("Confirm", "Do you want to gather the JSON?"):
            if self.callback:
                self.callback(self.selected_directories)
            print(f"Directories selected: {self.selected_directories}")
            self.tree.populate_tree(self.directory)
    def cancel(self):
        print("Operation cancelled")
