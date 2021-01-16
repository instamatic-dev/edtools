# https://github.com/alandmoore/cpython/blob/53046dcf91481f3e69ddbc97e5d8d0d921c1d09f/Lib/tkinter/ttk.py
from tkinter.ttk import Entry
import tkinter as tk

class Spinbox(Entry):
    """Ttk Spinbox is an Entry with increment and decrement arrows It is
    commonly used for number entry or to select from a list of string
    values."""

    def __init__(self, master=None, **kw):
        """Construct a Ttk Spinbox widget with the parent master.

        STANDARD OPTIONS: class, cursor, style, takefocus, validate,
        validatecommand, xscrollcommand, invalidcommand

        WIDGET-SPECIFIC OPTIONS: to, from_, increment, values, wrap, format, command
        """
        Entry.__init__(self, master, 'ttk::spinbox', **kw)

    def set(self, value):
        """Sets the value of the Spinbox to value."""
        self.tk.call(self._w, 'set', value)

class Hoverbox:
    """
    create a tooltip for a given widget
    """
    def __init__(self, widget, text='widget info'):
        self.waittime = 500     #miliseconds
        self.wraplength = 180   #pixels
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<ButtonPress>", self.leave)
        self.id = None
        self.tw = None

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(self.waittime, self.showtip)

    def unschedule(self):
        id = self.id
        self.id = None
        if id:
            self.widget.after_cancel(id)

    def showtip(self, event=None):
        x = y = 0
        x, y, cx, cy = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        # creates a toplevel window
        self.tw = tk.Toplevel(self.widget)
        # Leaves only the label and removes the app window
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(self.tw, text=self.text, justify='left',
                       background="#ffffff", relief='solid', borderwidth=1,
                       wraplength = self.wraplength)
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tw
        self.tw= None
        if tw:
            tw.destroy()