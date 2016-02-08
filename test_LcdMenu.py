import time

from char_display import CharDisplay
from pib_events import PibEvents
from lcd_menu import LcdMenu

display = CharDisplay()
events = PibEvents()
up = True
entries = [ (1,'toto'), (2,'tutu'), (3,'tata'), (5,'tete') ]

menu = LcdMenu(display, entries, 1)

while up:
    while events.queue.empty() == False:
        e = events.queue.get_nowait()

        if e[0] == PibEvents.KEY:
            selection = menu.process_key(e[1])
            if selection is not None:
                up = False
                print "menu returned:",selection

    time.sleep(0.2)

events.stop()
display.enable(False)

print "done."
