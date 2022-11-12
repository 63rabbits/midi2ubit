import os
# pip install chardet
from chardet import detect


MIDI_LEN = 4
MIDI_RECORD_MIN_LEN = 8
MIDI_HEAD_SIGN = bytes('MThd', 'ascii')  # header signature in MIDI file.
MIDI_TRACK_SIGN = bytes('MTrk', 'ascii')  # Track s11ignature in MIDI file.
MIDI_HEADER_MIN_LEN = 6
MIDI_TRACK_MIN_LEN = 100

MIDI_FILE = 'file'
MIDI_ERROR = 'error'
MIDI_HEADER_LENGTH = 'header length'
MIDI_HEADER_FORMAT_TYPE = 'format type'
MIDI_HEADER_NUMBER_OF_TRACKS = 'number of tracks'
MIDI_HEADER_TIME_BASE = 'time base'
MIDI_HEADER_POSITION = 'header position'
MIDI_TRACK_POSITION = 'position'

MIDI_META_SEQUENCE_NUMBER = 'sequence number'
MIDI_META_TEXT = 'text'
MIDI_META_COPYRIGHT = 'copyright'
MIDI_META_TRACK_NAME = 'track name'
MIDI_META_INSTRUMENT_NAME = 'instrument name'
MIDI_META_LYRICS = 'lyrics'
MIDI_META_MARKER = 'marker'
MIDI_META_QUEUE_POINT = 'queue point'
MIDI_META_PROGRAM_NAME = 'program name'
MIDI_META_DEVICE_NAME = 'device name'
MIDI_META_MIDI_CHANNEL_PREFIX = 'MIDI channel prefix'
MIDI_META_PORT = 'port'
MIDI_META_TEMPO = 'tempo'
MIDI_META_SMPTE_OFFSET = 'SMPTE offset'
MIDI_META_BEAT = 'beat'
MIDI_META_TONE = 'tone'
MIDI_META_SEQUENCER_EVENT = 'sequencer event'
MIDI_META_UNKNOWN = 'unknown meta info'

MIDI_EVENT_NOTE_OFF = 'note off'
MIDI_EVENT_NOTE_ON = 'note on'
MIDI_EVENT_POLYPHONIC_KEY_PRESSURE = 'polyphonic key pressure'
MIDI_EVENT_CONTROL_CHANGE = 'control change'
MIDI_EVENT_PROGRAM_CHANGE = 'program change'
MIDI_EVENT_CHANNEL_PRESSURE = 'channel pressure'
MIDI_EVENT_PITCH_BEND = 'pitch bend'
MIDI_EVENTS = 'events'
MIDI_EVENT_UNKNOWN = 'unknown event'


def read_variable_length_value(file):
    array = []
    for i in range(4):
        # raw_byte = file.read(1)
        raw_byte = file.read(1)
        if len(raw_byte) <= 0:
            return -1, 'can not read the file'
        v = raw_byte[0]
        array.append(v)
        if (v & 0x80) == 0:
            v = 0
            for j in range(len(array)):
                v = (v << 7) | (array[j] & 0x7f)
            return v, ''

    return -2, "too long. Max length exceeded."


def auto_decode(code):
    enc = detect(code)
    text = code
    if not enc['encoding'] is None:
        text = code.decode(errors='backslashreplace', encoding=enc['encoding']).replace('\x00', '')
    return text


def get_data(file):
    midi_info = {MIDI_FILE: f'{file}'}

    if not os.path.isfile(file):
        midi_info[MIDI_ERROR] = 'not a file.'
        return midi_info

    with open(file, 'rb') as midi:

        if not midi.seekable():
            midi_info[MIDI_ERROR] = 'Random access is not possible for this file.'
            return midi_info

        # HEADER

        read_buffer = midi.read(MIDI_RECORD_MIN_LEN)
        if len(read_buffer) < MIDI_RECORD_MIN_LEN:
            midi_info[MIDI_ERROR] = 'not a MIDI file. (not enough header record size)'
            return midi_info

        mid_head_sign = read_buffer[:4]
        if mid_head_sign != MIDI_HEAD_SIGN:
            midi_info[MIDI_ERROR] = 'not a MIDI file. (header signature mismatch)'
            return midi_info

        midi_header_length = int.from_bytes(read_buffer[4:8], byteorder='big')

        if midi_header_length < MIDI_HEADER_MIN_LEN:
            midi_info[MIDI_ERROR] = 'not a MIDI file. (not enough header length)'
            return midi_info

        midi_info[MIDI_HEADER_POSITION] = 0

        read_buffer = midi.read(midi_header_length)
        midi_format_type = int.from_bytes(read_buffer[0:2], byteorder='big')
        midi_number_of_tracks = int.from_bytes(read_buffer[2:4], byteorder='big')
        midi_time_base = int.from_bytes(read_buffer[4:6], byteorder='big')  # ticks of Quarter note

        midi_info[MIDI_HEADER_LENGTH] = midi_header_length
        midi_info[MIDI_HEADER_FORMAT_TYPE] = midi_format_type
        midi_info[MIDI_HEADER_NUMBER_OF_TRACKS] = midi_number_of_tracks
        midi_info[MIDI_HEADER_TIME_BASE] = midi_time_base

        # sikp header record
        midi.read(midi_header_length - MIDI_HEADER_MIN_LEN)

        # TRACK

        begin_pos = MIDI_RECORD_MIN_LEN + midi_header_length
        for track_no in range(midi_number_of_tracks):
            midi_info[f'TRACK-{track_no} ' + MIDI_TRACK_POSITION] = begin_pos
            midi.seek(begin_pos, os.SEEK_SET)

            read_buffer = midi.read(MIDI_RECORD_MIN_LEN)
            if len(read_buffer) < MIDI_RECORD_MIN_LEN:
                midi_info[MIDI_ERROR] = f'Track #{track_no} record not found. (not enough track record size)'
                return midi_info

            mid_track_sign = read_buffer[:4]
            if mid_track_sign != MIDI_TRACK_SIGN:
                midi_info[MIDI_ERROR] = f'Track #{track_no} record not found. (track signature mismatch)'
                return midi_info

            midi_track_length = int.from_bytes(read_buffer[4:8], byteorder='big')
            begin_pos += MIDI_RECORD_MIN_LEN + midi_track_length

            # read delta time and event

            events = []
            event_code = 0
            while midi_track_length > 0:

                # for delta time

                delta_time, error_message = read_variable_length_value(midi)
                if delta_time < 0:
                    midi_info[MIDI_ERROR] = f'Track #{track_no} is broken. ({error_message})'
                    return midi_info

                # for event

                read_buffer = midi.read(1)
                if len(read_buffer) <= 0: break
                event_code_old = event_code
                event_code = read_buffer[0]

                # handle running status
                if (event_code & 0x80) == 0:
                    event_code = event_code_old
                    midi.seek(-1, os.SEEK_CUR)  # rewind

                # SysEx event ... ignore
                if event_code == 0xf0:
                    pass
                elif event_code == 0xf7:
                    pass

                # META event
                elif event_code == 0xff:

                    # get meta type
                    read_buffer = midi.read(1)
                    if len(read_buffer) <= 0: break
                    meta_type = read_buffer[0]

                    # get data length
                    data_length, error_message = read_variable_length_value(midi)
                    if data_length < 0:
                        midi_info[MIDI_ERROR] = f'Track #{track_no} is broken. ({error_message})'
                        return midi_info

                    # get data
                    read_buffer = midi.read(data_length)
                    if data_length > 0 and len(read_buffer) <= 0:
                        midi_info[MIDI_ERROR] = f'Track #{track_no} is broken. (#202)'
                        return midi_info

                    # sequence number
                    if meta_type == 0x00:
                        v = int.from_bytes(read_buffer, byteorder='big')
                        midi_info[f'TRACK-{track_no} ' + MIDI_META_SEQUENCE_NUMBER] = v

                    # text
                    elif meta_type == 0x01:
                        midi_info[f'TRACK-{track_no} ' + MIDI_META_TEXT] = auto_decode(read_buffer)

                    # copyright
                    elif meta_type == 0x02:
                        midi_info[f'TRACK-{track_no} ' + MIDI_META_COPYRIGHT] = auto_decode(read_buffer)

                    # track name
                    elif meta_type == 0x03:
                        midi_info[f'TRACK-{track_no} ' + MIDI_META_TRACK_NAME] = auto_decode(read_buffer)

                    # instrument name
                    elif meta_type == 0x04:
                        midi_info[f'TRACK-{track_no} ' + MIDI_META_INSTRUMENT_NAME] = auto_decode(read_buffer)

                    # lyrics
                    elif meta_type == 0x05:
                        midi_info[f'TRACK-{track_no} ' + MIDI_META_LYRICS] = auto_decode(read_buffer)

                    # marker
                    elif meta_type == 0x06:
                        midi_info[f'TRACK-{track_no} ' + MIDI_META_MARKER] = auto_decode(read_buffer)

                    # queue point
                    elif meta_type == 0x07:
                        midi_info[f'TRACK-{track_no} ' + MIDI_META_QUEUE_POINT] = auto_decode(read_buffer)

                    # program name (timbre)
                    elif meta_type == 0x08:
                        midi_info[f'TRACK-{track_no} ' + MIDI_META_PROGRAM_NAME] = auto_decode(read_buffer)

                    # device name
                    elif meta_type == 0x09:
                        midi_info[f'TRACK-{track_no} ' + MIDI_META_DEVICE_NAME] = auto_decode(read_buffer)

                    # MIDI channel prefix
                    elif meta_type == 0x20:
                        # v = read_buffer[0]
                        v = int.from_bytes(read_buffer, byteorder='big')
                        midi_info[f'TRACK-{track_no} ' + MIDI_META_MIDI_CHANNEL_PREFIX] = v

                    # port
                    elif meta_type == 0x21:
                        # v = read_buffer[0]
                        v = int.from_bytes(read_buffer, byteorder='big')
                        midi_info[f'TRACK-{track_no} ' + MIDI_META_PORT] = v
                    # end of track
                    elif meta_type == 0x2f:
                        midi_info[f'TRACK-{track_no} ' + MIDI_EVENTS] = events
                        break
                    # tempo : Quarter note duration (usec)
                    elif meta_type == 0x51:
                        # v = read_buffer[0]
                        v = int.from_bytes(read_buffer, byteorder='big')
                        midi_info[f'TRACK-{track_no} ' + MIDI_META_TEMPO] = v

                    # SMPTE offset
                    elif meta_type == 0x54:
                        v1 = read_buffer[0]
                        v2 = read_buffer[1]
                        v3 = read_buffer[2]
                        v4 = read_buffer[3]
                        v5 = read_buffer[4]
                        midi_info[f'TRACK-{track_no} ' + MIDI_META_SMPTE_OFFSET] = [v1, v2, v3, v4, v5]

                    # beat
                    elif meta_type == 0x58:
                        v1 = read_buffer[0]
                        v2 = read_buffer[1]
                        v3 = read_buffer[2]
                        v4 = read_buffer[3]
                        midi_info[f'TRACK-{track_no} ' + MIDI_META_BEAT] = [v1, v2, v3, v4]

                    # tone
                    elif meta_type == 0x59:
                        v1 = read_buffer[0]
                        v2 = read_buffer[1]
                        midi_info[f'TRACK-{track_no} ' + MIDI_META_TONE] = [v1, v2]

                    # sequencer event
                    elif meta_type == 0x7f:
                        midi_info[f'TRACK-{track_no} ' + MIDI_META_SEQUENCER_EVENT] = read_buffer

                    # Unknown
                    else:
                        key = f'TRACK-{track_no} ' + MIDI_META_UNKNOWN
                        if key not in midi_info.keys():
                            midi_info[key] = [read_buffer]
                        else:
                            midi_info[key].append(read_buffer)

                # MIDI event
                else:
                    events.append(delta_time)

                    mask = 0xf0

                    # Note Off
                    if (event_code & mask) == 0x80:
                        read_buffer = midi.read(2)
                        ch = event_code & 0x0f
                        note = read_buffer[0]
                        velocity = read_buffer[1]
                        events.append([MIDI_EVENT_NOTE_OFF, ch, note, velocity])

                    # Note On
                    elif (event_code & mask) == 0x90:
                        read_buffer = midi.read(2)
                        ch = event_code & 0x0f
                        note = read_buffer[0]
                        velocity = read_buffer[1]
                        events.append([MIDI_EVENT_NOTE_ON, ch, note, velocity])

                    # Polyphonic Key Pressure
                    elif (event_code & mask) == 0xa0:
                        read_buffer = midi.read(2)
                        ch = event_code & 0x0f
                        note = read_buffer[0]
                        velocity = read_buffer[1]
                        events.append([MIDI_EVENT_POLYPHONIC_KEY_PRESSURE, ch, note, velocity])

                    # Control Change
                    elif (event_code & mask) == 0xb0:
                        read_buffer = midi.read(2)
                        ch = event_code & 0x0f
                        controler_no = read_buffer[0]
                        v = read_buffer[1]
                        events.append([MIDI_EVENT_CONTROL_CHANGE, ch, controler_no, v])

                    # Program Change
                    elif (event_code & mask) == 0xc0:
                        read_buffer = midi.read(1)
                        ch = event_code & 0x0f
                        pp = read_buffer[0]
                        events.append([MIDI_EVENT_PROGRAM_CHANGE, ch, pp])

                    # Channel Pressure
                    elif (event_code & mask) == 0xd0:
                        read_buffer = midi.read(1)
                        ch = event_code & 0x0f
                        vv = read_buffer[0]
                        events.append([MIDI_EVENT_CHANNEL_PRESSURE, ch, vv])

                    # Pitch Bend
                    elif (event_code & mask) == 0xe0:
                        read_buffer = midi.read(2)
                        ch = event_code & 0x0f
                        mm = read_buffer[0]
                        ll = read_buffer[1]
                        events.append([MIDI_EVENT_PITCH_BEND, ch, mm, ll])

                    # Unknown
                    else:
                        events.append([MIDI_EVENT_UNKNOWN, event_code])

    return midi_info
