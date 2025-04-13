import os
import gzip
import tkinter as tk
from tkinter import filedialog

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        if self.tip_window or not self.text:
            return
        x, y, _, _ = self.widget.bbox("insert")  # Get position
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20

        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)  # No window decorations
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify='left',
                         background="#ffffe0", relief='solid', borderwidth=1,
                         font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hide_tip(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None
            
class ModCreator():
    def __init__(self, root):
        self.root = root
        self.root.title("Conception 1 Mod Creator")
        self.root.minsize(700, 700)
        self.root.resizable(False, False)
        self.extension = ".CON1"
        self.modname = tk.StringVar()
        self.mod_info = tk.StringVar()
        
        self.gui_labels()
        self.gui_entries()
        self.gui_misc()
    def gui_labels(self):
        tk.Label(self.root, text=f"Mod Creator for applying mods to Conception 1.").place(x=10, y=10)
        tk.Label(self.root, text=f"Mod Name(only the name, leave out extension):").place(x=10, y=100)
        tk.Label(self.root, text=f"Mod Description:").place(x=10, y=200)
        
    def gui_entries(self):
        tk.Entry(self.root, textvariable=self.modname).place(x=280, y=100)
    
    def gui_misc(self):
        self.status_label = tk.Label(self.root, text="", fg="green")
        self.status_label.place(x=10, y=500)
        self.description = tk.Text(self.root, height = 20, width = 52)
        self.description.place(x=110, y=200)
        btn1 = tk.Button(self.root, text = "Create Mod", command = self.create_mod, height = 3, width = 20)
        btn1.place(x=500,y=50)
        ToolTip(btn1, "This button creates a mod file from a file modded that belonged to the game.")
        btn2 = tk.Button(self.root, text = "Convert File", command = self.convert_file, height = 3, width = 20)
        btn2.place(x=500,y=200)
        ToolTip(btn2, "This button is used for converting files that were't part of the game to a compatible mod file, \n select the file you want applied and then the file you want the game to ignore.")
    def convert_file(self):
        new_mod = self.modname.get() + self.extension
        self.file_path = filedialog.askopenfilename(
            initialdir=os.getcwd(),
            title="Select a file to convert into a Conception 1 Mod File",
            filetypes=(
                ("Supported Files", "*.*"),
            ))
        self.orig_path = filedialog.askopenfilename(
            initialdir=os.getcwd(),
            title="Conception 1 file to replace(the file isn't lost, the game just ignores the original file infavor of the mod when applied to the CFSI file)",
            filetypes=(
                ("Supported Files", "*.*"),
            ))
        try:
            if self.file_path:
                selected_file_size = os.path.getsize(self.orig_path)
                # Get mod description from Text widget
                description_text = self.description.get("1.0", tk.END).strip()
                description_bytes = description_text.encode("utf-8")
                description_len = len(description_bytes)

                # Write to new mod file, get the mod enabling and disabling metadata, and read the file to be converted
                with open(new_mod, "ab") as f1, open(self.orig_path, "r+b") as original, open(self.file_path, "rb") as f2:
                    f1.write(description_len.to_bytes(2, "little"))  # Write length (2 bytes)
                    f1.write(description_bytes)                      # Write description

                    # Go to metadata at the end of the original game's file for mod enabling and disabling for the mod manager
                    original.seek(selected_file_size - 4)
                    current_position = original.tell()
                    tail_metadata = int.from_bytes(original.read(4), "little")
                    original.seek(current_position - tail_metadata)
                    tail_metadata_offset = original.tell()
                    
                    container_len = int.from_bytes(original.read(1), "little") # length of container file's name
                    container = original.read(container_len) # container the mod is to be applied to
                    tail_data = original.read(12) # other metadata(file metadata offset, initial_file_offset, and original size), used for mod disabling
                    compression_marker = int.from_bytes(original.read(1), "little") # marker saying if compression was originally used
                    original.seek(0) # return to start of file

                    if compression_marker == 1: # If compression was used for the game's original file
                        all_data = f2.read() # read the user's file to be converted
                        data_to_comp = all_data # compress the data from the user's file to be converted
                        compressed_data = self.compression(data_to_comp)

                        # Modify the OS byte within the GZIP header
                        compressed_data = bytearray(compressed_data)
                        compressed_data[9] = 0x03 # Original value the game uses
                        
                        f1.write(container_len.to_bytes(1, "little"))
                        f1.write(container)
                        f1.write(tail_data)
                        f1.write(compression_marker.to_bytes(1, "little"))
                        f1.write(len(data_to_comp).to_bytes(4, "little")) # write decompressed size of the file
                        f1.write(compressed_data)
                    else: # if compression wasn't used for the game's original file
                        f1.write(container_len.to_bytes(1, "little"))
                        f1.write(container)
                        f1.write(tail_data)
                        f1.write(compression_marker.to_bytes(1, "little"))
                        all_data = f2.read()
                        f1.write(all_data)

                self.status_label.config(text=f"The file {new_mod} was converted into a mod successfully!", fg="green")
        except Exception as e:
            self.status_label.config(text=f"Error: {str(e)}", fg="red")
            
    def create_mod(self):
        new_mod = self.modname.get() + self.extension
        self.file_path = filedialog.askopenfilename(
            initialdir=os.getcwd(),
            title="Select a Conception 1 file",
            filetypes=(
                ("Supported Files", "*.*"),
            ))
        
        try:
            if self.file_path:
                selected_file_size = os.path.getsize(self.file_path)
                # Get mod description from Text widget
                description_text = self.description.get("1.0", tk.END).strip()
                description_bytes = description_text.encode("utf-8")
                description_len = len(description_bytes)

                # Write to new mod file
                with open(new_mod, "ab") as f1, open(self.file_path, "r+b") as original:
                    f1.write(description_len.to_bytes(2, "little"))  # Write length (2 bytes)
                    f1.write(description_bytes)                      # Write description

                    original.seek(selected_file_size - 4)
                    current_position = original.tell()
                    tail_metadata = int.from_bytes(original.read(4), "little")
                    original.seek(current_position - tail_metadata)
                    tail_metadata_offset = original.tell()
                    
                    container_len = int.from_bytes(original.read(1), "little") # length of container file's name
                    container = original.read(container_len) # container the mod is to be applied to
                    tail_data = original.read(12) # other metadata(file metadata offset, initial_file_offset, and original size), used for mod disabling
                    compression_marker = int.from_bytes(original.read(1), "little") # marker saying if compression was originally used
                    original.seek(0) # return to start of file

                    if compression_marker == 1:
                        all_data = original.read()
                        data_to_comp = all_data[:tail_metadata_offset]
                        compressed_data = self.compression(data_to_comp)

                        # Modify the OS byte within the GZIP header
                        compressed_data = bytearray(compressed_data)
                        compressed_data[9] = 0x03 # Original value the game uses
                        
                        f1.write(container_len.to_bytes(1, "little"))
                        f1.write(container)
                        f1.write(tail_data)
                        f1.write(compression_marker.to_bytes(1, "little"))
                        f1.write(len(data_to_comp).to_bytes(4, "little")) # write decompressed size of the file
                        f1.write(compressed_data)
                    else:
                        f1.write(container_len.to_bytes(1, "little"))
                        f1.write(container)
                        f1.write(tail_data)
                        f1.write(compression_marker.to_bytes(1, "little"))
                        all_data = original.read()
                        f1.write(all_data[:tail_metadata_offset])

                self.status_label.config(text=f"The Mod {new_mod} was created successfully!", fg="green")
        except Exception as e:
            self.status_label.config(text=f"Error: {str(e)}", fg="red")

    def compression(self, data):
        """This function handles compressing files that need to be compressed before applied as a mod"""
        return gzip.compress(data, 1, mtime=0)

                    
def runner():
    root = tk.Tk()
    creator = ModCreator(root)
    root.mainloop()
if __name__ == "__main__":
    runner()
