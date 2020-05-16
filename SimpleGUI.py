#!/usr/bin/env python

import sys
import os
import time
import math
import re

import pygtk
pygtk.require('2.0')
import gtk
from threading import Thread
import thread
import pango

_draw_flow_lock=thread.allocate_lock()

gtk.gdk.threads_init()

class gui(Thread):

    def __init__(self, title="Progress", width=760, height=700, frac=0, iconfile=None):

        Thread.__init__(self)

        self._flow_width=1024
        self._scale_text_to_fit=True
        self._scale_box_to_fit=False
        self._flow_data=None

        self._n_messages=0
        self._window_title=title
        
        self._can_quit=False
        self._window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self._window.set_border_width(0)
        self._window.set_default_size(width, height)
        if iconfile is not None:
            self._window.set_icon_from_file(iconfile)
        self._window.connect("delete_event", self._delete_event)
        self._window.connect("destroy", self._destroy)

        # Vertical box to store it all
        self._mainbox=gtk.VBox(False, 0)
        self._window.add(self._mainbox)

        # Frame/box for progress
        progress_frame=gtk.Frame("Progress")
        progress_frame.set_border_width(3)
        progress_frame.show()
        self._mainbox.pack_start(progress_frame, False, False, 0)
        self._progress_box=gtk.VBox(False, 0)
        self._progress_box.set_border_width(3)
        # Progress message
        self._progress_label=gtk.Label()
        self._progress_label.show()
        # The progress bar
        self._progress_bar=gtk.ProgressBar()
        self._progress_bar.set_orientation(gtk.PROGRESS_LEFT_TO_RIGHT)
        self._progress_box.pack_start(self._progress_bar, True, True, 0)
        self._progress_box.pack_start(self._progress_label, False, False, 5)
        progress_frame.add(self._progress_box)

        # Frame/box for messages
        self._message_frame=gtk.Frame("Messages")
        self._message_frame.set_border_width(3)
        self._message_frame.show()
        self._mainbox.pack_start(self._message_frame, True, True, 0)
        message_listscroll = gtk.ScrolledWindow()
        message_listscroll.set_shadow_type(gtk.SHADOW_IN)
        message_listscroll.set_border_width(3)
        self._message_liststore=gtk.ListStore(str, str)
        self._message_listview=gtk.TreeView(self._message_liststore)
        cell_rend_message=gtk.CellRendererText()
        self._message_listview.append_column( gtk.TreeViewColumn("Message",   cell_rend_message, markup=0, cell_background=1) )
        self._message_listview.set_headers_visible(False)
        #self._message_listview.connect("row-activated", self.preview_callback, None)
        listsel=self._message_listview.get_selection()
        #listsel.set_mode(gtk.SELECTION_MULTIPLE)
        listsel.set_mode(gtk.SELECTION_NONE)
        message_listscroll.add(self._message_listview)        
        self._message_frame.add(message_listscroll)
        message_listscroll.show()
        self._message_listview.show()
        self.set_frac(frac)

        # Show it all
        self._progress_bar.show()
        self._progress_box.show()
        self._mainbox.show()
        self._window.show()

    def run(self):

        # Main GUI loop
        gtk.main()

    def new_message(self, message):

        colour=["white", "grey90"][self._n_messages % 2]

        gtk.gdk.threads_enter()
        message_iter=self._message_liststore.append([message, colour])
        message_path=self._message_liststore.get_path(message_iter)
        self._message_listview.scroll_to_cell(message_path)
        gtk.gdk.threads_leave()

        self._n_messages+=1

    def _delete_event(self, widget, event, data=None):

        "Delete event callback."
        self._destroy(None,None)

        return True

    def _destroy(self, widget, data=None):
        "Destroy/quit callback."

        if self._can_quit:
            self.close()

    def enable_quit(self):

        self._can_quit=True
    
    def close(self):

        self._window.destroy()
        gtk.main_quit()

    def set_frac(self, frac):

        gtk.gdk.threads_enter()
        self._progress_bar.set_fraction(frac)
        self._window.set_title("%s - %3d%%" % (self._window_title, int(frac*100)))
        gtk.gdk.threads_leave()

    def set_text(self, text):
        
        gtk.gdk.threads_enter()
        self._progress_label.set_text(text)
        gtk.gdk.threads_leave()

        
if __name__ == "__main__":

    import time

    try:

        g=gui(title="GUI")
        g.start()

        #g.read_flow("program_flow.plain")
        
        ntest=100
        for i in range(ntest):
            g.set_text("Doing %d of %d ..." % (i, ntest))
            time.sleep(0.05)
            g.set_frac((i+1.)/ntest)
            if i==25:
                g.new_message("A message")
            if i==35:
                g.new_message("Another message")
                g.new_message("Another message")
                g.new_message("Another message")
                g.new_message("Another message")
                g.new_message("Another message")
                g.new_message("Another message")
                g.new_message("Another message")
                g.new_message("Another message")
            if i==45:
                g.new_message("A more interesting message. Not.")

    except Exception, mess:

        g.new_message("<b>"+str(mess)+"</b>")

    #finally:

    g.enable_quit()
    g.new_message("<b>Waiting for you to close the window.....</b>")
    g.join()

    print "Thankyou. Finished"
