# # make App
# pip install pyinstaller
# pip install pillow
# pip install tkinterdnd2
# pyinstaller main.py --name midi2ubit --onefile --noconsole --collect-data tkinterdnd2 --collect-data chardet --add-data="./resources/*;./resources" --icon="./resources/icon.ico"  # for windows
# pyinstaller main.py --name midi2ubit --onefile --noconsole --collect-data tkinterdnd2 --collect-data chardet --add-data="./resources/*:./resources" --icon="./resources/icon.icns" # for mac
# [!] If you get a "No module named ..." error at runtime, reinstall pyinstaller and the target module.


from tkinter import *
from tkinterdnd2 import *
import datetime

import utility63rabbits as util
import read_midi as rmidi
import notes2ubit as ubit


# JST = datetime.timezone(datetime.timedelta(hours=9), 'JST')
DEFALUT_TEMPO = 480
DEFAULT_LOW_BEAT = 4


def put_message(message, op='APPEND'):
    op = op.upper()
    textbox.config(state=NORMAL)
    if op == 'APPEND':
        textbox.insert(END, message)
        textbox.see(END)
    elif op == 'CLEAR':
        textbox.delete("1.0", END)
    textbox.config(state=DISABLED)


def dnd_handler(event):
    file_list = util.DND.make_file_list(event.data)
    for target_file in file_list:
        midi_info = rmidi.get_data(target_file)
        if rmidi.MIDI_ERROR in midi_info:
            put_message(f'\n{midi_info[rmidi.MIDI_FILE]} ### ERROR : {midi_info[rmidi.MIDI_ERROR]}\n')
            continue

        put_message('\n')
        for key in midi_info:
            put_message(f'{key} = {midi_info[key]}\n')

        tempo = DEFALUT_TEMPO
        lowbeat = DEFAULT_LOW_BEAT
        for index in range(midi_info[rmidi.MIDI_HEADER_NUMBER_OF_TRACKS]):

            # now = datetime.datetime.now(UBIT_JST)
            track_name = midi_info[f'TRACK-{index} {rmidi.MIDI_META_TRACK_NAME}']
            now = datetime.datetime.now(datetime.timezone.utc)
            comments = f'// [ uBit instructions ] TRACK-{index} = {track_name} : created on {now}.\n'

            key = f'TRACK-{index} {rmidi.MIDI_META_TEMPO}'
            if key in midi_info:
                tempo = midi_info[key]

            key = f'TRACK-{index} {rmidi.MIDI_META_BEAT}'
            if key in midi_info:
                lowbeat = 2 ** midi_info[key][1]    # denominator of the time signature

            notes = ubit.to_ubit(
                notes=midi_info[f'TRACK-{index} {rmidi.MIDI_EVENTS}'],
                ubitfile=midi_info['file'] + '.txt',
                comments=comments,
                timebase=midi_info[rmidi.MIDI_HEADER_TIME_BASE],
                tempo=tempo,
                beatdenom=lowbeat
            )
            if notes[0] >= 0:
                put_message(f'TRACK-{index} {notes[1]}\n')
            else:
                put_message(f'### ERROR : {notes[1]}\n')
                break


# Const
WINDOW_WIDTH = 500
WINDOW_HEIGHT = 200

# Main Window
root = TkinterDnD.Tk()
root.title('midi2ubit - Convert MIDI file to micro:bit')
# root.geometry(f'{win_width}x{win_height}+500+100')
root.geometry(util.WIN.get_pos_string_on_screen(root, WINDOW_WIDTH, WINDOW_HEIGHT, 'n', 0, 50)[0])
# root.minsize(width=50, height=50)
# root.config(bg='#cccccc')
if util.PLTFORM.is_windows():
    root.iconbitmap(default=util.RSC.get_resource_path('resources\\icon.ico'))

# Drag-and-Drop
root.drop_target_register(DND_FILES)
root.dnd_bind('<<Drop>>', dnd_handler)

# Widgets
frame = Frame(root)

textbox = Text(frame, width=30, height=10)
textbox.config(state=DISABLED, wrap=NONE)
put_message('Drag and Drop files here.\n\n')

scroll_y = Scrollbar(frame, orient=VERTICAL, command=textbox.yview)
scroll_x = Scrollbar(frame, orient=HORIZONTAL, command=textbox.xview)

textbox.configure(yscrollcommand=scroll_y.set)
textbox.configure(xscrollcommand=scroll_x.set)

# Arrangement
frame.pack(fill=BOTH, expand=TRUE)
scroll_y.pack(side=RIGHT, fill=Y)
scroll_x.pack(side=BOTTOM, fill=X)
textbox.pack(fill=BOTH, expand=TRUE)

root.mainloop()
