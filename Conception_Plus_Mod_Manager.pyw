import os
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

class ModManager():
    def __init__(self, root):
        self.root = root
        self.root.title("Conception 1 Mod Manager")
        self.root.minsize(1100, 700)
        self.root.resizable(False, False)
        self.backups = "Backups_Folder"
        self.mods_enabled_file = "Conception_1.MODS"
        self.main_container = "00000000.cfsi"
        self.bgm = "bgm.cfsi"
        self.voice = "voice.cfsi"
        self.main_cfsi_size = 2929987872 # main container size
        self.bgm_size = 107557248 # bgm container size
        self.voice_size = 1122974352 # voice container size
        self.modname = None
        self.offset = None # metadata offset
        self.initial_offset = None
        self.original_size = None
        self.mod_data = None
        self.pad_len = None
        self.container_modded = None
        self.contained_to_mod = None
        self.container_offset = None

        self.gui_labels()
        self.gui_misc()
        self.current_mods()
    def gui_labels(self):
        tk.Label(self.root, text="Mod Manager for applying and disabling mods to Conception 1.").place(x=10, y=10)
        tk.Label(self.root, text="Mod Name:").place(x=10, y=100)
        tk.Label(self.root, text="Mod Description:").place(x=10, y=200)
        tk.Label(self.root, text="Current Mods Enabled:").place(x=570,y=200)

        self.mod_file = tk.Label(self.root, text="No mod selected.")
        self.mod_file.place(x=100, y=100)
        
    def gui_misc(self):
        self.status_label = tk.Label(self.root, text="", fg="green")
        self.status_label.place(x=10, y=500)
        self.description = tk.Text(self.root, wrap = tk.WORD, height = 20, width = 52)
        self.description.place(x=110, y=200)
        self.description.config(state=tk.DISABLED)
        btn1 = tk.Button(self.root, text = "Select a Mod", command = self.mod_reader, height = 3, width = 20)
        btn1.place(x=300,y=100)
        ToolTip(btn1, "This button handles mod reading, when you select a mod it will read its data.")
        btn2 = tk.Button(self.root, text = "Apply Mod", command = self.mod_writer, height = 3, width = 20)
        btn2.place(x=500,y=100)
        ToolTip(btn2, "This button handles mod writing, it will apply the mod to the matching CFSI container file.")
        btn3 = tk.Button(self.root, text = "Disable Mod", command = self.disable_mod, height = 3, width = 20)
        btn3.place(x=700,y=100)
        ToolTip(btn3, "This button handles mod disabling, it's good if you want to disable one or several mods but not all of them.")
        btn4 = tk.Button(self.root, text = "Disable All Mods and replace CFSI container files", command = self.disable_mods, height = 3, width = 40)
        btn4.place(x=100,y=600)
        ToolTip(btn4, "This button handles disabling all mods but also \n replaces all CFSI container files with fresh unmodded copies. \n It'll take a few seconds since it's writing several gigabytes of data.")
        self.mods_list = tk.Listbox(height = 20, width = 52)
        self.mods_list.place(x=700,y=200)

    def update_mods(self, mod):
        """This function is used for updating the .MODS file such as if you disabled a mod, it will remove it from the .MODS file for correct display"""
        try:
            self.mods_list.delete(0, tk.END)
            with open(self.mods_enabled_file, "r+b") as f1: # open the file that contains mods applied
                while True:
                    current_position = f1.tell()
                    modname_len = int.from_bytes(f1.read(1), "little") # read length of mod's filename
                    if not modname_len:
                        break # EOF
                    container_len = int.from_bytes(f1.read(1), "little") # read length of container's filename
                    mod_name = f1.read(modname_len).decode()
                    container_name = f1.read(container_len).decode()
                    
                    f1.read(12) # read the metadata
                    if mod.strip().lower() == mod_name.strip().lower(): # If the mod selected to be disabled matches the read mod name
                        f1.seek(current_position) # go to disabled mod
                        nulls_to_write = 2 + modname_len + container_len + 12 # calculate needs null values to write
                        f1.write(b'\x00' * nulls_to_write) # write null values to overwrite the disabled mod's metadata
                        return_offset = f1.tell() # get the current offset
                        rest_of_mods = f1.read() # read any mods that came after the disabled mod
                        f1.seek(return_offset) # go to the end of where the disabled mod's metadata was
                        f1.write(b'\x00' * len(rest_of_mods)) # write null values to overwrite all data that came after the disabled mod
                        f1.seek(current_position) # go to the start of where the disabled mod's metadata was
                        f1.write(rest_of_mods) # write the mods that were still enabled that came after the disabled mod's metadata
                        
                        cleaner_length = f1.tell() # used to calculate how many bytes need read
                        f1.seek(0) # seek start of file to begin reading enabled mods
                        kept_mods = f1.read(cleaner_length) # read the enabled mods
                        self.clean_mods(kept_mods) # call cleaning function that will recreate the .MODS file with only enabled mod metadata sections
                        return True

        except Exception as e:
            self.status_label.config(text=f"Error: {str(e)}", fg="red")
            return False
                    
    def clean_mods(self, data):
        """This function is used to remake the .MODS file after a single mod has been disabled, bringing a fresh copy with only the enabled mods stored"""
        try:
            with open(self.mods_enabled_file, "wb") as f1: # create the new .MODS file
                f1.write(data) # write only the enabled mods
            with open(self.mods_enabled_file, "rb") as f2: # open the .MODS file to read and update the listbox with current enabled mods
                while True:
                    current_position = f2.tell()
                    modname_len = int.from_bytes(f2.read(1), "little") # read length of mod's filename
                    if not modname_len:
                        break # EOF
                    container_len = int.from_bytes(f2.read(1), "little") # read length of container's filename
                    mod_name = f2.read(modname_len).decode()
                    container_name = f2.read(container_len)
                    
                    f2.read(12) # read the metadata
                    self.mods_list.insert(tk.END, mod_name)
                    
        except Exception as e:
            self.status_label.config(text=f"Error: {str(e)}", fg="red")
            return False
            
    def current_mods(self):
        """This function is used for checking mods that are currently enabled"""
        try:
            self.mods_list.delete(0, tk.END)
            with open(self.mods_enabled_file, "rb") as f1: # open the file that contains mods applied
                while True:
                    modname_len = int.from_bytes(f1.read(1), "little") # read length of mod's filename
                    if not modname_len:
                        break # EOF
                    container_len = int.from_bytes(f1.read(1), "little") # read length of container's filename
                    mod_name = f1.read(modname_len).decode()
                    container_name = f1.read(container_len).decode()
                    
                    f1.read(4) # read the metadata offset to the original file's initial offset to file data
                    f1.read(4) # read the initial offset for the original non-modded file's file data
                    f1.read(4) # read the file size for the original non-modded file
                    
                    self.mods_list.insert(tk.END, mod_name)
                    
        except Exception as e:
            self.status_label.config(text=f"Error: {str(e)}", fg="red")

    def check_if_applied(self, mod):
        """This handles checking if a user has enabled a mod before to see if it actually needs disabled"""
        try:
            with open(self.mods_enabled_file, "rb") as f1: # open the file that contains mods applied
                while True:
                    modname_len = int.from_bytes(f1.read(1), "little") # read length of mod's filename
                    if not modname_len:
                        break # EOF
                    container_len = int.from_bytes(f1.read(1), "little") # read length of container's filename
                    mod_name = f1.read(modname_len).decode()
                    container_name = f1.read(container_len).decode()
                    
                    f1.read(4) # read the metadata offset to the original file's initial offset to file data
                    f1.read(4) # read the initial offset for the original non-modded file's file data
                    f1.read(4) # read the file size for the original non-modded file

                    if mod.strip().lower() == mod_name: # If the mod selected to be disabled has been applied before
                        return True
                    else: # If the mod selected to be disabled hasn't been applied before
                        self.status_label.config(text=f"The mod file '{mod}' was not within the {self.mods_enabled_file} file, are you sure you have applied that mod before?", fg="red")
                        return False
        except Exception as e:
            self.status_label.config(text=f"Error: {str(e)}", fg="red")
            return False
    def disable_mods(self):
        """This handles disabling all mods, updating the Conception_1.MODS file, and reverting the CFSI container that had mods enabled"""
        cfsi_list = [self.main_container, self.bgm, self.voice]
        try:
            for i in cfsi_list:
                backup_path = os.path.join(self.backups, i)
                with open(backup_path, "rb") as f1:
                    original_data = f1.read() # unmodded container file data
                    with open(i, "wb") as f2: # overwriting the modded container file with unmodded container file's data
                        f2.write(original_data)
                        
            self.status_label.config(text=f"All Mods have been disabled and the CFSI container files have been replaced with fresh unmodded copies.", fg="green")
        except Exception as e:
            self.status_label.config(text=f"Error: {str(e)}", fg="red")

        self.current_mods()
        
        with open(self.mods_enabled_file, "w") as a1:
            pass
        self.mods_list.delete(0, tk.END)
            
    def mod_list(self):
        """This is used for storing mods currently enabled along with metadata for each mod for disabling."""
        with open(self.mods_enabled_file, "ab") as w1:
            w1.write(len(self.modname).to_bytes(1, "little")) # write length of mod's filename
            w1.write(len(self.container_modded).to_bytes(1, "little")) # write length of container's filename
            w1.write(self.modname.encode()) # write the encoded mod's name
            w1.write(self.container_modded.encode()) # write the encoded container file's name

            # This section is metadata used for mod disabling
            w1.write(self.offset.to_bytes(4, "little")) # write the metadata offset to the original file's initial offset to file data
            w1.write(self.initial_offset) # write the initial offset for the original non-modded file's file data
            w1.write(self.original_size) # write the file size for the original non-modded file
            
    def mod_reader(self):
        self.file_path = filedialog.askopenfilename(
            initialdir=os.getcwd(),
            title="Select a Conception 1 mod file",
            filetypes=(("Supported Files", "*.CON1"),)
        )
        try:
            if self.file_path:
                filename = os.path.basename(self.file_path)
                self.modname = filename
                self.mod_file.config(text=filename)

                with open(self.file_path, "rb") as f1:
                    # Step 1: Read the description
                    description_len = int.from_bytes(f1.read(2), "little")
                    description = f1.read(description_len).decode()
                    
                    # Step 2: Read the container filename
                    container_name_len = int.from_bytes(f1.read(1), "little")
                    container_name = f1.read(container_name_len).decode()
                    self.container_to_mod = container_name
                    
                    # Step 3: Display description
                    self.description.config(state=tk.NORMAL)
                    self.description.delete("1.0", tk.END)
                    self.description.insert(tk.END, description)
                    self.description.config(state=tk.DISABLED)

                    # Step 4: Read mod disabling metadata
                    file_metadata_offset = int.from_bytes(f1.read(4), "little")
                    file_base_offset = f1.read(4) # this contains the original offset before math
                    file_size = f1.read(4) # original file size
                    comp_marker = f1.read(1) # compression marker

                    self.offset = file_metadata_offset
                    self.initial_offset = file_base_offset
                    self.original_size = file_size
                    
                    # Step 5: read mod data
                    data = f1.read()

                    # Ensure mod_data aligns to 16-byte boundary
                    padding = (16 - (len(data) % 16)) % 16
                    if padding:
                        data += b'\x00' * padding
                    self.pad_len = padding
                    self.mod_data = data
        except Exception as e:
            self.status_label.config(text=f"Error: {str(e)}", fg="red")

    def mod_writer(self):
        """Handles applying the mod"""
        
        base_offset = 0x2D7A0 # first step for calculating main container offsets
        base_bgm_offset = 0x520 # used as part of calculating the final offset to file data for bgm container
        base_voice_offset = 0x95690 # used as part of calculating the final offset to file data for voice container
        base_value = 16 # second step for calculating
        try:
            if self.container_to_mod:
                if self.container_to_mod == self.main_container:
                    self.container_offset = base_offset
                elif self.container_to_mod == self.bgm:
                    self.container_offset = base_bgm_offset
                elif self.container_to_mod == self.voice:
                    self.container_offset = base_voice_offset
                    
                self.container_modded = os.path.basename(self.container_to_mod) # get container filename, used for mod_list function
                end_of_file = os.path.getsize(self.container_to_mod) # used for obtaining the offset at the end of the file
                with open(self.container_to_mod, "ab") as f1: # open the selected container file to apply mod
                    f1.seek(end_of_file) # seek end of file
                    current_offset = f1.tell() # get the offset
                    f1.write(self.mod_data) # write the mod data
                    
                with open(self.container_to_mod, "r+b") as f2: # open the selected container file to update metadata
                    f2.seek(self.offset) # go to the metadata offset that stores the filename, file offset, and file size
                    subbed_offset = current_offset - self.container_offset # subtract the offset of the appended mod by the base off
                    final_offset = subbed_offset // base_value # divide the subbed offset by base value
                    f2.write(final_offset.to_bytes(4, "little")) # write current offset
                    calculate_size = len(self.mod_data) - self.pad_len # this is used to calculate the file size without the padding being counted
                    f2.write(calculate_size.to_bytes(4, "little")) # write current mod's file size

                self.status_label.config(text=f"The Mod '{self.modname}' was enabled without issue.", fg="green")

                self.mod_list()
                    
        except Exception as e:
            self.status_label.config(text=f"Error: {str(e)}", fg="red")

        self.current_mods()

    def disable_mod(self):
        """handles mod disabling"""
        self.file_path = filedialog.askopenfilename(
            initialdir=os.getcwd(),
            title="Select the Conception 1 mod file to disable",
            filetypes=(("Supported Files", "*.CON1"),)
        )
        try:
            if self.file_path:
                filename = os.path.basename(self.file_path)
                self.modname = filename
                self.mod_file.config(text=filename)

                with open(self.file_path, "rb") as f1:
                    # (Steps 1 - 3 remain unchanged)
                    description_len = int.from_bytes(f1.read(2), "little")
                    description = f1.read(description_len).decode()
                    container_name_len = int.from_bytes(f1.read(1), "little")
                    container_name = f1.read(container_name_len).decode()
                    self.container_to_mod = container_name
                    file_metadata_offset = int.from_bytes(f1.read(4), "little")
                    file_base_offset = f1.read(4)  # original file offset
                    file_size = f1.read(4)         # original file size
                    comp_marker = f1.read(1)       # compression marker

                    # Step 4: check if the mod has been applied before
                    self.check_if_applied(filename)

                    # Step 5: disable the mod by scanning the .MODS file
                    mod_found = False
                    with open("Conception_1.MODS", "rb") as f:
                        while True:
                            mod_name_len_bytes = f.read(1)
                            if not mod_name_len_bytes:
                                break  # End of file
                            mod_name_len = int.from_bytes(mod_name_len_bytes, "little")
                            container_name_len = int.from_bytes(f.read(1), "little")

                            mod_name = f.read(mod_name_len).decode()
                            container_name = f.read(container_name_len).decode()

                            metadata_offset = int.from_bytes(f.read(4), "little")
                            original_offset = f.read(4)
                            original_size = f.read(4)

                            if mod_name == self.modname:
                                with open(container_name, "r+b") as container_file:
                                    container_file.seek(metadata_offset)
                                    container_file.write(original_offset)
                                    container_file.write(original_size)

                                self.status_label.config(
                                    text=f"Mod '{self.modname}' disabled and original file restored.",
                                    fg="blue"
                                )
                                mod_found = True
                                break

                    if not mod_found:
                        self.status_label.config(text="Mod not found in tracking file.", fg="red")

                    # Step 6: Update the .MODS file (call the updater)
                    self.update_mods(filename)
                    
        except Exception as e:
            self.status_label.config(text=f"Error: {str(e)}", fg="red")


def runner():
    root = tk.Tk()
    manager = ModManager(root)
    root.mainloop()
if __name__ == "__main__":
    runner()
