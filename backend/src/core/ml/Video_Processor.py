import datetime
import os
os.environ["KMP_DUPLICATE_LIB_OK"]="TRUE"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"


import cv2
import torch
import numpy as np
import time
from src.core.ml.mjpeg_reader import MJPEGReader
from src.core.ml.Detection_Model import DetectionModel
from src.core.ml.ZoneCounter import ZoneCounter, ZoneCounterManager, ZoneConfig
import json


def load_zone_manager(config_path: str, class_names) -> ZoneCounterManager:
    with open(config_path) as f:
        data = json.load(f)
    configs = [ZoneConfig(**z) for z in data["zone"]]
    return ZoneCounterManager(configs,class_names )

class VideoProcessor:
    def __init__(self,
                 url: str,
                 weight_model : str,
                 device: torch.device,
                 conf_thresh: float,
                 iou_thresh:float
                 ) -> None:

        # Xử lý 1 frame trên 3 frame để tối ưu
        self._FRAME_SKIP = 1
        self.model = DetectionModel(
            model_path = weight_model,
            device = device,
            conf_thresh = conf_thresh,
            iou_thresh = iou_thresh

        )
        self.roi = (2, 256, 1277, 611)
        self.reader = MJPEGReader(url)

        self.zone_manager = load_zone_manager("src/core/zone.json", class_names=self.model.model.names)

        #fps
        self.frame_counter = 0
        self.start_time = time.time()
        self.real_fps = 0




    def __enter__(self):
        self.reader.start()
        return self

    def __exit__(self, *_):
        self.reader.stop()

    def process_video(self) -> None:
        last_annotated = None
        TARGET_FPS = 25
        FRAME_TIME = 1.0 / TARGET_FPS

        with self.reader:
            for frame_data in self.reader.frames():

                start_loop = time.time()

                if frame_data.image is None:
                    continue

                frame = frame_data.image

                if frame_data.index % self._FRAME_SKIP == 0:
                    # Lỗi 1+2 sửa: dùng datetime object, không strftime
                    timestamp = datetime.datetime.now().replace(microsecond=0)
                    last_annotated = self.process_frame(frame, timestamp)

                if last_annotated is not None:
                    cv2.imshow("YOLO Detection", last_annotated)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break

                elapsed = time.time() - start_loop
                sleep_time = FRAME_TIME - elapsed
                if sleep_time > 0:
                    time.sleep(sleep_time)

        cv2.destroyAllWindows()

    def process_frame(self, frame: np.ndarray, timestamp: datetime.datetime) -> np.ndarray:

        detections = self.model.tracking_frame(frame=frame, roi=self.roi)

        frame_annotated = frame.copy()
        frame_annotated = self.model.annotation_frame(
            frame=frame_annotated, detections=detections
        )

        self.zone_manager.update_all(detection=detections, timestamp=timestamp)
        frame_annotated = self.zone_manager.draw_all(frame=frame_annotated)
        frame_annotated = self.draw_real_fps(frame=frame_annotated)

        return frame_annotated




    def draw_real_fps(self, frame: np.ndarray) -> np.ndarray:
        self.frame_counter += 1
        current_time = time.time()
        elapsed = current_time - self.start_time

        if elapsed >= 1.0:
            self.real_fps = self.frame_counter / elapsed
            self.frame_counter = 0
            self.start_time = current_time
        cv2.putText(
            frame, f"FPS: {self.real_fps:.1f}", (0 + 50,  0 + 60), cv2.FONT_HERSHEY_SIMPLEX,
            1, (0, 255, 0), 2, cv2.LINE_AA)
        return frame


# if __name__ == '__main__':
#     STREAM_URL = "http://localhost:8080/stream"
#     WEIGHT_MODEL = "weights/yolo26m.pt"
#     DEVICE = torch.device("cuda:0")
#     CONF_THRESH = 0.5
#     IOU_THRESH = 0.5
#
#     processor = VideoProcessor(
#         url=STREAM_URL,
#         weight_model=WEIGHT_MODEL,
#         device=DEVICE,
#         conf_thresh=CONF_THRESH,
#         iou_thresh=IOU_THRESH
#     )
#     processor.process_video()
#






