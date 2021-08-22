import os
import tempfile
import subprocess
import cv2
import numpy as np
import time

# To get this path execute:
#    $ which ffmpeg
FFMPEG_BIN = '/usr/bin/ffmpeg'

def run_ffmpeg():
    ffmpg_cmd = [
        FFMPEG_BIN,
        '-i', 'rtsp://admin:admin@192.168.0.160',
        '-video_size', '640x480',
        '-pix_fmt', 'bgr24',  # opencv requires bgr24 pixel format
        '-vcodec', 'rawvideo',
        '-an', '-sn',  # disable audio processing
        '-f', 'image2pipe',
        '-',  # output to go to stdout
    ]
    return subprocess.Popen(ffmpg_cmd, stdout=subprocess.PIPE, bufsize=10 ** 8)


def run_cv_window(process):
    while True:
        time.sleep(0.2)
        # read frame-by-frame
        raw_image = process.stdout.read(640 * 480 * 3)
        if raw_image == b'':
            raise RuntimeError("Empty pipe")

        # transform the bytes read into a numpy array
        frame = np.frombuffer(raw_image, dtype='uint8')
        frame = frame.reshape((480, 640, 3))  # height, width, channels
        if frame is not None:
            cv2.imshow('Video', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        process.stdout.flush()

    cv2.destroyAllWindows()
    process.terminate()
    print(process.poll())


def run():
    ffmpeg_process = run_ffmpeg()
    run_cv_window(ffmpeg_process)

run()