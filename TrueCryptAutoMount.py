import os
import sys
import wmi
import time
import winreg
import win32api
import win32file
import platform
import functools
import pythoncom
import subprocess
import xml.dom.minidom
from PyQt5 import QtGui, QtCore, QtWidgets, uic

__version__ = "0.4.1"

# Windows7 Taskbar Grouping (Don't group with Python)
if platform.system() == 'Windows' and platform.release() == '7':
    import ctypes
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('TrueCrypt_AutoMount')

class GenericThread(QtCore.QThread):
    def __init__(self, function, *args, **kwargs):
        QtCore.QThread.__init__(self)
        self.function = function
        self.args = args
        self.kwargs = kwargs
 
    def __del__(self):
        self.wait()
 
    def run(self):
        self.function(*self.args,**self.kwargs)
        return

class About_Dialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        QtWidgets.QDialog.__init__(self, parent)
        self.ui = uic.loadUi('about.ui', self)
        self.ui.labelVersion.setText(__version__)
        self.setModal(True)
        self.show()
        
class BatchCommands_Dialog(QtWidgets.QDialog):
    def __init__(self, parent=None, command_list=[]):
        QtWidgets.QDialog.__init__(self, parent)
        self.command_list = command_list
        
        self.ui = uic.loadUi('batch.ui', self)
        
        for command in command_list:
            self.ui.listCommands.addItem(command)
        
        self.setModal(True)
        self.ui.buttonAdd.clicked.connect(self.button_add_click_event)
        self.ui.buttonDelete.clicked.connect(self.button_del_click_event)
        self.ui.buttonUp.clicked.connect(self.button_up_click_event)
        self.ui.buttonDown.clicked.connect(self.button_down_click_event)
        self.ui.buttonOK.clicked.connect(self.button_ok_click_event)
        self.ui.buttonCancel.clicked.connect(self.button_cancel_click_event)
        self.ui.listCommands.currentTextChanged.connect(self.list_currenttextchanged_event)
        self.show()
        
    def getCommandList(self):
        if QtWidgets.QDialog.exec_(self) == QtWidgets.QDialog.Accepted:
            text_list = []
            for i in range(self.ui.listCommands.count()):
                text_list.append(self.ui.listCommands.item(i).text())
            return (True, text_list)
        else:
            return (False, [])
        
    def list_currenttextchanged_event(self, text):
        self.ui.editCommand.setText(text)
        
    def button_add_click_event(self):
        if self.ui.editCommand.text():
            self.ui.listCommands.addItem(self.ui.editCommand.text())
            self.ui.editCommand.clear()
        
    def button_del_click_event(self):
        self.ui.listCommands.takeItem(self.ui.listCommands.currentRow())
    
    def button_up_click_event(self):
        item = self.ui.listCommands.currentItem()
        row = self.ui.listCommands.currentRow()
        self.ui.listCommands.takeItem(row)
        self.ui.listCommands.insertItem(row - 1, item)
        self.ui.listCommands.setCurrentItem(item)
    
    def button_down_click_event(self):
        item = self.ui.listCommands.currentItem()
        row = self.ui.listCommands.currentRow()
        self.ui.listCommands.takeItem(row)
        self.ui.listCommands.insertItem(row + 1, item)
        self.ui.listCommands.setCurrentItem(item)
        
    def button_ok_click_event(self):
        self.accept()
        
    def button_cancel_click_event(self):
        self.reject()
        
class TrueCrypt_AutoMounter(QtWidgets.QMainWindow):

    thread1_signal = QtCore.pyqtSignal()
    thread2_signal = QtCore.pyqtSignal()

    def __init__(self, interface, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent=parent)
        
        self.ui = uic.loadUi('gui.ui', self)
        
        icon = QtGui.QIcon()
        icon.addFile('icons/ico16.png', QtCore.QSize(16, 16))
        icon.addFile('icons/ico24.png', QtCore.QSize(24, 24))
        icon.addFile('icons/ico32.png', QtCore.QSize(32, 32))
        icon.addFile('icons/ico48.png', QtCore.QSize(48, 48))
        self.setWindowIcon(icon)
        
        self.interface = interface
        self.settings = {}
        self.drive_dict = {}
        self.keyfiles = []
        self.password = None
        self.tc_path = ""
        self.sysTrayMenuActions = {}
        self.start_minimized = False
        self.automount_onstart = False
        self.automount_onconnect = False
        
        self.load_settings()
        self.actions_set_checked()
        self.actions_load_default_keyfiles()
        
        if self.automount_onstart:
            self.search_new_drive()
        else:
            self.drive_dict = self.get_physical_drives()

        self.icons = {}
        self.icons["logo"] = icon
        self.icons["blank"] = QtGui.QIcon()
        self.icons["drive"] = QtGui.QIcon("icons/silk/drive.png")
        self.icons["drive_add"] = QtGui.QIcon("icons/silk/drive_add.png")
        self.icons["drive_cd"] = QtGui.QIcon("icons/silk/drive_cd.png")
        self.icons["drive_link"] = QtGui.QIcon("icons/silk/drive_link.png")
        self.icons["drive_network"] = QtGui.QIcon("icons/silk/drive_network.png")
        self.icons["drive_flash"] = QtGui.QIcon("icons/silk/drive_flash.png")
        self.icons["drive_go"] = QtGui.QIcon("icons/silk/drive_go.png")
        self.icons["drive_error"] = QtGui.QIcon("icons/silk/drive_error.png")
        self.icons["application_double"] = QtGui.QIcon("icons/silk/application_double.png")
        self.icons["logo_big"] = QtGui.QPixmap("icons/tc_logo.gif")
        
        self.ui.labelLogo.setPixmap(self.icons["logo_big"])
        
        self.ui.treeVolumeList.setColumnWidth(0,50)  # Drive Icon + Drive Letter
        self.ui.treeVolumeList.setColumnWidth(1,120) # Drive Caption
        self.ui.treeVolumeList.setColumnWidth(2,40)
        self.ui.treeVolumeList.setColumnWidth(3,35)
        self.ui.treeVolumeList.setColumnWidth(4,220)
        self.ui.treeVolumeList.setColumnWidth(5,60)
        self.ui.treeVolumeList.setColumnWidth(6,155)
        self.ui.treeVolumeList.setColumnWidth(7,35)
        
        w32_logicaldrives = self.interface.Win32_LogicalDisk()
        logical_drives = self.get_logical_drives(w32_logicaldrives)

        for c in "CDEFGHIJKLMNOPQRSTUVWXYZ":
            self.ui.treeVolumeList.addTopLevelItem(self.treeview_add_new_drive(c, logical_drives, w32_logicaldrives))
        
        self.treeview_update_drives(w32_logicaldrives)
        self.combo_update_physical_drives()
        
        self.ui.buttonAssign.clicked.connect(self.button_assign_click_event)
        self.ui.buttonUnassign.clicked.connect(self.button_unassign_click_event)
        self.ui.buttonPostMountBatch.clicked.connect(self.button_postmountbatch_click_event)
        self.ui.buttonMount.clicked.connect(self.button_mount_click_event)
        self.ui.buttonDismount.clicked.connect(self.button_dismount_click_event)
        self.ui.buttonMountAll.clicked.connect(self.button_mount_all_click_event)
        self.ui.buttonDismountAll.clicked.connect(self.button_dismount_all_click_event)
        self.ui.comboVolumes.activated['QString'].connect(self.combo_drives_activated_event)
        self.ui.treeVolumeList.itemSelectionChanged.connect(self.treeview_selectionchanged_event)
        self.ui.buttonExit.clicked.connect(app.quit)
        self.ui.actionPath_to_TrueCrypt.triggered.connect(self.action_set_tc_path)
        self.ui.actionStart_with_Windows.triggered.connect(self.action_set_autostart)
        self.ui.actionStart_Minimized.triggered.connect(self.action_set_start_minimized)
        self.ui.actionAuto_Mount_on_Application_Start.triggered.connect(self.action_set_automount_onstart)
        self.ui.actionAuto_Mount_on_Drive_Connect.triggered.connect(self.action_set_automount_onconnect)
        self.ui.actionDefault_Password.triggered.connect(self.action_set_default_password)
        self.ui.actionAdd_Default_Keyfile.triggered.connect(self.action_add_default_keyfile)
        self.ui.actionAbout.triggered.connect(functools.partial(About_Dialog, parent=self))
        
        self.create_sys_tray()
        if not self.start_minimized:
            self.show()
        
        self.thread1 = GenericThread(self.device_plugging_watcher_thread)
        self.thread1_signal.connect(self.search_new_drive)
        self.thread1.start()
        
        self.thread2 = GenericThread(self.logical_drive_watcher_thread)
        self.thread2_signal.connect(self.treeview_update_drives)
        self.thread2.start()
        
    # Events
    def closeEvent(self, event):
        event.ignore()
        self.hide()
            
    def hideEvent(self, event):
        self.sysTrayMenuActions["Hide"].setVisible(False)
        self.sysTrayMenuActions["Show"].setVisible(True)
        event.accept()
        
    def showEvent(self, event):
        self.sysTrayMenuActions["Hide"].setVisible(True)
        self.sysTrayMenuActions["Show"].setVisible(False)
        event.accept()
    
    # Threads
    def device_plugging_watcher_thread(self):
        pythoncom.CoInitialize()  # @UndefinedVariable
        interface = wmi.WMI()
        watcher = interface.Win32_DeviceChangeEvent.watch_for()
        event_occured = False
        while True:
            try:
                event = watcher(1000).EventType # Timeout 1000ms
                if event == 2 or event == 3: # Device Arrival (2) or Device Unplugged (3)
                    event_occured = True
            except wmi.x_wmi_timed_out:
                if event_occured:
                    event_occured = False
                    self.thread1_signal.emit()
                
    def logical_drive_watcher_thread(self):
        pythoncom.CoInitialize()  # @UndefinedVariable
        w32_logicaldrives = win32api.GetLogicalDriveStrings()
        while True:
            time.sleep(1)
            new_call = win32api.GetLogicalDriveStrings()
            if w32_logicaldrives != new_call:
                w32_logicaldrives = new_call
                self.thread2_signal.emit()
            
    # OS interaction and helpers
    def format_serial_number(self, serial_number):
        try:
            sn_str = bytes.fromhex(serial_number).decode('ascii')
            if any([ord(c) < 32 for c in sn_str]):
                return serial_number
        except UnicodeDecodeError:
            return serial_number
        except ValueError:
            return serial_number
        c = ""
        for n in range(0, len(sn_str), 2):
            c += sn_str[n+1]
            c += sn_str[n]
        return c.strip()
        
    def get_physical_drives(self):
        w32_drives = self.interface.Win32_DiskDrive()
        w32_partitions = self.interface.Win32_DiskPartition()
        w32_volumes = self.interface.Win32_Volume()
        drive_dict = {}
        
        for medium in w32_drives:
            if 'PHYSICALDRIVE' in medium.DeviceID:
                if not medium.SerialNumber:
                    continue
                drive_sn = self.format_serial_number(medium.SerialNumber.strip())
                drive_id = "".join((medium.DeviceID.replace('\\\\.\\PHYSICALDRIVE', '\\Device\\Harddisk'), '\\Partition0'))
                drive_name = medium.Caption
                drive_size = medium.Size
                drive_dict[drive_id] = {"SerialNumber":drive_sn, "Caption":drive_name, "Size":drive_size}
                
        for medium in w32_partitions:
            drive_id = "\\Device\\Harddisk%s\\Partition%s" % (medium.DiskIndex, medium.Index + 1)
            drive_sn = drive_dict["\\Device\\Harddisk%s\\Partition0" % medium.DiskIndex]["SerialNumber"] + "#%s" % (medium.Index + 1)
            drive_name = drive_dict["\\Device\\Harddisk%s\\Partition0" % medium.DiskIndex]["Caption"]
            drive_size = medium.Size
            drive_dict[drive_id] = {"SerialNumber":drive_sn, "Caption":drive_name, "Size":drive_size}
                
        for volume in w32_volumes:
            if volume.DriveType == 3 and not volume.FileSystem:
                volume_name = volume.DeviceID
                device_name = win32file.QueryDosDevice(volume_name.replace("\\","").replace("?","")).strip("\x00")
                drive_dict[device_name] = {"SerialNumber":volume_name, "Caption":"Unidentified Harddisk Volume", "Size":0}
        
        return drive_dict
    
    def update_drive_size(self, drive_letter):
        w32_logicaldisk = self.interface.Win32_LogicalDisk()
        for disk in w32_logicaldisk:
            print(disk.DeviceID.lower(), drive_letter.lower())
            if disk.DeviceID.lower() == drive_letter.lower():
                print(self.settings[drive_letter]["Size"])
                if self.settings[drive_letter]["Size"] == "0 GiB":
                    drive_size = "%s GiB" % int(int(disk.Size)/1024**3)
                    self.settings[drive_letter]["Size"] =  drive_size
                    self.save_settings()
        
    def get_logical_drives(self, w32_logicaldrives=None):
        if not w32_logicaldrives:
            w32_logicaldrives = self.interface.Win32_LogicalDisk()
        return [drive.DeviceID for drive in w32_logicaldrives]

    def get_logical_drive_info(self, path, w32_logicaldrives=None):
        drive_dict = {0:"Unknown", 1:"No Root Directory", 2:"Removable Disk", 3:"Local Disk", 4:"Network Drive", 5:"Compact Disc", 6:"RAM Disk"}
        if not w32_logicaldrives:
            w32_logicaldrives = interface.Win32_LogicalDisk()
        for drive in w32_logicaldrives:
            if drive.DeviceID == path:
                return {"VolumenName":drive.VolumeName, "FileSystem":drive.FileSystem, "DriveType":drive_dict[drive.DriveType]}

    def search_new_drive(self):
        old_drive_keys = set(self.drive_dict.keys())
        drive_letters = self.get_logical_drives()
        self.drive_dict = self.get_physical_drives()
        new_drive_keys = set(self.drive_dict.keys())
        if self.automount_onconnect:
            for drive in new_drive_keys.difference(old_drive_keys):
                for drive_letter in self.settings:
                    if drive_letter in drive_letters:
                        continue
                    if self.drive_dict[drive]["SerialNumber"] == self.settings[drive_letter]["SerialNumber"]:
                        self.mount_drive(self.tc_path, drive, drive_letter, self.keyfiles, self.password)
        self.combo_update_physical_drives()
                
    def generate_autostart_string(self):
        if sys.argv[0].endswith('.exe'):
            return sys.argv[0]
        else:
            for path in sys.path:
                test_path = os.path.join(path, "pythonw.exe")
                if os.path.isfile(test_path):
                    return "\"%s\" \"%s\"" % (test_path, sys.argv[0])
                
    def get_autostart_regkey(self):
        try:
            aReg = winreg.ConnectRegistry(None,winreg.HKEY_CURRENT_USER)
            aKey = winreg.OpenKey(aReg, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run", winreg.REG_SZ, winreg.KEY_ALL_ACCESS)
            if winreg.QueryValueEx(aKey, "TrueCrypt Auto-Mounter")[0] == self.generate_autostart_string():
                return True
            else:
                winreg.DeleteValue(aKey, "TrueCrypt Auto-Mounter")
                return False
        except WindowsError:
            return False
        finally:
            winreg.CloseKey(aKey)
            winreg.CloseKey(aReg)
            
    def set_autostart_regkey(self, delete=False):
        try:
            aReg = winreg.ConnectRegistry(None,winreg.HKEY_CURRENT_USER)
            aKey = winreg.OpenKey(aReg, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run", winreg.REG_SZ, winreg.KEY_ALL_ACCESS)
            if delete:
                winreg.DeleteValue(aKey, "TrueCrypt Auto-Mounter")
            else:
                winreg.SetValueEx(aKey, "TrueCrypt Auto-Mounter", 0, winreg.REG_SZ, self.generate_autostart_string())
                return winreg.QueryValueEx(aKey, "TrueCrypt Auto-Mounter")[0] == self.generate_autostart_string()
        finally:
            winreg.CloseKey(aKey)
            winreg.CloseKey(aReg)
                
    # Serialization
    def load_settings(self, event=None):
        #.\settings.xml
        if not os.path.isfile('settings.xml'):
            return
        dom = xml.dom.minidom.parse('settings.xml')
        drives = dom.getElementsByTagName('Settings')[0].getElementsByTagName('Drive')
        for drive in drives:
            postmountbatch = [command.strip() for command in drive.getAttribute("PostMountBatch").split("&")]
            if "" in postmountbatch:
                postmountbatch.remove("")
            self.settings[drive.getAttribute("Letter")] = {
                                    "Name":drive.getAttribute("Name"),
                                    "SerialNumber":drive.getAttribute("SerialNumber"),
                                    "Size":drive.getAttribute("Size"),
                                    "PostMountBatch":postmountbatch
                                    }
        elements = dom.getElementsByTagName('Settings')[0].getElementsByTagName('Path')
        for element in elements:
            if element.hasAttribute("TrueCrypt"):
                self.tc_path = element.getAttribute("TrueCrypt")
            if element.hasAttribute("Keyfile"):
                self.keyfiles.append(element.getAttribute("Keyfile"))
        elements = dom.getElementsByTagName('Settings')[0].getElementsByTagName('Mount')
        for element in elements:
            if element.hasAttribute("OnStart"):
                self.automount_onstart = True if element.getAttribute("OnStart") == "yes" else False
            if element.hasAttribute("OnConnect"):
                self.automount_onconnect = True if element.getAttribute("OnConnect") == "yes" else False
        elements = dom.getElementsByTagName('Settings')[0].getElementsByTagName('Start')
        for element in elements:
            if element.hasAttribute("Minimized"):
                self.start_minimized = True if element.getAttribute("Minimized") == "yes" else False
        elements = dom.getElementsByTagName('Settings')[0].getElementsByTagName('Password')
        for element in elements:
            self.password = element.getAttribute("String") if element.getAttribute("Active") == "yes" else None

    def save_settings(self, event=None):
        #.\settings.xml
        dom = xml.dom.minidom.Document()
        settings = dom.createElement("Settings")
        settings_item = dom.createElement("Path")
        settings_item.setAttribute("TrueCrypt", self.tc_path)
        settings.appendChild(settings_item)
        settings_item = dom.createElement("Start")
        settings_item.setAttribute("Minimized", "yes" if self.start_minimized else "no")
        settings.appendChild(settings_item)
        settings_item = dom.createElement("Mount")
        settings_item.setAttribute("OnStart", "yes" if self.automount_onstart else "no")
        settings.appendChild(settings_item)
        settings_item = dom.createElement("Mount")
        settings_item.setAttribute("OnConnect", "yes" if self.automount_onconnect else "no")
        settings.appendChild(settings_item)
        settings_item = dom.createElement("Password")
        settings_item.setAttribute("Active", "yes" if self.password != None else "no")
        settings_item.setAttribute("String", self.password if self.password != None else "")
        settings.appendChild(settings_item)
        for keyfile in self.keyfiles:
            settings_item = dom.createElement("Path")
            settings_item.setAttribute("Keyfile", keyfile)
            settings.appendChild(settings_item)
        for drive in self.settings:
            if not self.settings[drive]["SerialNumber"]:
                continue
            settings_item = dom.createElement("Drive")
            settings_item.setAttribute("Letter", drive)
            settings_item.setAttribute("SerialNumber", self.settings[drive]["SerialNumber"])
            settings_item.setAttribute("Name", self.settings[drive]["Name"])
            settings_item.setAttribute("Size", self.settings[drive]["Size"])
            settings_item.setAttribute("PostMountBatch", " & ".join(self.settings[drive]["PostMountBatch"]))
            settings.appendChild(settings_item)
        dom.appendChild(settings)
        with open("settings.xml", "wb") as f:
            f.write(dom.toprettyxml(encoding="utf-8"))
        
    # Menu
    def action_set_tc_path(self, checked):
        if checked:
            self.tc_path, _ = QtWidgets.QFileDialog.getOpenFileName(parent=self, caption='Select TrueCrypt.exe', filter='TrueCrypt.exe')
            if os.path.basename(self.tc_path).lower() != "TrueCrypt.exe".lower():
                self.ui.actionPath_to_TrueCrypt.setChecked(False)
                self.tc_path = ""
        else:
            self.tc_path = ""
        self.save_settings()
            
    def action_add_default_keyfile(self):
        keyfile, _ = QtWidgets.QFileDialog.getOpenFileName(parent=self, caption='Select a TrueCrypt keyfile')
        if keyfile:
            self.keyfiles.append(keyfile)
            action = QtWidgets.QAction(keyfile, self.ui.menuSettings)
            self.ui.menuSettings.addAction(action)
            action.triggered.connect(self.action_del_default_keyfile)
            self.save_settings()
            
    def action_del_default_keyfile(self):
        action = self.sender()
        self.keyfiles.remove(action.text())
        self.ui.menuSettings.removeAction(action)
        self.save_settings()
            
    def action_set_autostart(self, checked):
        if checked:
            if not self.set_autostart_regkey():
                self.ui.actionStart_with_Windows.setChecked(False)
        else:
            self.set_autostart_regkey(delete=True)
            
    def action_set_start_minimized(self, checked):
        self.start_minimized = checked
        if checked:
            print("Start minimized on")
        else:
            print("Start minimized off")
        self.save_settings()
            
    def action_set_automount_onstart(self, checked):
        self.automount_onstart = checked
        if checked:
            print("Automount on start on")
        else:
            print("Automount on start off")
        self.save_settings()
            
    def action_set_automount_onconnect(self, checked):
        self.automount_onconnect = checked
        if checked:
            print("Automount on connect on")
        else:
            print("Automount on connect off")
        self.save_settings()
        
    def action_set_default_password(self, checked):
        if checked:
            text, ok = QtWidgets.QInputDialog.getText(self, 'Set a default password', 'Warning! Password is safed as plain text! (Empty passwords work)')
            if ok:
                self.password = text
            else:
                self.ui.actionDefault_Password.setChecked(False)
        else:
            self.password = None
        self.save_settings()
    
    def actions_load_default_keyfiles(self):
        for keyfile in self.keyfiles:
            self.action_load_default_keyfile(keyfile)
            
    def action_load_default_keyfile(self, keyfile):
        if keyfile:
            action = QtWidgets.QAction(keyfile, self.ui.menuSettings)
            self.ui.menuSettings.addAction(action)
            action.triggered.connect(self.action_del_default_keyfile)
    
    def actions_set_checked(self):
        # Path to TrueCrypt
        if os.path.basename(self.tc_path).lower() == "TrueCrypt.exe".lower() and os.path.exists(self.tc_path):
            self.ui.actionPath_to_TrueCrypt.setChecked(True)
        else:
            self.tc_patch = ""
            self.ui.actionPath_to_TrueCrypt.setChecked(False)
        # Start with Windows
        if self.get_autostart_regkey():
            self.ui.actionStart_with_Windows.setChecked(True)
        else:
            self.ui.actionStart_with_Windows.setChecked(False)
        # Start minimized
        if self.start_minimized:
            self.ui.actionStart_Minimized.setChecked(True)
        else:
            self.ui.actionStart_Minimized.setChecked(False)
        # Mount on Application Start
        if self.automount_onstart:
            self.ui.actionAuto_Mount_on_Application_Start.setChecked(True)
        else:
            self.ui.actionAuto_Mount_on_Application_Start.setChecked(False)
        # Mount on Drive Connect
        if self.automount_onconnect:
            self.ui.actionAuto_Mount_on_Drive_Connect.setChecked(True)
        else:
            self.ui.actionAuto_Mount_on_Drive_Connect.setChecked(False)
        # Default Password
        if self.password != None:
            self.ui.actionDefault_Password.setChecked(True)
        else:
            self.ui.actionDefault_Password.setChecked(False)
    
    # Treeview
    def treeview_update_drives(self, w32_logicaldrives=None):
        if not w32_logicaldrives:
            w32_logicaldrives = self.interface.Win32_LogicalDisk()
        logical_drives = self.get_logical_drives(w32_logicaldrives)
        item_count = self.ui.treeVolumeList.topLevelItemCount()
        for item_index in range(item_count):
            row = self.ui.treeVolumeList.topLevelItem(item_index)
            row.setIcon(0, self.icons["drive_add"])
            row.setText(1, "")
            row.setText(2, "")
            drive = row.text(0)
            if drive in logical_drives:
                drive_info = self.get_logical_drive_info(drive, w32_logicaldrives)
                if drive_info["DriveType"] == "Local Disk":
                    row.setIcon(0, self.icons["drive"])
                elif drive_info["DriveType"] == "Compact Disc":
                    row.setIcon(0, self.icons["drive_cd"])
                elif drive_info["DriveType"] == "Network Drive":
                    row.setIcon(0, self.icons["drive_network"])    
                elif drive_info["DriveType"] == "Removable Disk":
                    row.setIcon(0, self.icons["drive_flash"])
                row.setText(1, drive_info["VolumenName"])
                row.setText(2, drive_info["FileSystem"])
            if drive in self.settings:
                row.setText(4, self.settings[drive]["Name"])
                row.setText(5, self.settings[drive]["Size"])
                row.setText(6, self.settings[drive]["SerialNumber"])
                if self.settings[drive]["PostMountBatch"]:
                    row.setIcon(7, self.icons["application_double"])
                else:
                    row.setIcon(7, self.icons["blank"])
            self.treeview_set_status_icon(row)
            
    def treeview_add_new_drive(self, c, logical_drives, w32_logicaldrives=None):
        row = QtWidgets.QTreeWidgetItem()
        row.setIcon(0, self.icons["drive"])
        row.setText(0, '%s:' % c)
        return row
        
    def treeview_set_status_icon(self, row):
        row.setIcon(3, self.icons["blank"])
        serial_number = row.text(6)
        serial_numbers = [self.drive_dict[drive]["SerialNumber"] for drive in self.drive_dict]
        if serial_number:
            if serial_number in serial_numbers:
                if row.icon(0).cacheKey() == self.icons["drive_add"].cacheKey():
                    row.setIcon(3, self.icons["drive_go"])
                else:
                    row.setIcon(3, self.icons["drive_link"])
            else:
                row.setIcon(3, self.icons["drive_error"])
    
    def treeview_selectionchanged_event(self):
        tree_item = self.ui.treeVolumeList.selectedItems()[0]
        self.enable_buttons(tree_item)
        self.statusbar_show_drive_info(tree_item)

    # Buttons
    def enable_buttons(self, row):
        serial_number = row.text(6)
        mounted_icon = row.icon(3)
        # Assign Button
        self.ui.buttonAssign.setEnabled(True)
        # Mount Button
        if serial_number and mounted_icon.cacheKey() == self.icons["drive_go"].cacheKey():
            self.ui.buttonMount.setEnabled(True)
        else:
            self.ui.buttonMount.setEnabled(False)
        # Dismount Button
        if serial_number and mounted_icon.cacheKey() == self.icons["drive_link"].cacheKey():
            self.ui.buttonDismount.setEnabled(True)
        else:
            self.ui.buttonDismount.setEnabled(False)
        # Unassign Button
        if serial_number:
            self.ui.buttonUnassign.setEnabled(True)
        else:
            self.ui.buttonUnassign.setEnabled(False)
        # Post-Mount Batch Button
        if serial_number:
            self.ui.buttonPostMountBatch.setEnabled(True)
        else:
            self.ui.buttonPostMountBatch.setEnabled(False)
    
    def button_assign_click_event(self):
        drive_id = self.ui.comboVolumes.currentText().split()[0]
        serial_number = self.drive_dict[drive_id]["SerialNumber"]
        drive_name = self.drive_dict[drive_id]["Caption"]
        drive_size = "%s GiB" % int(int(self.drive_dict[drive_id]["Size"])/1024**3)
        for tree_item in self.ui.treeVolumeList.findItems(serial_number, QtCore.Qt.MatchExactly, 6):
            tree_item.setIcon(3, self.icons["blank"])
            tree_item.setText(4, "")
            tree_item.setText(5, "")
            tree_item.setText(6, "")
            self.settings[tree_item.text(0)] = {'SerialNumber': '', 'Name': '', 'Size': '', 'PostMountBatch': ''}
        tree_item = self.ui.treeVolumeList.currentItem()
        tree_item.setText(4, drive_name)
        tree_item.setText(5, drive_size)
        tree_item.setText(6, serial_number)
        self.settings[tree_item.text(0)] = {'SerialNumber': serial_number, 'Name': drive_name, 'Size': drive_size, 'PostMountBatch': ''}
        self.treeview_set_status_icon(tree_item)
        self.enable_buttons(tree_item)
        self.save_settings()
        
    def button_unassign_click_event(self):
        tree_item = self.ui.treeVolumeList.currentItem()
        self.settings[tree_item.text(0)] = {'SerialNumber': '', 'Name': '', 'Size': '', 'PostMountBatch': ''}
        tree_item.setText(4, "")
        tree_item.setText(5, "")
        tree_item.setText(6, "")
        tree_item.setIcon(7, self.icons["blank"])
        self.treeview_set_status_icon(tree_item)
        self.enable_buttons(tree_item)
        self.save_settings()
        
    def button_mount_click_event(self):
        self.drive_dict = self.get_physical_drives()
        tree_item = self.ui.treeVolumeList.currentItem()
        serial_number = tree_item.text(6)
        drive_letter = tree_item.text(0)
        for drive in self.drive_dict.keys():
            if self.drive_dict[drive]["SerialNumber"] == serial_number:
                self.mount_drive(self.tc_path, drive, drive_letter, self.keyfiles, self.password)
                self.ui.buttonMount.setEnabled(False)
                self.ui.buttonDismount.setEnabled(True)
                
    def button_mount_all_click_event(self):
        self.drive_dict = self.get_physical_drives()
        item_count = self.ui.treeVolumeList.topLevelItemCount()
        for item_index in range(item_count):
            tree_item = self.ui.treeVolumeList.topLevelItem(item_index)
            if tree_item.icon(3).cacheKey() == self.icons["drive_go"].cacheKey():
                serial_number = tree_item.text(6)
                drive_letter = tree_item.text(0)
                for drive in self.drive_dict.keys():
                    if self.drive_dict[drive]["SerialNumber"] == serial_number:
                        self.mount_drive(self.tc_path, drive, drive_letter, self.keyfiles, self.password)
                
    def button_dismount_click_event(self):
        tree_item = self.ui.treeVolumeList.currentItem()
        drive_letter = tree_item.text(0)
        self.dismount_drive(self.tc_path, drive_letter)
        self.ui.buttonMount.setEnabled(True)
        self.ui.buttonDismount.setEnabled(False)
        
    def button_dismount_all_click_event(self):
        self.dismount_drive(self.tc_path)
        
    def button_postmountbatch_click_event(self):
        tree_item = self.ui.treeVolumeList.currentItem()
        drive_letter = tree_item.text(0)
        old_commands = []
        if drive_letter in self.settings and "PostMountBatch" in self.settings[drive_letter]:
            old_commands = self.settings[drive_letter]["PostMountBatch"]
        batch_dialog = BatchCommands_Dialog(self, old_commands)
        ok, command_list = batch_dialog.getCommandList()
        if ok:
            self.settings[drive_letter]["PostMountBatch"] = command_list
            if command_list:
                tree_item.setIcon(7, self.icons["application_double"])
            else:
                tree_item.setIcon(7, self.icons["blank"])
            self.save_settings()
    
    # TrueCrypt interaction
    def mount_drive(self, tc_path, volume, drive_letter, keyfiles=[], password=None):
        switches = []
        switches.append('/v %s' % volume)            # Device (e.g. \Device\Harddisk2\Partition0)
        switches.append('/l %s' % drive_letter)        # Drive Letter (e.g. X:)
        for keyfile in keyfiles:
            switches.append('/k %s' % keyfile)        # Keyfile (e.g. C:\Temp\key)
        if password != None:
            switches.append('/p \"%s\"' % password)    # Password (empty string is allowed)
        switches.append('/q')
        subprocess.call('%s %s' % (tc_path, " ".join(switches)), shell=True)
        self.update_drive_size(drive_letter)
        if drive_letter in self.settings and "PostMountBatch" in self.settings[drive_letter]:
            if self.settings[drive_letter]["PostMountBatch"]:
                for command in self.settings[drive_letter]["PostMountBatch"]:
                    subprocess.Popen(command)
        
    def dismount_drive(self, tc_path, drive_letter=None):
        if not drive_letter:
            subprocess.call('%s /d /q' % self.tc_path, shell=True)
        if drive_letter in self.get_logical_drives():
            subprocess.call('%s /d %s /q' % (self.tc_path, drive_letter), shell=True)
        
    # ComboBox
    def combo_drives_activated_event(self, value):
        value = value.split()[0]
        labeltext = "%s\n%s\n%s GiB\n%s" % (value, self.drive_dict[value]["Caption"], int(int(self.drive_dict[value]["Size"])/1024**3), self.drive_dict[value]["SerialNumber"])
        self.ui.labelDeviceInfos.setText(labeltext)
        
    def combo_update_physical_drives(self):
        drives = list(self.drive_dict.keys())
        drives.sort()
        self.ui.comboVolumes.clear()
        for drive in drives:
            self.ui.comboVolumes.addItem("%s (%s GB)" % (drive, int(int(self.drive_dict[drive]["Size"])/1024**3)))
        self.combo_drives_activated_event(drives[0])
        item_count = self.ui.treeVolumeList.topLevelItemCount()
        for item_index in range(item_count):
            row = self.ui.treeVolumeList.topLevelItem(item_index)
            self.treeview_set_status_icon(row)
    
    # Systray
    def create_sys_tray(self):
        self.sysTray = QtWidgets.QSystemTrayIcon(self)
        self.sysTray.setIcon(self.icons["logo"])
        self.sysTray.setVisible(True)
        self.sysTray.activated.connect(self.on_sys_tray_activated)

        self.sysTrayMenu = QtWidgets.QMenu(self)
        self.sysTrayMenuActions["Hide"] = self.sysTrayMenu.addAction("Hide")
        self.sysTrayMenuActions["Hide"].triggered.connect(self.hide)
        self.sysTrayMenuActions["Show"] = self.sysTrayMenu.addAction("Show")
        self.sysTrayMenuActions["Show"].triggered.connect(self.show)
        self.sysTrayMenuActions["Exit"] = self.sysTrayMenu.addAction("Exit")
        self.sysTrayMenuActions["Exit"].triggered.connect(app.quit)
        self.sysTray.setContextMenu(self.sysTrayMenu)
        if not self.isVisible():
            self.sysTrayMenuActions["Hide"].setVisible(False)
        
    def on_sys_tray_activated(self, reason):
        if reason == QtWidgets.QSystemTrayIcon.DoubleClick:
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.activateWindow()
        
    # Statusbar
    def statusbar_show_drive_info(self, tree_item):
        drive_letter = tree_item.text(0)
        drive_name = tree_item.text(4)
        drive_size = tree_item.text(5)
        if tree_item.icon(3).cacheKey() == self.icons["drive_go"].cacheKey():
            self.ui.statusbar.showMessage("Drive %s can be assigned to %s (%s)" % (drive_letter, drive_name, drive_size))
        elif tree_item.icon(3).cacheKey() == self.icons["drive_link"].cacheKey():
            self.ui.statusbar.showMessage("Drive %s is assigend to %s (%s)" % (drive_letter, drive_name, drive_size))
        elif tree_item.icon(3).cacheKey() == self.icons["drive_error"].cacheKey():
            self.ui.statusbar.showMessage("Drive %s currently can't be assigend to %s (%s)" % (drive_letter, drive_name, drive_size))
        elif tree_item.icon(0).cacheKey() == self.icons["drive_add"].cacheKey():
            self.ui.statusbar.showMessage("Drive %s currently isn't assigend" % drive_letter)
        else:
            self.ui.statusbar.showMessage("Drive %s is a system drive" % drive_letter)
                
def on_close(win):
    win.save_settings()
    win.sysTray.setVisible(False)
    print("Goodbye")
        
    
if __name__ == "__main__":
    if getattr(sys, 'frozen', False):
        # The application is frozen
        os.chdir(os.path.dirname(os.path.abspath(sys.executable)))
    else:
        # The application is not frozen
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
    interface = wmi.WMI()
    app = QtWidgets.QApplication(sys.argv)
    win = TrueCrypt_AutoMounter(interface)
    #win.show()
    app.aboutToQuit.connect(functools.partial(on_close, win=win))
    sys.exit(app.exec_())