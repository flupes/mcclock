import time

from char_display import CharDisplay

disp = CharDisplay()

time.sleep(3)

disp.static_msg(1, "Text on first line", 1)
disp.scroll_msg(2, "[And a long second line that scrolls]", 0.2)

for i in range(0,400):
    disp.update()
    if i == 60:
        disp.timed_msg(1, "Temporary message", 8)
    if i == 100:
        disp.timed_msg(2, "  it will last 6s", 6)
    if i == 200:
        disp.static_msg(2, "New text on 2nd!", 1)
    time.sleep(0.1)

disp.enable(False)

time.sleep(1)

