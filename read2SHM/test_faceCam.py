from pymba import Vimba, VimbaException
import sys
import os
# when executed as a process add parent SHM dir to path again
sys.path.insert(1, os.path.join(sys.path[0], '..')) # project dir
sys.path.insert(1, os.path.join(sys.path[0], '..', 'SHM')) # SHM dir

import time
import argparse
import cv2


from CustomLogger import CustomLogger as Logger



def _read_stream_faceCam(y_res, x_res, nchannels):

    with Vimba() as vimba:
        camera = vimba.camera(0)
        camera.open()

        camera.arm('SingleFrame')

        frame_i = 0
        # capture a single frame, more than once if desired
        while True:

            frame = camera.acquire_frame()
            image = frame.buffer_data_numpy()
            pack = "<{" + f"N:I,ID:{frame_i},PCT:{int(time.time()*1e6)}" + "}>\r\n"

            # frame = frame[:y_res, :x_res, :nchannels]
            # frame = frame.transpose(1,0,2) # cv2: y-x-rgb, everywhere: x-y-rgb
            frame_i += 1
            print(image[0])
            
        # camera.disarm()

        # camera.close()






if __name__ == "__main__":
    # cam = _get_setup_camera()
    _read_stream_faceCam(480, 640, 3)