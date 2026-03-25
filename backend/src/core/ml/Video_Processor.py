import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

import datetime
import threading
import cv2
import torch
import numpy as np
import time
import json
import queue

from src.core.ml.mjpeg_reader import MJPEGReader
from src.core.ml.Detection_Model import DetectionModel
from src.core.ml.ZoneCounter import ZoneCounterManager, ZoneConfig
from src.core.config import configs
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

def load_zone_manager(config_path: str, class_names) -> ZoneCounterManager:
    with open(config_path) as f:
        data = json.load(f)
    configs = [ZoneConfig(**z) for z in data["zone"]]
    return ZoneCounterManager(configs, class_names)


class VideoProcessor:
    def __init__(self,
                 url_camera_ip: str,
                 weight_model: str,
                 device: torch.device,
                 conf_thresh: float,
                 iou_thresh: float,
                 event_queue: queue.Queue = None,
                 ) -> None:
        self._FRAME_SKIP = 1
        self.model = DetectionModel(
            model_path=weight_model,
            device=device,
            conf_thresh=conf_thresh,
            iou_thresh=iou_thresh
        )
        self.event_queue = event_queue
        self.roi = (2, 256, 1277, 611)
        self.reader = MJPEGReader(url_camera_ip)
        self.zone_manager = load_zone_manager(
            "src/core/zone.json",
            class_names=self.model.clsnames
        )

        # FPS
        self.frame_counter = 0
        self.start_time = time.time()
        self.real_fps = 0.0

        # thread
        self._jpg_cache: bytes | None = None
        self._jpg_lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None


    def start(self) -> None:
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self.ml_loop, daemon=True, name="ml pipeline"
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        self.reader.stop()
        if self._thread:
            self._thread.join(timeout=5)

    def ml_loop(self) -> None:
        TARGET_FPS = 25
        FRAME_TIME = 1.0 / TARGET_FPS

        with self.reader:
            for frame_data in self.reader.frames():
                if self._stop_event.is_set():
                    break

                if frame_data.image is None:
                    continue

                t0 = time.perf_counter()

                frame = frame_data.image
                if frame_data.index % self._FRAME_SKIP == 0:
                    timestamp = datetime.datetime.now().replace(microsecond=0)
                    last_annotated = self.process_frame(frame, timestamp)

                    _, buf = cv2.imencode(
                        ".jpg", last_annotated,
                        [cv2.IMWRITE_JPEG_QUALITY, 70],
                    )
                    with self._jpg_lock:
                        self._jpg_cache = buf.tobytes()

                elapsed = time.perf_counter() - t0
                wait = FRAME_TIME - elapsed
                if wait > 0:
                    time.sleep(wait)

    def process_frame(
            self, frame: np.ndarray, timestamp: datetime.datetime
    ) -> np.ndarray:
        detections = self.model.tracking_frame(frame=frame)
        frame_annotated = self.model.annotation_frame(frame=frame.copy(), detections=detections)
        frame_annotated = self.zone_manager.draw_all(frame=frame_annotated)
        events =self.zone_manager.update_all(detection=detections, timestamp=timestamp)
        if events:
            for zone_events in events.values():
                for ev in zone_events:
                    try:
                        self.event_queue.put_nowait(ev)
                    except queue.Full:
                        pass

        # logger.info(f"frame {timestamp} , events: {events}")
        frame_annotated = self.draw_fps(frame=frame_annotated)
        return frame_annotated

    def draw_fps(self, frame: np.ndarray) -> np.ndarray:
        self.frame_counter += 1
        elapsed = time.time() - self.start_time
        if elapsed >= 1.0:
            self.real_fps = self.frame_counter / elapsed
            self.frame_counter = 0
            self.start_time = time.time()
        cv2.putText(
            frame, f"FPS: {self.real_fps:.1f}",
            (50, 60), cv2.FONT_HERSHEY_SIMPLEX,
            1, (0, 255, 0), 2, cv2.LINE_AA,
        )
        return frame

    def run_local(self) -> None:
        last_annotated = None
        with self.reader:
            for frame_data in self.reader.frames():
                if frame_data.image is None:
                    continue
                if frame_data.index % self._FRAME_SKIP == 0:
                    timestamp = datetime.datetime.now().replace(microsecond=0)
                    last_annotated = self.process_frame(frame=frame_data.image, timestamp=timestamp)
                if last_annotated is not None:
                    cv2.imshow("frame", last_annotated)
                    if cv2.waitKey(1) & 0XFF == 27:
                        break
        cv2.destroyAllWindows()


    def get_jpg(self) -> bytes | None:
        with self._jpg_lock:
            return self._jpg_cache

    def get_counts(self) -> dict:
        return self.zone_manager.get_all_counts()
