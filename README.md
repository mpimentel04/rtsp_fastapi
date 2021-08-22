# rtsp_fastapi

Stream video from a RTSP to a web browser

I'm using multiprocessing to avoid memory leak when finished the  image stream.

[Setup]

1 - Install the dependencies in requirements.txt

2 - Alter variable url_rtsp

3 - Start server webstreaming.py

[Test]

1 - After started the server, open the page http://localhost:6064/keep-alive

2 - Open the http://localhost:6064/ to watch the stream rtsp through browser
