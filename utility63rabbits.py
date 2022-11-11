import os
import sys
import re


# for Platform

class PLTFORM:
    @staticmethod
    def is_windows():
        if os.name == 'nt':  return True
        return False

    @staticmethod
    def is_linux():
        if os.name == 'posix':  return True
        return False

    @staticmethod
    def is_mac():
        return PLTFORM.is_linux()


# for Resource Control

class RSC:
    @staticmethod
    def get_resource_path(filename):
        if hasattr(sys, "_MEIPASS"):
            return os.path.join(sys._MEIPASS, filename)
        # return os.path.join(filename)
        return filename


# for Window

class WIN:
    @staticmethod
    def get_pos_string_on_screen(self, width, height, position='C', x_offset=0, y_offset=0):
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        xy = ((sw - width) // 2, (sh - height) // 2)
        p = position.upper()
        if p == 'NW':       xy = (0, 0)
        elif p == 'N':      xy = ((sw - width)//2, 0)
        elif p == 'NE':     xy = (sw - width, 0)
        elif p == 'W':      xy = (0, (sh - height)//2)
        elif p == 'C':      pass
        elif p == 'E':      xy = (sw - width, (sh - height)//2)
        elif p == 'SW':     xy = (0, sh - height)
        elif p == 'S':      xy = ((sw - width)//2, sh - height)
        elif p == 'SE':     xy = (sw - width, sh - height)

        xy = (xy[0]+x_offset, xy[1]+y_offset)
        r = (f'{width}x{height}+{xy[0]}+{xy[1]}', width, height, xy[0], xy[1])
        return r


# for Drag and Drop with tkinterdnd2

class DND:
    @staticmethod
    def make_file_list(dnd_files_string):
        rawfs = dnd_files_string
        bfs = re.findall('{.+?}', rawfs)
        fs = []
        for f in bfs:
            rawfs = rawfs.replace(f, '')
            fs.append(f.replace('{', '').replace('}', ''))
        fs = sorted(fs + rawfs.split())
        return fs
