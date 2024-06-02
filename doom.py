from pyxll import xl_func, Formatter
from pathlib import Path
import cydoomgeneric as cdg
import scipy.ndimage
import numpy as np
import threading
import itertools
import time


_frame = None
_frame_event = threading.Event()
_thread = None
_thread_lock = threading.Lock()


def _draw_frame(pixels):
    """Called by the Doom main loop whenever a frame is drawn."""
    global _frame
    _frame = pixels
    _frame_event.set()
    time.sleep(0.01)


def _get_key():
    """Called by the Doom main loop to get inputs."""
    pass


def _start_doom():
    """Starts Doom in a background thread, if not already started.
    """
    global _thread


    with _thread_lock:
        if _thread is None:
            def doom_thread_func(wadfile):
                cdg.init(640, 400, _draw_frame, _get_key)
                cdg.main(["", "-iwad", str(wadfile), "-playdemo"])

            wadfile = Path(__file__).parent / "Doom1.WAD"
            if not wadfile.exists():
                raise RuntimeError(f"WAD file '{wadfile}' not found.")

            _thread = threading.Thread(target=doom_thread_func, args=(wadfile,))
            _thread.daemon = True
            _thread.start()

    return True


class DoomFormatter(Formatter):
    """Formatter class that set the cell interior color to the 
    cell value (colour value as uint32 BGR) and sets the number
    format to blank.
    """

    def apply(self, cell, value=None, **kwargs):
        if not isinstance(value, np.ndarray):
            return

        self.apply_style(cell, {
            "number_format": ";;;"
        })

        cell = cell.resize(1, 1)
        for y in range(0, value.shape[0]):
            for x in range(0, value.shape[1]):
                self.apply_style(cell.offset(y, x), {
                    "interior_color": value[y, x]
                })


@xl_func("float scale: rtd<union<str, numpy_array>>", formatter=DoomFormatter())
def doom(scale=0.15):

    _start_doom()

    yield "Please wait..."

    while True:
        _frame_event.wait()

        pixels = scipy.ndimage.zoom(_frame, [scale, scale, 1])
        
        pixels = pixels.astype(np.uint32)

        blue = pixels[:,:,0]
        green = pixels[:,:,1]
        red = pixels[:,:,2]

        blue = (blue >> 3) << 3
        green = (green >> 3) << 3
        red = (red >> 3) << 3

        pixels = (blue << 16) | (green << 8) | red
        yield pixels


if __name__ == "__main__":
    for pixels in itertools.islice(doom(), 25):
        print(pixels)