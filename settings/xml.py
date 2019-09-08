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
import ast
import xml.etree.ElementTree as ET

from collections import defaultdict

from .setting import Setting
from .drives import Drives


class SettingsXML(object):
    '''
    Settings to XML serializer/deserializer.
    '''

    def __init__(self, xml_path="settings.xml"):
        super().__setattr__("_settings", {})
        super().__setattr__("Drives", Drives())
        super().__setattr__("Keyfiles", [])
        super().__setattr__("_xml_path", xml_path)

    def __getattr__(self, name):
        if name not in self._settings:
            self._settings[name] = Setting()
        return self._settings[name]

    def __setattr__(self, name, value):
        self._settings[name] = value

    @staticmethod
    def _type_to_string(arg) -> str:
        if arg is True:
            return "True"
        if arg is False:
            return "False"
        return str(arg)

    @staticmethod
    def _string_to_type(arg: str):
        if arg.lower() in ("true", "1", "yes", "on"):
            return True
        if arg.lower() in ("false", "0", "no", "off"):
            return False
        try:
            return ast.literal_eval(arg)
        except SyntaxError:
            return arg
        except ValueError:
            return arg

    @staticmethod
    def _swap_dict_values(in_dict: dict, swap_fct: callable):
        for key, value in in_dict.items():
            in_dict[key] = swap_fct(value)
        return in_dict

    @staticmethod
    def _convert_batch_str_to_list(attribs: dict):
        if "PostMountBatch" in attribs:
            if not attribs["PostMountBatch"]:
                attribs["PostMountBatch"] = []
            else:
                attribs["PostMountBatch"] = [command.strip() for command in attribs["PostMountBatch"].split("&")]
        return attribs

    @staticmethod
    def _convert_batch_list_to_str(attribs: dict):
        output = {}
        output.update(attribs)  # Make copy so to not change active settings on save
        if "PostMountBatch" in output and isinstance(output["PostMountBatch"], list):
            output["PostMountBatch"] = " & ".join(output["PostMountBatch"])
        return output

    def _indent(self, elem, level=0, indentation=4):
        tail = "\n" + level * indentation * " "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = tail + indentation * " "
            if not elem.tail or not elem.tail.strip():
                elem.tail = tail
            for elem in elem:
                self._indent(elem, level+1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = tail
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = tail

    def load(self):
        if not os.path.isfile(self._xml_path):
            return
        tree = ET.parse(self._xml_path)
        root = tree.getroot()
        settings = defaultdict(dict)
        for setting in root.find("Drives"):
            attribs = self._swap_dict_values(setting.attrib, self._string_to_type)
            self.Drives.append(Setting(self._convert_batch_str_to_list(attribs)))
        for setting in root.find("Keyfiles"):
            self.Keyfiles.append(setting.text)
        for setting in root.find("Settings"):
            attribs = self._swap_dict_values(setting.attrib, self._string_to_type)
            settings[setting.tag].update(attribs)
        for setting in settings:
            self._settings[setting] = Setting(settings[setting])

    def save(self):
        root = ET.Element("TrueCryptAutoMount")
        settings = ET.SubElement(root, "Settings")
        for tag in self._settings:
            setting = ET.SubElement(settings, tag)
            attribs = self._swap_dict_values(self._settings[tag], self._type_to_string)
            setting.attrib = attribs
        keyfiles = ET.SubElement(root, "Keyfiles")
        for text in self.Keyfiles:
            keyfile = ET.SubElement(keyfiles, "Keyfile")
            keyfile.text = text
        drives = ET.SubElement(root, "Drives")
        for attribs in sorted(self.Drives, key=lambda drive: drive.Letter):
            drive = ET.SubElement(drives, "Drive")
            attribs = self._convert_batch_list_to_str(attribs)
            attribs = self._swap_dict_values(attribs, self._type_to_string)
            drive.attrib = attribs
        tree = ET.ElementTree(element=root)
        self._indent(root)
        tree.write(self._xml_path, encoding="utf-8", xml_declaration=True)
