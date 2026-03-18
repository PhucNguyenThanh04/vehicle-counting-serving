import cv2
import numpy as np
import urllib.request
import threading
import queue
import time
from dataclasses import dataclass

@dataclass
class FrameData:
    index:       int
    timestamp_s: float
    image:       np.ndarray


class MJPEGReader:

    def __init__(self, url: str, timeout: int = 10,
                 reconnect_delay: int = 3):
        self.url = url
        self.timeout = timeout
        self.reconnect_delay = reconnect_delay

        self._queue = queue.Queue(maxsize=2)
        self._stop_event = threading.Event()
        self._thread = None
        self._frame_idx = 0
        self._start_time = None


    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *_):
        self.stop()


    def start(self):
        self._start_time = time.time()
        self._thread = threading.Thread(
            target=self._read_loop, daemon=True
        )
        self._thread.start()
        return self

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)

    def read(self) -> tuple[bool, FrameData | None]:
        try:
            return True, self._queue.get(timeout=3.0)
        except queue.Empty:
            return False, None

    def frames(self):
        while not self._stop_event.is_set():
            ok, frame_data = self.read()
            if ok:
                yield frame_data


    def _read_loop(self):
        while not self._stop_event.is_set():
            try:
                self._connect_and_read()
            except Exception as e:
                print(f"[MJPEGReader] Lỗi: {e}")
                print(f"[MJPEGReader] Thử lại sau {self.reconnect_delay}s...")
                time.sleep(self.reconnect_delay)

    def _connect_and_read(self):
        print(f"[MJPEGReader] Kết nối: {self.url}")
        stream = urllib.request.urlopen(self.url, timeout=self.timeout)
        print("[MJPEGReader] Kết nối thành công")

        buffer = b""

        while not self._stop_event.is_set():
            buffer += stream.read(4096)

            start = buffer.find(b"\xff\xd8")   # SOI marker
            end = buffer.find(b"\xff\xd9")   # EOI marker

            if start == -1 or end == -1 or end < start:
                if len(buffer) > 1024 * 1024:
                    buffer = b""
                continue

            # Extract JPEG bytes
            jpg = buffer[start: end + 2]
            buffer = buffer[end + 2:]

            frame = cv2.imdecode(
                np.frombuffer(jpg, dtype=np.uint8),
                cv2.IMREAD_COLOR,
            )
            if frame is None:
                continue

            ts = time.time() - self._start_time

            frame_data = FrameData(
                index=self._frame_idx,
                timestamp_s=round(ts, 3),
                image=frame,
            )
            self._frame_idx += 1

            # Bỏ frame cũ nếu queue đầy — giữ frame mới nhất
            if self._queue.full():
                try:
                    self._queue.get_nowait()
                except queue.Empty:
                    pass
            self._queue.put(frame_data)

