# import the necessary packages
from imutils.video import VideoStream
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import threading
import imutils
import time
import cv2
import uvicorn
from multiprocessing import Process, Queue
import subprocess
import numpy as np

HTTP_PORT = 6064
lock = threading.Lock()
app = FastAPI()

manager = None
count_keep_alive = 0

width = 1280
height = 720

url_rtsp = 'rtsp://admin:smartcam@192.168.0.172/profile5/media.smp'

def run_ffmpeg():
    global width
    global height

    get_entries = ['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height',
                   '-of', 'csv=s=x:p=0', url_rtsp]
    s = subprocess.Popen(get_entries, stdout=subprocess.PIPE)
    probe_str = s.communicate()[0]  # Reading content of p0.stdout (output of FFprobe) as string
    s.wait()
    width, height = probe_str.decode('ascii').rstrip().split('x')

    width = int(width)
    height = int(height)

    command = [
        'ffmpeg',
        '-i', url_rtsp,
        '-video_size', f'{680}x{480}',
        '-pix_fmt', 'bgr24',  # opencv requires bgr24 pixel format
        '-vcodec', 'rawvideo',
        '-an', '-sn',  # disable audio processing
        '-f', 'image2pipe',
        '-',  # output to go to stdout
    ]
    return subprocess.Popen(command, stdout=subprocess.PIPE, bufsize=10 ** 8)


def start_stream(url_rtsp, manager):
    global width
    global height

    # vs = VideoStream(url_rtsp).start()
    ffmpeg_process = run_ffmpeg()
    while True:
        time.sleep(0.2)
        raw_image = ffmpeg_process.stdout.read(width*height*3)
        if raw_image == b'':
            raise RuntimeError("Empty pipe")

        # frame = vs.read()
        frame = np.frombuffer(raw_image, dtype='uint8')
        # frame = imutils.resize(frame, width=680)
        frame = frame.reshape((height, width, 3))  # height, width, channels
        output_frame = frame.copy()

        if output_frame is None:
            continue
        (flag, encodedImage) = cv2.imencode(".jpg", output_frame)
        if not flag:
            continue
        manager.put(encodedImage)


def streamer():
    try:
        while manager:
            yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' +
                   bytearray(manager.get()) + b'\r\n')
    except GeneratorExit:
        print("cancelled")


def manager_keep_alive(p):
    global count_keep_alive
    global manager
    while count_keep_alive:
        time.sleep(1)
        print(count_keep_alive)
        count_keep_alive -= 1
    p.kill()
    time.sleep(.5)
    p.close()
    manager.close()
    manager = None



@app.get("/")
def video_feed():
    return StreamingResponse(streamer(), media_type="multipart/x-mixed-replace;boundary=frame")


@app.get("/keep-alive")
def keep_alive():
    global manager
    global count_keep_alive
    count_keep_alive = 100
    if not manager:
        manager = Queue()
        p = Process(target=start_stream, args=('rtsp://admin:smartcam@192.168.0.172/profile5/media.smp', manager,))
        p.start()
        threading.Thread(target=manager_keep_alive, args=(p,)).start()


# check to see if this is the main thread of execution
if __name__ == '__main__':
    # start the flask app
    uvicorn.run(app, host="0.0.0.0", port=HTTP_PORT, access_log=False)
