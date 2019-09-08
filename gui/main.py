''' Copyright (c) 2014-2018, Felix Heide

    This file is part of TrueCrypt AutoMount.

    TrueCrypt AutoMount is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    TrueCrypt AutoMount is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with TrueCrypt AutoMount.  If not, see <http://www.gnu.org/licenses/>.
'''

import os
import sys
import wmi
import winreg
import functools
import subprocess
import images_qrc  # @UnusedImport
from PyQt5 import QtGui, QtCore, QtWidgets, uic

import gui
import threads
from drives import Drives, LogicalDiskType
from settings import Settings


class TrueCrypt_AutoMounter(QtWidgets.QMainWindow):

    thread1_signal = QtCore.pyqtSignal()
    thread2_signal = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent=parent)

        self.ui = uic.loadUi('gui.ui', self)

        icon = QtGui.QIcon()
        icon.addFile(':/window/ico16', QtCore.QSize(16, 16))
        icon.addFile(':/window/ico24', QtCore.QSize(24, 24))
        icon.addFile(':/window/ico32', QtCore.QSize(32, 32))
        icon.addFile(':/window/ico48', QtCore.QSize(48, 48))
        self.setWindowIcon(icon)

        self.interface = wmi.WMI()
        self.drives = Drives(self.interface)

        self.sysTrayMenuActions = {}

        self.load_settings()
        self.actions_set_checked()
        self.actions_load_default_keyfiles()

        if self.settings.Mount.OnStart:
            self.search_new_drive()

        self.icons = {}
        self.icons["logo"] = icon
        self.icons["blank"] = QtGui.QIcon()
        self.icons["drive"] = QtGui.QIcon(":/treeview/drive")
        self.icons["drive_add"] = QtGui.QIcon(":/treeview/drive_add")
        self.icons["drive_cd"] = QtGui.QIcon(":/treeview/drive_cd")
        self.icons["drive_link"] = QtGui.QIcon(":/treeview/drive_link")
        self.icons["drive_network"] = QtGui.QIcon(":/treeview/drive_network")
        self.icons["drive_flash"] = QtGui.QIcon(":/treeview/drive_flash")
        self.icons["drive_go"] = QtGui.QIcon(":/treeview/drive_go")
        self.icons["drive_error"] = QtGui.QIcon(":/treeview/drive_error")
        self.icons["application_double"] = QtGui.QIcon(":/treeview/application_double")
        self.icons["logo_big"] = QtGui.QPixmap(":/window/logo_big")

        self.ui.labelLogo.setPixmap(self.icons["logo_big"])

        self.ui.treeVolumeList.setColumnWidth(0, 50)  # Drive Icon + Drive Letter
        self.ui.treeVolumeList.setColumnWidth(1, 80)  # Drive Caption
        self.ui.treeVolumeList.setColumnWidth(2, 40)
        self.ui.treeVolumeList.setColumnWidth(3, 35)
        self.ui.treeVolumeList.setColumnWidth(4, 220)
        self.ui.treeVolumeList.setColumnWidth(5, 60)
        self.ui.treeVolumeList.setColumnWidth(6, 60)
        self.ui.treeVolumeList.setColumnWidth(7, 130)
        self.ui.treeVolumeList.setColumnWidth(8, 35)

        for c in "CDEFGHIJKLMNOPQRSTUVWXYZ":
            self.ui.treeVolumeList.addTopLevelItem(self.treeview_add_new_drive(c))

        self.treeview_update_drives()
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
        self.ui.buttonExit.clicked.connect(QtWidgets.QApplication.quit)
        self.ui.actionPath_to_TrueCrypt.triggered.connect(self.action_set_tc_path)
        self.ui.actionStart_with_Windows.triggered.connect(self.action_set_autostart)
        self.ui.actionStart_Minimized.triggered.connect(self.action_set_start_minimized)
        self.ui.actionAuto_Mount_on_Application_Start.triggered.connect(self.action_set_automount_onstart)
        self.ui.actionAuto_Mount_on_Drive_Connect.triggered.connect(self.action_set_automount_onconnect)
        self.ui.actionDefault_Password.triggered.connect(self.action_set_default_password)
        self.ui.actionAdd_Default_Keyfile.triggered.connect(self.action_add_default_keyfile)
        self.ui.actionAbout.triggered.connect(functools.partial(gui.About_Dialog, parent=self))

        self.create_sys_tray()
        if not self.settings.Start.Minimized:
            self.show()

        self.thread1 = threads.get_device_plugging_watcher(self.thread1_signal)
        self.thread1_signal.connect(self.search_new_drive)
        self.thread1.start()

        self.thread2 = threads.get_logical_drive_watcher(self.thread2_signal)
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

    # OS interaction and helpers
    def update_drive_size(self, drive_letter):
        logicaldisk = self.drives.get_logicaldisk_by_id(drive_letter)
        if not logicaldisk:
            return
        for drive in self.settings.Drives:
            if drive.Letter == drive_letter:
                break
        drive.SpaceFree = logicaldisk.free_str
        drive.Size = logicaldisk.size_str
        self.save_settings()

    def get_active_drive_letters(self):
        return [drive.id for drive in self.drives.logicaldisks]

    def get_active_drives(self):
        return [drive.id for drive in self.drives.drives]

    def search_new_drive(self):
        old_drive_ids = set(self.get_active_drives())
        self.drives.refresh()
        drive_letters = self.get_active_drive_letters()
        new_drive_ids = set(self.get_active_drives())
        self.combo_update_physical_drives()

        if not self.settings.Mount.OnConnect:
            return

        for drive_id in new_drive_ids.difference(old_drive_ids):
            for drive in self.settings.Drives:
                if drive.Letter in drive_letters:
                    continue
                if self.drives.get_drive_by_id(drive_id).serial == drive.SerialNumber:
                    self.mount_drive(drive_id, drive.Letter)

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
            aReg = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
            aKey = winreg.OpenKey(aReg, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
                                  winreg.REG_SZ, winreg.KEY_ALL_ACCESS)
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
            aReg = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
            aKey = winreg.OpenKey(aReg, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
                                  winreg.REG_SZ, winreg.KEY_ALL_ACCESS)
            if delete:
                winreg.DeleteValue(aKey, "TrueCrypt Auto-Mounter")
            else:
                winreg.SetValueEx(aKey, "TrueCrypt Auto-Mounter", 0, winreg.REG_SZ, self.generate_autostart_string())
                return winreg.QueryValueEx(aKey, "TrueCrypt Auto-Mounter")[0] == self.generate_autostart_string()
        finally:
            winreg.CloseKey(aKey)
            winreg.CloseKey(aReg)

    # Serialization
    def load_settings(self):
        self.settings = Settings()
        self.settings.Password.Active = False
        self.settings.Password.String = ""
        self.settings.Start.Minimized = False
        self.settings.Mount.OnConnect = False
        self.settings.Mount.OnStart = False
        self.settings.Path.TrueCrypt = ""
        self.settings.load()

    def save_settings(self):
        self.settings.save()

    # Menu
    def action_set_tc_path(self, checked):
        if checked:
            self.settings.Path.TrueCrypt, _ = QtWidgets.QFileDialog.getOpenFileName(
                parent=self, caption='Select TrueCrypt.exe', filter='TrueCrypt.exe')
            if os.path.basename(self.settings.Path.TrueCrypt).lower() != "TrueCrypt.exe".lower():
                self.ui.actionPath_to_TrueCrypt.setChecked(False)
                self.settings.Path.TrueCrypt = ""
        else:
            self.settings.Path.TrueCrypt = ""
        self.save_settings()

    def action_add_default_keyfile(self):
        keyfile, _ = QtWidgets.QFileDialog.getOpenFileName(parent=self, caption='Select a TrueCrypt keyfile')
        if keyfile:
            self.settings.Keyfiles.append(keyfile)
            action = QtWidgets.QAction(keyfile, self.ui.menuSettings)
            self.ui.menuSettings.addAction(action)
            action.triggered.connect(self.action_del_default_keyfile)
            self.save_settings()

    def action_del_default_keyfile(self):
        action = self.sender()
        self.settings.Keyfiles.remove(action.text())
        self.ui.menuSettings.removeAction(action)
        self.save_settings()

    def action_set_autostart(self, checked):
        if checked:
            if not self.set_autostart_regkey():
                self.ui.actionStart_with_Windows.setChecked(False)
        else:
            self.set_autostart_regkey(delete=True)

    def action_set_start_minimized(self, checked):
        self.settings.Start.Minimized = checked
        if checked:
            print("Start minimized on")
        else:
            print("Start minimized off")
        self.save_settings()

    def action_set_automount_onstart(self, checked):
        self.settings.Mount.OnStart = checked
        if checked:
            print("Automount on start on")
        else:
            print("Automount on start off")
        self.save_settings()

    def action_set_automount_onconnect(self, checked):
        self.settings.Mount.OnConnect = checked
        if checked:
            print("Automount on connect on")
        else:
            print("Automount on connect off")
        self.save_settings()

    def action_set_default_password(self, checked):
        if checked:
            title = 'Set a default password'
            msg = 'Warning! Password is safed as plain text! (Empty passwords work)'
            text, ok = QtWidgets.QInputDialog.getText(self, title, msg)
            if ok:
                self.settings.Password.String = text
                self.settings.Password.Active = True
            else:
                self.ui.actionDefault_Password.setChecked(False)
        else:
            self.settings.Password.Active = False
            self.settings.Password.String = ""
        self.save_settings()

    def actions_load_default_keyfiles(self):
        for keyfile in self.settings.Keyfiles:
            self.action_load_default_keyfile(keyfile)

    def action_load_default_keyfile(self, keyfile):
        if keyfile:
            action = QtWidgets.QAction(keyfile, self.ui.menuSettings)
            self.ui.menuSettings.addAction(action)
            action.triggered.connect(self.action_del_default_keyfile)

    def actions_set_checked(self):
        # Path to TrueCrypt
        if (os.path.basename(self.settings.Path.TrueCrypt).lower() == "TrueCrypt.exe".lower()
                and os.path.exists(self.settings.Path.TrueCrypt)):
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
        if self.settings.Start.Minimized:
            self.ui.actionStart_Minimized.setChecked(True)
        else:
            self.ui.actionStart_Minimized.setChecked(False)
        # Mount on Application Start
        if self.settings.Mount.OnStart:
            self.ui.actionAuto_Mount_on_Application_Start.setChecked(True)
        else:
            self.ui.actionAuto_Mount_on_Application_Start.setChecked(False)
        # Mount on Drive Connect
        if self.settings.Mount.OnConnect:
            self.ui.actionAuto_Mount_on_Drive_Connect.setChecked(True)
        else:
            self.ui.actionAuto_Mount_on_Drive_Connect.setChecked(False)
        # Default Password
        if self.settings.Password.Active:
            self.ui.actionDefault_Password.setChecked(True)
        else:
            self.ui.actionDefault_Password.setChecked(False)

    # Treeview
    def treeview_update_drives(self):
        self.drives.refresh()
        item_count = self.ui.treeVolumeList.topLevelItemCount()
        for item_index in range(item_count):
            row = self.ui.treeVolumeList.topLevelItem(item_index)
            row.setIcon(0, self.icons["drive_add"])
            row.setText(1, "")
            row.setText(2, "")
            drive_letter = row.text(0)
            logicaldisk = self.drives.get_logicaldisk_by_id(drive_letter)
            if logicaldisk:
                if logicaldisk.type == LogicalDiskType.LOCAL_DRIVE:
                    row.setIcon(0, self.icons["drive"])
                elif logicaldisk.type == LogicalDiskType.COMPACT_DISC:
                    row.setIcon(0, self.icons["drive_cd"])
                elif logicaldisk.type == LogicalDiskType.NETWORK_DRIVE:
                    row.setIcon(0, self.icons["drive_network"])
                elif logicaldisk.type == LogicalDiskType.REMOVABLE_DRIVE:
                    row.setIcon(0, self.icons["drive_flash"])
                row.setText(1, logicaldisk.caption)
                row.setText(2, logicaldisk.filesystem)
                row.setText(5, logicaldisk.size_str)
                row.setText(6, logicaldisk.free_str)
            for drive in self.settings.Drives:
                if drive.Letter != drive_letter:
                    continue
                row.setText(4, drive.Name)
                row.setText(5, drive.Size)
                if drive.SpaceFree:
                    row.setText(6, drive.SpaceFree)
                row.setText(7, drive.SerialNumber)
                if drive.PostMountBatch:
                    row.setIcon(8, self.icons["application_double"])
                else:
                    row.setIcon(8, self.icons["blank"])
            self.treeview_set_status_icon(row)

    def treeview_add_new_drive(self, c):
        row = QtWidgets.QTreeWidgetItem()
        row.setIcon(0, self.icons["drive"])
        row.setText(0, '%s:' % c)
        return row

    def treeview_set_status_icon(self, row):
        row.setIcon(3, self.icons["blank"])
        serial_number = row.text(7)
        if not serial_number:
            return
        if not self.drives.get_drive_by_serial(serial_number):
            row.setIcon(3, self.icons["drive_error"])
            return
        if row.icon(0).cacheKey() == self.icons["drive_add"].cacheKey():
            row.setIcon(3, self.icons["drive_go"])
        else:
            row.setIcon(3, self.icons["drive_link"])

    def treeview_selectionchanged_event(self):
        tree_item = self.ui.treeVolumeList.selectedItems()[0]
        self.enable_buttons(tree_item)
        self.statusbar_show_drive_info(tree_item)

    # Buttons
    def enable_buttons(self, row):
        serial_number = row.text(7)
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
        drive = self.drives.get_drive_by_id(drive_id)
        for tree_item in self.ui.treeVolumeList.findItems(drive.serial, QtCore.Qt.MatchExactly, 6):
            tree_item.setIcon(3, self.icons["blank"])
            tree_item.setText(4, "")
            tree_item.setText(5, "")
            tree_item.setText(6, "")
            self.settings.Drives.append({'Letter': tree_item.text(0), 'SerialNumber': '', 'Name': '', 'Size': '',
                                         'SpaceFree': '', 'PostMountBatch': []})
        tree_item = self.ui.treeVolumeList.currentItem()
        tree_item.setText(4, drive.caption)
        tree_item.setText(5, drive.size_str)
        tree_item.setText(7, drive.serial)
        self.settings.Drives.append({'Letter': tree_item.text(0), 'SerialNumber': drive.serial, 'Name': drive.caption,
                                     'Size': drive.size_str, 'SpaceFree': '', 'PostMountBatch': []})
        self.treeview_set_status_icon(tree_item)
        self.enable_buttons(tree_item)
        self.save_settings()

    def button_unassign_click_event(self):
        tree_item = self.ui.treeVolumeList.currentItem()
        self.settings.Drives.append({'Letter': tree_item.text(0), 'SerialNumber': '', 'Name': '', 'Size': '',
                                     'SpaceFree': '', 'PostMountBatch': []})
        tree_item.setText(4, "")
        tree_item.setText(5, "")
        tree_item.setText(6, "")
        tree_item.setText(7, "")
        tree_item.setIcon(8, self.icons["blank"])
        self.treeview_set_status_icon(tree_item)
        self.enable_buttons(tree_item)
        self.save_settings()

    def button_mount_click_event(self):
        self.drives.refresh()
        tree_item = self.ui.treeVolumeList.currentItem()
        serial_number = tree_item.text(7)
        drive_letter = tree_item.text(0)
        drive = self.drives.get_drive_by_serial(serial_number)
        if drive:
            self.mount_drive(drive.id, drive_letter)
            self.ui.buttonMount.setEnabled(False)
            self.ui.buttonDismount.setEnabled(True)

    def button_mount_all_click_event(self):
        self.drives.refresh()
        item_count = self.ui.treeVolumeList.topLevelItemCount()
        for item_index in range(item_count):
            tree_item = self.ui.treeVolumeList.topLevelItem(item_index)
            if tree_item.icon(3).cacheKey() == self.icons["drive_go"].cacheKey():
                serial_number = tree_item.text(7)
                drive_letter = tree_item.text(0)
                drive = self.drives.get_drive_by_serial(serial_number)
                self.mount_drive(drive.id, drive_letter)

    def button_dismount_click_event(self):
        tree_item = self.ui.treeVolumeList.currentItem()
        drive_letter = tree_item.text(0)
        self.dismount_drive(drive_letter)
        self.ui.buttonMount.setEnabled(True)
        self.ui.buttonDismount.setEnabled(False)

    def button_dismount_all_click_event(self):
        self.dismount_drive()

    def button_postmountbatch_click_event(self):
        tree_item = self.ui.treeVolumeList.currentItem()
        drive_letter = tree_item.text(0)
        old_commands = []
        for drive in self.settings.Drives:
            if drive.Letter == drive_letter:
                old_commands = drive.PostMountBatch
                break
        batch_dialog = gui.BatchCommands_Dialog(self, old_commands)
        ok, command_list = batch_dialog.getCommandList()
        if ok:
            drive.PostMountBatch = command_list
            if command_list:
                tree_item.setIcon(8, self.icons["application_double"])
            else:
                tree_item.setIcon(8, self.icons["blank"])
            self.save_settings()

    # TrueCrypt interaction
    def mount_drive(self, volume, drive_letter):
        switches = []
        switches.append('/v %s' % volume)  # Device (e.g. \Device\Harddisk2\Partition0)
        switches.append('/l %s' % drive_letter)  # Drive Letter (e.g. X:)
        for keyfile in self.settings.Keyfiles:
            switches.append('/k %s' % keyfile)  # Keyfile (e.g. C:\Temp\key)
        if self.settings.Password.Active:
            switches.append('/p \"%s\"' % self.settings.Password.String)  # Password (empty string is allowed)
        switches.append('/q')
        subprocess.call('%s %s' % (self.settings.Path.TrueCrypt, " ".join(switches)), shell=True)
        self.update_drive_size(drive_letter)
        for drive in self.settings.Drives:
            if drive.Letter == drive_letter:
                for command in drive.PostMountBatch:
                    subprocess.Popen(command)

    def dismount_drive(self, drive_letter=None):
        if not drive_letter:
            subprocess.call('%s /d /q' % self.settings.Path.TrueCrypt, shell=True)
        if drive_letter in self.get_active_drive_letters():
            subprocess.call('%s /d %s /q' % (self.settings.Path.TrueCrypt, drive_letter), shell=True)

    # ComboBox
    def combo_drives_activated_event(self, value):
        drive_id = value.split()[0]
        drive = self.drives.get_drive_by_id(drive_id)
        size = int(int(drive.size) / 1024 ** 3)
        labeltext = "%s\n%s\n%s GiB\n%s" % (drive_id, drive.caption, size, drive.serial)
        self.ui.labelDeviceInfos.setText(labeltext)

    def combo_update_physical_drives(self):
        self.ui.comboVolumes.clear()
        for drive in self.drives.drives:
            self.ui.comboVolumes.addItem("%s (%s)" % (drive.id, drive.size_str))
        self.combo_drives_activated_event(self.drives.drives[0].id)
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
        self.sysTrayMenuActions["Exit"].triggered.connect(QtWidgets.QApplication.quit)
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
            self.ui.statusbar.showMessage("Drive %s can be assigned to %s (%s)"
                                          % (drive_letter, drive_name, drive_size))
        elif tree_item.icon(3).cacheKey() == self.icons["drive_link"].cacheKey():
            self.ui.statusbar.showMessage("Drive %s is assigend to %s (%s)" % (drive_letter, drive_name, drive_size))
        elif tree_item.icon(3).cacheKey() == self.icons["drive_error"].cacheKey():
            self.ui.statusbar.showMessage("Drive %s currently can't be assigend to %s (%s)"
                                          % (drive_letter, drive_name, drive_size))
        elif tree_item.icon(0).cacheKey() == self.icons["drive_add"].cacheKey():
            self.ui.statusbar.showMessage("Drive %s currently isn't assigend" % drive_letter)
        else:
            self.ui.statusbar.showMessage("Drive %s is a system disk" % drive_letter)
