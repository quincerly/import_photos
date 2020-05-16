#!/usr/bin/python

import sys, time
from threading import Thread
import pygtk
pygtk.require('2.0')
import gtk

class progress_bar:

    def __init__(self, title=None, width=79, frac=0):

        self._length=width-9
        if self._length<20:
            self._length=20
        self._barstring=""

        if title is not None:
            print title

        self.set_frac(0)

    def start(self):
        pass

    def set_text(self, text):
        pass

    def set_frac(self, frac):

        delstring="\b"*(len(self._barstring)+1)

        string=""
        num=int(frac*self._length)
        string+="#"*num+" "*(self._length-num)
        string+=" %3d%%" % round(frac*100)
        self._barstring="[ "+string+" ]"

        print delstring+self._barstring,
        sys.stdout.flush()

    def close(self):
        print

class gui_progress_bar(Thread):

    def __init__(self, title="Progress", width=400, frac=0):

        Thread.__init__(self)
       
        self._window_title=title
        self._quit_dialog=None
        self._window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self._window.set_border_width(0)
        self._window.set_default_size(width, -1)
        self._window.set_icon_from_file("/dan/pix/icons/camera_icon.png")
        self._window.connect("delete_event", self._delete_event)
        self._window.connect("destroy", self._destroy)

        # Vertical box to store it all
        self._mainbox=gtk.VBox(False, 0)
        self._window.add(self._mainbox)

        # File name label
        self._label=gtk.Label()
        self._mainbox.pack_start(self._label, False, False, 5)
        self._label.show()

        # The progress bar
        self._progress_frame=gtk.HBox(True, 0)
        self._progress_frame.set_border_width(0)
        self._mainbox.pack_start(self._progress_frame, False, False, 0)
        self._progress_bar=gtk.ProgressBar()
        self._progress_bar.set_orientation(gtk.PROGRESS_LEFT_TO_RIGHT)
        self._progress_frame.pack_start(self._progress_bar, True, True, 0)

        self.set_frac(frac)

        # Show it all
        self._progress_bar.show()
        self._progress_frame.show()
        self._mainbox.show()
        self._window.show()

    def run(self):

        # Main GUI loop
        gtk.main()

    def _delete_event(self, widget, event, data=None):
        "Delete event callback."

        self._destroy(None,None)

        return True # Don't die

    def _destroy(self, widget, data=None):
        "Destroy/quit callback."

        pass # Do nothing

    def close(self):
        self._window.destroy()
        self._window=None
        self.join()

    def set_frac(self, frac):

        self._progress_bar.set_fraction(frac)
        self._window.set_title("%s - %3d%%" % (self._window_title, int(frac*100)))

    def set_text(self, text):
        
        self._label.set_text(text)
            
if __name__ == "__main__":

    import time

    # Import files
    bars=[]
    bars.append(gui_progress_bar(title="GUI progress bar"))
    bars.append(progress_bar(title="Text progress bar"))

    for bar in bars: bar.start()

    ntest=50
    for i in range(ntest):
        for bar in bars: bar.set_text("Doing %d of %d ..." % (i, ntest))
        time.sleep(0.005)
        for bar in bars: bar.set_frac((i+1.)/ntest)
    for bar in bars: bar.close()
