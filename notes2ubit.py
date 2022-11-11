# import os.path
from collections import deque
import read_midi as rmidi


UBIT_NOTES = "c#d#ef#g#a#b"
UBIT_RESOLUTION_MAG = 8         # resolution magnification
UBIT_INSTRUCTION_PREFIX = 'sound = nerds.stringToNoteArray("'
UBIT_INSTRUCTION_SUFFIX = '")\nnerds.playNoteArray(sound, MelodyOptions.Once)\n'


def note2code(note):
    octave = note // 12 - 1
    index = note % 12
    pitch_name = UBIT_NOTES[index]
    if pitch_name == '#':
        pitch_name = UBIT_NOTES[index - 1] + pitch_name
    return f'{pitch_name}{octave}'


def get_notecode_on_ubit(note, velocity, deltatime, timebase):
    code = ''
    if velocity > 0:
        notecode = note2code(note)
        code = f'{notecode}:{deltatime}'
    else:
        code = f'r:{deltatime}'
    return code


def to_ubit(notes, ubitfile, comments='', timebase=480, tempo=500000):

    # if os.path.exists(file):
    #     return -1, f'Output file already exists. path = {file}'

    q = deque()
    # with open(file, 'w') as ubit:
    with open(ubitfile, 'a') as ubit:

        # utf8comments = comments.decode('UTF-8', 'ignore')
        # utf8comments = comments.encode(encoding='utf-8', errors='replace')
        # if len(comments) > 0: ubit.write(utf8comments)
        if len(comments) > 0: ubit.write(comments)
        ubit.write(f'music.setTempo({60 * 1000000 / tempo * UBIT_RESOLUTION_MAG :.0f})\n')
        ubit.write(UBIT_INSTRUCTION_PREFIX)

        separator = ''
        delta_time = 0
        default_time = 0
        for element in notes:

            # delta time
            if type(element) is int:
                delta_time += element

            # event
            elif type(element) is list:
                # focus only on note-on event and note-off event
                #   element = [ event, ch, note, velocity ]

                # convert note-off to note-on(velocity=0)
                if element[0] == rmidi.MIDI_EVENT_NOTE_OFF:
                    element[0] = rmidi.MIDI_EVENT_NOTE_ON   # event
                    element[3] = 0                          # velocity

                if element[0] == rmidi.MIDI_EVENT_NOTE_ON:
                    if delta_time <= 0:
                        q.append(element)
                        continue

                    # for 1st rest
                    if len(q) <= 0:
                        code = get_notecode_on_ubit(0, 0, delta_time, timebase)

                    # convert midi-notes to ubit-notes
                    else:
                        (event, ch, note, velocity) = q.popleft()
                        delta_time = delta_time * 4 * UBIT_RESOLUTION_MAG // timebase
                        if delta_time <= 0: delta_time = default_time
                        code = get_notecode_on_ubit(note, velocity, delta_time, timebase)

                    ubit.write(separator + code)
                    delta_time = 0
                    default_time = 1
                    separator = ','

                    q.clear()
                    q.append(element)


            # unknown
            else:
                pass

        # process last note
        if len(q) > 0:
            # convert midi-notes to ubit-notes
            (event, ch, note, velocity) = q.popleft()
            delta_time = delta_time * 4 * UBIT_RESOLUTION_MAG // timebase
            if delta_time <= 0: delta_time = default_time
            code = get_notecode_on_ubit(note, velocity, delta_time, timebase)
            ubit.write(separator + code)

        ubit.write(UBIT_INSTRUCTION_SUFFIX)

        ubit.write('\n')

    return 0, f'Successfully output code for microbit. {ubitfile}'
