from events_base import EventsBase

class LcdMenu(object):

    selection = 0
    """Index of the current menu entry selected"""
    
    def __init__(self, display, entries, selection):
        """ Initialize the menu.
        display -- the display target
        entries -- a list of tuples composing the menu elements (id,string)
        selection -- the active selection (index in the dictionary
        """
        self.display = display
        self.entries = entries
        self.maximum = len(entries)
        self.update_display(selection)

    def update_display(self, index):
        """Update the menu display with the current index in t
        the list of menu entries"""
        if (index >= 0) and (index < self.maximum):
            self.selection = index
            self.display.static_msg(1, '\x7E '+self.entries[index][1], 1, flush=True)
            if index < self.maximum-1:
                self.display.static_msg(2, '  '+self.entries[index+1][1], 1, flush=True)
            else:
                self.display.static_msg(2, '  \xB0\xB0\xB0', 1, flush=True)
    
    def process_key(self, key):
        """Process the given key event
        Returns the menu value if selected, None otherwise,
        or -1 if the user wants to leave the menu without
        selection (left key)"""
        if key == EventsBase.KEY_RIGHT:
            print "RIGHT"
            self.display.lcd.clear()
            return self.entries[self.selection][0]
        elif key == EventsBase.KEY_LEFT:
            print "LEFT"
            self.display.lcd.clear()
            return -1
        elif key == EventsBase.KEY_DOWN:
            print "DOWN"
            self.update_display(self.selection+1)
            return None
        elif key == EventsBase.KEY_UP:
            print "UP"
            self.update_display(self.selection-1)
            return None
