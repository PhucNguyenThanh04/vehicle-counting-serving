import cv2
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

class MJPEGHandler(BaseHTTPRequestHandler):

    video_path = None
    _lock = threading.Lock()
    _frame = None

    def log_message(self, *args):
        pass

    def do_GET(self):
        if self.path != "/stream":
            self.send_response(404)
            self.end_headers()
            return

        self.send_response(200)
        self.send_header("Content-Type",
                         "multipart/x-mixed-replace; boundary=frame")
        self.end_headers()

        try:
            while True:
                with MJPEGHandler._lock:
                    frame = MJPEGHandler._frame

                if frame is None:
                    time.sleep(0.01)
                    continue

                _, jpg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                jpg_bytes = jpg.tobytes()

                # MJPEG boundary format
                self.wfile.write(
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n"
                    b"Content-Length: " + str(len(jpg_bytes)).encode() + b"\r\n"
                    b"\r\n" + jpg_bytes + b"\r\n"
                )
        except (BrokenPipeError, ConnectionResetError):
            pass


def _capture_loop(video_path: str, fps: float):
    delay = 1.0 / fps
    while True:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise FileNotFoundError(f"Không mở được: {video_path}")

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            with MJPEGHandler._lock:
                MJPEGHandler._frame = frame

            time.sleep(delay)

        cap.release()


def start_fake_camera(video_path: str, host: str = "0.0.0.0",
                      port: int = 8080, fps: float = 25.0):

    MJPEGHandler.video_path = video_path

    # Thread đọc video
    t = threading.Thread(
        target=_capture_loop,
        args=(video_path, fps),
        daemon=True,
    )
    t.start()

    print("Đang load video...", end=" ")
    while MJPEGHandler._frame is None:
        time.sleep(0.05)
    print("OK")

    server = HTTPServer((host, port), MJPEGHandler)
    print(f"Fake camera running: http://{host}:{port}/stream")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDừng server.")
        server.shutdown()


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "videos/wqctLW0Hb_0.mp4"
    start_fake_camera(path, fps=25.0)