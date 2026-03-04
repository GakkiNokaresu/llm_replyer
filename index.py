import whisper
from audio import *


def p():
    print("success")


recording = Recording()
recording.set_input_device(input_device_proposals[0])
print(recording.record(p))
