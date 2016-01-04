import time
from keyboard_events import KeyboardEvents
from pianobar_controller import PianobarController

ke = KeyboardEvents()
pianobar_ctrl = PianobarController(ke, 0)

print "main thread sleeping 12s"
time.sleep(12)
print "ask controller to shutdown"
pianobar_ctrl.shutdown()
print "stop keyboard listener"
ke.stop()
print "done."
