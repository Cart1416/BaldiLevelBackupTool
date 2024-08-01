import subprocess
import sys
import os
import shutil
import json
import zipfile
from datetime import datetime

# Function to install packages
def install_package(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Function to ensure wxPython is installed on Windows
def ensure_wxpython_windows():
    try:
        import wx
    except ImportError:
        print("wxPython is not installed. Installing...")
        install_package("wxPython")
        import wx  # Try importing again after installation
    return wx

# Function to check if GTK is available
def check_gtk():
    try:
        import gi
        gi.require_version("Gtk", "3.0")
        from gi.repository import Gtk
        return True
    except ImportError:
        return False

# Function to install GTK on Windows
def install_gtk_windows():
    msys2_url = "https://github.com/msys2/msys2-installer/releases/download/2024-07-27/msys2-x86_64-20240727.exe"
    msys2_installer = "msys2-installer.exe"
    msys2_path = r"C:\msys64"
    msys2_shell = os.path.join(msys2_path, "msys2_shell.cmd")

    if os.path.isdir(msys2_path):
        print("MSYS2 is already installed.")
    else:
        print("This program requires GTK 3")
        print("Downloading MSYS2 installer...")
        subprocess.check_call(["curl", "-L", msys2_url, "-o", msys2_installer])

        print("Installing MSYS2...")
        try:
            subprocess.check_call([msys2_installer, "--al", "--am", "-c"], stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            print(f"Error installing MSYS2: {e.output.decode()}")
            return

        os.remove(msys2_installer)

    if not os.path.isfile(msys2_shell):
        raise FileNotFoundError(f"MSYS2 shell script not found at {msys2_shell}")

    print("Installing GTK...")
    try:
        subprocess.check_call([msys2_shell, "-c", "pacman -Syu --noconfirm && pacman -S --noconfirm mingw-w64-x86_64-gtk3"], shell=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        print(f"Error installing GTK: {e.output.decode()}")
        return

    print("GTK installation completed.")

# Function to install GTK and PyGObject on Linux
def install_gtk_linux():
    print("Installing GTK and PyGObject...")
    try:
        subprocess.check_call(["sudo", "apt-get", "update"])
        subprocess.check_call(["sudo", "apt-get", "install", "-y", "libgtk-3-dev", "python3-gi"])
    except subprocess.CalledProcessError as e:
        print(f"Error installing GTK: {e.output.decode()}")
        return

# Function to ensure GTK and wxPython are installed
def ensure_gtk():
    if sys.platform == "win32":
        ensure_wxpython_windows()
    elif sys.platform == "linux":
        try:
            import gi
            gi.require_version("Gtk", "3.0")
            from gi.repository import Gtk
        except ImportError:
            install_package("pygobject")
            if not check_gtk():
                install_gtk_linux()
    else:
        raise OSError("Unsupported operating system")

# Ensure GTK and wxPython are installed
ensure_gtk()

# Define paths
if sys.platform == "win32":
    username = os.getenv('USERNAME')
    if username is None:
        raise EnvironmentError("Unable to retrieve USERNAME environment variable.")
    base_path = os.path.join(f"C:\\Users\\{username}", "AppData", "LocalLow", "Basically Games", "Baldi's Basics Plus", "CustomLevels")
    #print(base_path)
else:
    base_path = os.path.expanduser("~/.config/unity3d/Basically Games/Baldi's Basics Plus/CustomLevels")

backup_path = os.path.join(base_path, "Backup")
metadata_file = os.path.join(backup_path, "backups.json")

# Ensure backup directory exists
os.makedirs(backup_path, exist_ok=True)

# Files to be backed up
files_to_backup = ["level.cbld", "level.bld"]

# Load or initialize metadata
if os.path.exists(metadata_file):
    with open(metadata_file, 'r') as f:
        backups_metadata = json.load(f)
else:
    backups_metadata = {}

def save_metadata():
    with open(metadata_file, 'w') as f:
        json.dump(backups_metadata, f, indent=4)

def backup_level(name):
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    for file_name in files_to_backup:
        source_file = os.path.join(base_path, file_name)
        if os.path.exists(source_file):
            backup_file = os.path.join(backup_path, f"{file_name}.{timestamp}.bak")
            shutil.copy2(source_file, backup_file)
            backups_metadata[timestamp] = name
    save_metadata()

def list_backups():
    backup_list = [(timestamp, name) for timestamp, name in backups_metadata.items()]
    return backup_list

def load_level(name):
    timestamp = None
    for ts, nm in backups_metadata.items():
        if nm == name:
            timestamp = ts
            break
    if timestamp:
        for file_name in files_to_backup:
            backup_file = os.path.join(backup_path, f"{file_name}.{timestamp}.bak")
            if os.path.exists(backup_file):
                target_file = os.path.join(base_path, file_name)
                shutil.copy2(backup_file, target_file)

def delete_backup(name):
    timestamp = None
    for ts, nm in backups_metadata.items():
        if nm == name:
            timestamp = ts
            break
    if timestamp:
        for file_name in files_to_backup:
            backup_file = os.path.join(backup_path, f"{file_name}.{timestamp}.bak")
            if os.path.exists(backup_file):
                os.remove(backup_file)
        del backups_metadata[timestamp]
        save_metadata()

def export_backup(name, export_path):
    timestamp = None
    for ts, nm in backups_metadata.items():
        if nm == name:
            timestamp = ts
            break
    if timestamp:
        with zipfile.ZipFile(export_path, 'w') as zf:
            for file_name in files_to_backup:
                backup_file = os.path.join(backup_path, f"{file_name}.{timestamp}.bak")
                if os.path.exists(backup_file):
                    zf.write(backup_file, arcname=file_name)

def import_backup(zip_path):
    with zipfile.ZipFile(zip_path, 'r') as zf:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        for file_name in files_to_backup:
            zf.extract(file_name, backup_path)
            backup_file = os.path.join(backup_path, file_name)
            new_backup_file = os.path.join(backup_path, f"{file_name}.{timestamp}.bak")
            os.rename(backup_file, new_backup_file)
        backups_metadata[timestamp] = os.path.splitext(os.path.basename(zip_path))[0]
        save_metadata()

if sys.platform == "win32":
    # wxPython for Windows
    import wx

    class LevelManager(wx.Frame):
        def __init__(self, *args, **kw):
            super(LevelManager, self).__init__(*args, **kw)
            self.panel = wx.Panel(self)
            self.sizer = wx.BoxSizer(wx.VERTICAL)

            self.backup_listbox = wx.ListBox(self.panel)
            self.sizer.Add(self.backup_listbox, 1, wx.EXPAND | wx.ALL, 5)

            self.button_backup = wx.Button(self.panel, label="Backup current level")
            self.button_load = wx.Button(self.panel, label="Load backup")
            self.button_delete = wx.Button(self.panel, label="Delete backup")
            self.button_export = wx.Button(self.panel, label="Export backup")
            self.button_import = wx.Button(self.panel, label="Import backup")
            self.button_exit = wx.Button(self.panel, label="Exit")

            self.sizer.Add(self.button_backup, 0, wx.ALL, 5)
            self.sizer.Add(self.button_load, 0, wx.ALL, 5)
            self.sizer.Add(self.button_delete, 0, wx.ALL, 5)
            self.sizer.Add(self.button_export, 0, wx.ALL, 5)
            self.sizer.Add(self.button_import, 0, wx.ALL, 5)
            self.sizer.Add(self.button_exit, 0, wx.ALL, 5)

            self.panel.SetSizer(self.sizer)

            self.Bind(wx.EVT_BUTTON, self.on_backup, self.button_backup)
            self.Bind(wx.EVT_BUTTON, self.on_load, self.button_load)
            self.Bind(wx.EVT_BUTTON, self.on_delete, self.button_delete)
            self.Bind(wx.EVT_BUTTON, self.on_export, self.button_export)
            self.Bind(wx.EVT_BUTTON, self.on_import, self.button_import)
            self.Bind(wx.EVT_BUTTON, self.on_exit, self.button_exit)

            self.update_backup_listbox()

        def update_backup_listbox(self):
            self.backup_listbox.Clear()
            backups = list_backups()
            for timestamp, name in backups:
                self.backup_listbox.Append(f"{timestamp} - {name}")

        def on_backup(self, event):
            name = wx.GetTextFromUser("Enter a name for the backup:", "Backup Level")
            if name:
                backup_level(name)
                self.update_backup_listbox()

        def on_load(self, event):
            selection = self.backup_listbox.GetSelection()
            if selection != wx.NOT_FOUND:
                name = self.backup_listbox.GetString(selection).split(" - ", 1)[1]
                load_level(name)

        def on_delete(self, event):
            selection = self.backup_listbox.GetSelection()
            if selection != wx.NOT_FOUND:
                name = self.backup_listbox.GetString(selection).split(" - ", 1)[1]
                delete_backup(name)
                self.update_backup_listbox()

        def on_export(self, event):
            selection = self.backup_listbox.GetSelection()
            if selection != wx.NOT_FOUND:
                name = self.backup_listbox.GetString(selection).split(" - ", 1)[1]
                with wx.FileDialog(self, "Save ZIP file", wildcard="ZIP files (*.zip)|*.zip", style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as file_dialog:
                    if file_dialog.ShowModal() == wx.ID_OK:
                        export_backup(name, file_dialog.GetPath())

        def on_import(self, event):
            with wx.FileDialog(self, "Open ZIP file", wildcard="ZIP files (*.zip)|*.zip", style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as file_dialog:
                if file_dialog.ShowModal() == wx.ID_OK:
                    import_backup(file_dialog.GetPath())
                    self.update_backup_listbox()

        def on_exit(self, event):
            self.Close()

    if __name__ == "__main__":
        app = wx.App(False)
        frame = LevelManager(None, title="Level Backup Manager", size=(400, 300))
        frame.Show(True)
        app.MainLoop()

elif sys.platform == "linux":
    import gi
    gi.require_version("Gtk", "3.0")
    from gi.repository import Gtk

    class LevelManager(Gtk.Window):
        def __init__(self):
            super(LevelManager, self).__init__(title="Level Backup Manager")
            self.set_border_width(10)
            self.set_default_size(400, 300)
    
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            self.add(hbox)
    
            self.backup_liststore = Gtk.ListStore(str, str)
            self.update_backup_liststore()
    
            scrolled_window = Gtk.ScrolledWindow()
            scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
            scrolled_window.set_min_content_height(150)  # Approximately 6 items
            hbox.pack_start(scrolled_window, True, True, 0)
    
            self.backup_treeview = Gtk.TreeView(model=self.backup_liststore)
            for i, column_title in enumerate(["Timestamp", "Name"]):
                renderer = Gtk.CellRendererText()
                column = Gtk.TreeViewColumn(column_title, renderer, text=i)
                self.backup_treeview.append_column(column)
    
            scrolled_window.add(self.backup_treeview)
    
            button_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
            hbox.pack_start(button_vbox, False, False, 0)
    
            self.button_backup = Gtk.Button(label="Backup current level")
            self.button_load = Gtk.Button(label="Load backup")
            self.button_delete = Gtk.Button(label="Delete backup")
            self.button_export = Gtk.Button(label="Export backup")
            self.button_import = Gtk.Button(label="Import backup")
            self.button_update = Gtk.Button(label="Check for Updates")
            self.button_exit = Gtk.Button(label="Exit")
    
            self.button_backup.connect("clicked", self.on_backup)
            self.button_load.connect("clicked", self.on_load)
            self.button_delete.connect("clicked", self.on_delete)
            self.button_export.connect("clicked", self.on_export)
            self.button_import.connect("clicked", self.on_import)
            self.button_update.connect("clicked", self.on_update)
            self.button_exit.connect("clicked", self.on_exit)
    
            button_vbox.pack_start(self.button_backup, False, False, 0)
            button_vbox.pack_start(self.button_load, False, False, 0)
            button_vbox.pack_start(self.button_delete, False, False, 0)
            button_vbox.pack_start(self.button_export, False, False, 0)
            button_vbox.pack_start(self.button_import, False, False, 0)
            button_vbox.pack_start(self.button_update, False, False, 0)
            button_vbox.pack_start(self.button_exit, False, False, 0)
    
        def update_backup_liststore(self):
            self.backup_liststore.clear()
            backups = list_backups()
            for timestamp, name in backups:
                self.backup_liststore.append([timestamp, name])
    
        def on_backup(self, widget):
            dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.QUESTION, Gtk.ButtonsType.OK_CANCEL, "Backup Level")
            dialog.format_secondary_text("Enter a name for the backup:")
            entry = Gtk.Entry()
            entry.set_visibility(True)
            dialog.get_content_area().pack_end(entry, False, False, 0)
            dialog.show_all()
            response = dialog.run()
            name = entry.get_text()
            dialog.destroy()
            if response == Gtk.ResponseType.OK and name:
                backup_level(name)
                self.update_backup_liststore()
    
        def on_load(self, widget):
            selection = self.backup_treeview.get_selection()
            model, treeiter = selection.get_selected()
            if treeiter:
                name = model[treeiter][1]
                load_level(name)
    
        def on_delete(self, widget):
            selection = self.backup_treeview.get_selection()
            model, treeiter = selection.get_selected()
            if treeiter:
                name = model[treeiter][1]
                delete_backup(name)
                self.update_backup_liststore()
    
        def on_export(self, widget):
            selection = self.backup_treeview.get_selection()
            model, treeiter = selection.get_selected()
            if treeiter:
                name = model[treeiter][1]
                dialog = Gtk.FileChooserDialog("Save ZIP file", self, Gtk.FileChooserAction.SAVE,
                                               (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_SAVE, Gtk.ResponseType.OK))
                dialog.set_do_overwrite_confirmation(True)
                dialog.add_filter(self.create_zip_filter())
                response = dialog.run()
                if response == Gtk.ResponseType.OK:
                    export_backup(name, dialog.get_filename())
                dialog.destroy()
    
        def on_import(self, widget):
            dialog = Gtk.FileChooserDialog("Open ZIP file", self, Gtk.FileChooserAction.OPEN,
                                           (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
            dialog.add_filter(self.create_zip_filter())
            response = dialog.run()
            if response == Gtk.ResponseType.OK:
                import_backup(dialog.get_filename())
                self.update_backup_liststore()
            dialog.destroy()
    
        def create_zip_filter(self):
            zip_filter = Gtk.FileFilter()
            zip_filter.set_name("ZIP files")
            zip_filter.add_mime_type("application/zip")
            zip_filter.add_pattern("*.zip")
            return zip_filter
    
        def on_update(self, widget):
            self.check_for_updates()
    
        def check_for_updates(self):
            try:
                response = requests.get("https://cart1416.github.io/BaldiLevelBackupTool/version.txt")
                response.raise_for_status()
                latest_version = response.text.strip()
    
                if latest_version > CURRENT_VERSION:
                    dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.INFO, Gtk.ButtonsType.OK_CANCEL,
                                               "Update Available")
                    dialog.format_secondary_text(f"New version {latest_version} is available. Do you want to update?")
                    response = dialog.run()
                    dialog.destroy()
                    if response == Gtk.ResponseType.OK:
                        self.download_and_replace(latest_version)
                else:
                    dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.INFO, Gtk.ButtonsType.OK,
                                               "No Update Available")
                    dialog.format_secondary_text("You are already using the latest version.")
                    dialog.run()
                    dialog.destroy()
            except requests.RequestException as e:
                dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.OK,
                                           "Update Check Failed")
                dialog.format_secondary_text(f"Failed to check for updates: {e}")
                dialog.run()
                dialog.destroy()
    
        def download_and_replace(self, latest_version):
            try:
                response = requests.get("https://cart1416.github.io/BaldiLevelBackupTool/baldilevelsaver.py")
                response.raise_for_status()
    
                script_path = os.path.abspath(sys.argv[0])
                with open(script_path, 'wb') as script_file:
                    script_file.write(response.content)
    
                dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.INFO, Gtk.ButtonsType.OK,
                                           "Update Completed")
                dialog.format_secondary_text("The application has been updated. Please restart the application.")
                dialog.run()
                dialog.destroy()
    
            except requests.RequestException as e:
                dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.OK,
                                           "Update Failed")
                dialog.format_secondary_text(f"Failed to download the update: {e}")
                dialog.run()
                dialog.destroy()
    
        def on_exit(self, widget):
            Gtk.main_quit()
    
    if __name__ == "__main__":
        win = LevelManager()
        win.connect("destroy", Gtk.main_quit)
        win.show_all()
        Gtk.main()
