import time

from char_display import CharDisplay

disp = CharDisplay()

time.sleep(3)

disp.static_msg(1, "Line 1: \x00 \x01 \x7E", 1)
disp.scroll_msg(2, "[And a long second line that scrolls]", 0.2)

for i in range(0,400):
    disp.update()
    if i == 60:
        disp.timed_msg(1, "Temporary message", 8)
    if i == 100:
        disp.timed_msg(2, "\x02\x05 \x03\x05 \x04\x05 \x04\x06 \x04\x07", 12)
    if i == 200:
        disp.static_msg(2, "New text on 2nd!", 1)
    time.sleep(0.1)

disp.enable(False)

time.sleep(1)

