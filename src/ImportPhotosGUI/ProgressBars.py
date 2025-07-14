#!/usr/bin/python3

import sys

class progress_bar:

    def __init__(self, title=None, width=79, frac=0):

        self._length=width-9
        if self._length<20:
            self._length=20
        self._barstring=""

        if title is not None:
            print(title)

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
        string+=" {:3d}%".format(int(round(frac*100)))
        self._barstring="[ "+string+" ]"

        print(delstring+self._barstring, end='')
        sys.stdout.flush()

    def close(self):
        print()

if __name__ == "__main__":

    import time

    bar=progress_bar(title="Text progress bar")
    bar.start()

    ntest=50
    for i in range(ntest):
        bar.set_text("Doing %d of %d ..." % (i, ntest))
        time.sleep(0.005)
        bar.set_frac((i+1)/ntest)
    bar.close()
