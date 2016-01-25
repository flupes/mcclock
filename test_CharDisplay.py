import time

from char_display import CharDisplay

disp = CharDisplay()

time.sleep(3)

disp.static_msg(0, "This is a static line", 0)
#disp.static_msg(1, "And a second.", 2)
disp.scroll_msg(1, "[And a long second line that scrolls]", 0.2)

for i in range(0,300):
    disp.update()
    time.sleep(0.1)

disp.lcd.clear()
disp.lcd.set_color(0,0,0)
disp.lcd.enable_display(False)
time.sleep(1)

