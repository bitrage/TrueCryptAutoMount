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

from PyQt5 import QtWidgets, uic


class BatchCommands_Dialog(QtWidgets.QDialog):
    '''
    TrueCrypt AutoMount BatchCommands Dialog
    '''
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
