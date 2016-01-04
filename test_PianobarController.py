import time
from keyboard_events import KeyboardEvents
from pianobar_controller import PianobarController

ke = KeyboardEvents()

pianobar_ctrl = PianobarController(ke, 0)
pianobar_ctrl.control()

print "stop keyboard listener"
ke.stop()

print "done."
