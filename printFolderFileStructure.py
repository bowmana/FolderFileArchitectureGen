import os
import argparse
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path


def print_folder_structure(directory, prefix="", is_last=True, exclude_patterns=None, selected_items=None):
    """
    Recursively print the folder and file structure starting from the given directory.
    
    Args:
        directory (str): Path to the directory to print
        prefix (str): Prefix to use for the current line (for indentation)
        is_last (bool): Whether this is the last item in the current directory
        exclude_patterns (list): List of patterns to exclude from the output
        selected_items (set): Set of paths that should be included
    """
    if exclude_patterns is None:
        exclude_patterns = []
    
    # Skip if this directory is not selected and not root
    if selected_items is not None and directory != target_path and directory not in selected_items:
        return
        
    # Get the base name of the directory
    base_name = os.path.basename(directory)
    
    # Skip if this directory matches any exclude pattern
    if any(pattern in directory for pattern in exclude_patterns):
        return
    
    # Print the current directory with appropriate prefix
    connector = "└── " if is_last else "├── "
    print(f"{prefix}{connector}{base_name}/")
    
    # Prepare the prefix for items inside this directory
    new_prefix = prefix + ("    " if is_last else "│   ")
    
    # Get all items in the directory
    try:
        items = sorted(os.listdir(directory))
        
        # Filter out excluded items
        items = [item for item in items if not any(pattern in item for pattern in exclude_patterns)]
        
        # Process all items
        for i, item in enumerate(items):
            item_path = os.path.join(directory, item)
            is_last_item = (i == len(items) - 1)
            
            # Only process if this item is selected or its parent is selected
            if selected_items is None or item_path in selected_items or directory in selected_items:
                if os.path.isdir(item_path):
                    print_folder_structure(item_path, new_prefix, is_last_item, exclude_patterns, selected_items)
                else:
                    file_connector = "└── " if is_last_item else "├── "
                    print(f"{new_prefix}{file_connector}{item}")
    except PermissionError:
        print(f"{new_prefix}└── [Permission Denied]")
    except Exception as e:
        print(f"{new_prefix}└── [Error: {str(e)}]")


def select_folder():
    """
    Open a file dialog to select a folder.
    
    Returns:
        str: Path to the selected folder or None if canceled
    """
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    folder_path = filedialog.askdirectory(title="Select Folder to Print Structure")
    root.destroy()
    return folder_path if folder_path else None


def select_items_in_folder(directory):
    """
    Display a tree view GUI to select which items to include.
    
    Args:
        directory (str): Path to the parent directory
        
    Returns:
        set: Set of selected item paths
    """
    selected_paths = set()
    last_item_clicked = None
    
    def populate_tree(tree, parent, path, level=0, max_initial_level=2):
        try:
            # Get and sort items (directories first, then files)
            items = os.listdir(path)
            dirs = [item for item in items if os.path.isdir(os.path.join(path, item))]
            files = [item for item in items if not os.path.isdir(os.path.join(path, item))]
            
            # Sort directories and files separately
            dirs.sort()
            files.sort()
            
            # Process directories first
            for item in dirs:
                item_path = os.path.join(path, item)
                item_id = tree.insert(parent, 'end', text=item, 
                                     values=(item_path, "folder"),
                                     open=(level < max_initial_level))
                
                # If we're at less than the maximum initial level, populate children immediately
                if level < max_initial_level:
                    populate_tree(tree, item_id, item_path, level + 1, max_initial_level)
            
            # Then process files
            for item in files:
                item_path = os.path.join(path, item)
                tree.insert(parent, 'end', text=item, 
                           values=(item_path, "file"))
                
        except PermissionError:
            tree.insert(parent, 'end', text="[Permission Denied]")
        except Exception as e:
            tree.insert(parent, 'end', text=f"[Error: {str(e)}]")
    
    def item_expanded(event):
        item = tree.focus()
        
        # Check if this item has been populated
        if not tree.get_children(item):
            values = tree.item(item, "values")
            if len(values) >= 2 and values[1] == "folder":
                path = values[0]
                populate_tree(tree, item, path, max_initial_level=0)  # Don't auto-expand these children
    
    def get_all_children(item=""):
        """Recursively get all children of an item"""
        children = list(tree.get_children(item))
        for child in list(children):
            children.extend(get_all_children(child))
        return children
    
    def selection_changed(event):
        nonlocal last_item_clicked
        
        current_selection = tree.selection()
        if not current_selection:
            return
            
        # Get the newly selected item (the last one clicked)
        new_selection = current_selection[-1]
        
        # If Control key is not pressed, handle normal selection behavior
        if not (event.state & 0x4):  # 0x4 is the mask for Control key
            # If a folder is selected, select all its children
            item_values = tree.item(new_selection, "values")
            if len(item_values) >= 2 and item_values[1] == "folder":
                # Get all children of this folder
                children = get_all_children(new_selection)
                
                # Add all children to the current selection
                tree.selection_add(children)
        else:
            # If Control key is pressed and this is a previously selected item, 
            # allow deselecting it without affecting other selections
            if last_item_clicked == new_selection:
                tree.selection_remove(new_selection)
                
        # Update the last clicked item
        last_item_clicked = new_selection
    
    def on_ok():
        # Collect all selected paths
        for item_id in tree.selection():
            values = tree.item(item_id, "values")
            if len(values) >= 1:
                selected_paths.add(values[0])
        
        root.destroy()
    
    def on_cancel():
        selected_paths.clear()
        root.destroy()
    
    # Create the main window
    root = tk.Tk()
    root.title("Select Items to Include")
    root.geometry("800x600")
    
    # Add instructions
    instructions = ttk.Label(root, text="Click to select items. Ctrl+click to select/deselect individual items.\nSelected items (highlighted in blue) will be included in the output.")
    instructions.pack(pady=10)
    
    # Create a frame for the tree and scrollbars
    frame = ttk.Frame(root)
    frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Create vertical and horizontal scrollbars
    vsb = ttk.Scrollbar(frame, orient="vertical")
    hsb = ttk.Scrollbar(frame, orient="horizontal")
    
    # Create the treeview with extended selection mode
    tree = ttk.Treeview(frame, columns=("path", "type"), 
                        yscrollcommand=vsb.set, 
                        xscrollcommand=hsb.set,
                        selectmode="extended")
    
    # Configure the scrollbars
    vsb.config(command=tree.yview)
    hsb.config(command=tree.xview)
    
    # Place the tree and scrollbars
    vsb.pack(side=tk.RIGHT, fill=tk.Y)
    hsb.pack(side=tk.BOTTOM, fill=tk.X)
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    # Configure columns
    tree.column("#0", width=300, minwidth=200)
    tree.column("path", width=0, stretch=tk.NO)
    tree.column("type", width=0, stretch=tk.NO)
    
    tree.heading("#0", text="File/Folder")
    
    # Bind event for selection changes
    tree.bind("<<TreeviewSelect>>", selection_changed)
    
    # Bind event for expanding items
    tree.bind("<<TreeviewOpen>>", item_expanded)
    
    # Add buttons
    button_frame = ttk.Frame(root)
    button_frame.pack(fill=tk.X, padx=10, pady=10)
    
    ttk.Button(button_frame, text="OK", command=on_ok).pack(side=tk.RIGHT, padx=5)
    ttk.Button(button_frame, text="Cancel", command=on_cancel).pack(side=tk.RIGHT, padx=5)
    
    # Populate the root of the tree
    root_id = tree.insert('', 'end', text=os.path.basename(directory), values=(directory, "folder"), open=True)
    
    # Populate the initial view
    populate_tree(tree, root_id, directory)
    
    # Start the main loop
    root.mainloop()
    
    return selected_paths


# Global variable to store the target path
target_path = None

def main():
    global target_path
    
    parser = argparse.ArgumentParser(description="Print folder structure in a tree-like format")
    parser.add_argument("path", nargs="?", default=None, help="Path to the directory to print (default: select via GUI)")
    parser.add_argument("-e", "--exclude", nargs="+", default=[], help="Patterns to exclude from the output")
    parser.add_argument("--gui", action="store_true", help="Use GUI to select folder and items to include")
    args = parser.parse_args()
    
    # If no path provided or --gui flag is used, open folder selection dialog
    target_path = args.path
    if target_path is None or args.gui:
        target_path = select_folder()
        if not target_path:
            print("No folder selected. Exiting.")
            return
    
    # Convert to absolute path
    target_path = os.path.abspath(target_path)
    
    if not os.path.exists(target_path):
        print(f"Error: Path '{target_path}' does not exist")
        return
    
    if not os.path.isdir(target_path):
        print(f"Error: Path '{target_path}' is not a directory")
        return
    
    # Open GUI to select which items to include
    selected_items = select_items_in_folder(target_path)
    
    # Print the results
    print(f"Structure of: {target_path}")
    if selected_items:
        print(f"Including {len(selected_items)} selected item(s)")
        print_folder_structure(target_path, exclude_patterns=args.exclude, selected_items=selected_items)
    else:
        print("No items selected. Nothing to print.")


if __name__ == "__main__":
    main()
