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


def load_zone_manager(config_path: str) -> ZoneCounterManager:
    with open(config_path) as f:
        data = json.load(f)
    configs = [ZoneConfig(**z) for z in data["zone"]]
    return ZoneCounterManager(configs)

class VideoProcessor:
    def __init__(self,
                 url: str,
                 weight_model : str,
                 device: torch.device,
                 conf_thresh: float,
                 iou_thresh:float
                 ) -> None:

        # Xử lý 1 frame trên 3 frame để tối ưu
        self._FRAME_SKIP = 3
        self.model = DetectionModel(
            model_path = weight_model,
            device = device,
            conf_thresh = conf_thresh,
            iou_thresh = iou_thresh

        )
        self.reader = MJPEGReader(url)

        self.zone_manager = load_zone_manager("src/core/zone.json")

        #fps
        self.frame_counter = 0
        self.start_time = time.time()
        self.real_fps = 0




    def __enter__(self):
        self.reader.start()
        return self

    def __exit__(self, *_):
        self.reader.stop()

    # def process_video(self) -> None:
    #     last_annotated = None
    #     with self.reader:
    #         for frame_data in self.reader.frames():
    #
    #             if frame_data.image is None:
    #                 continue
    #
    #             frame = frame_data.image
    #
    #             if frame_data.index % self._FRAME_SKIP == 0:
    #                 timestamp = datetime.datetime.now()
    #                 last_annotated = self.process_frame(frame, timestamp)
    #
    #             if last_annotated is not None:
    #                 # yield last_annotated
    #                 cv2.imshow("YOLO Detection", last_annotated)
    #                 if cv2.waitKey(1) & 0xFF == ord("q"):
    #                     break
    #     cv2.destroyAllWindows()
    # def process_frame(self, frame: np.ndarray, timestamp: datetime) -> np.ndarray:
    #
    #     detections = self.model.tracking_frame(frame=frame)
    #
    #     frame_anotate = frame.copy()
    #
    #     frame_anotate = self.model.annotation_frame(frame=frame_anotate, detections=detections)
    #
    #     self.zone_manager.update_all(detections=detections, timestamp=timestamp)
    #     frame_anotate = self.zone_manager.draw_all(frame=frame_anotate)
    #     frame_anotate = self.draw_real_fps(frame=frame_anotate)
    #
    #     return frame_anotate

    def process_video(self) -> None:
        last_annotated = None

        with self.reader:
            for frame_data in self.reader.frames():

                if frame_data.image is None:
                    continue

                frame = frame_data.image

                if frame_data.index % self._FRAME_SKIP == 0:
                    # Lỗi 1+2 sửa: dùng datetime object, không strftime
                    timestamp = datetime.datetime.now()
                    last_annotated = self.process_frame(frame, timestamp)

                if last_annotated is not None:
                    cv2.imshow("YOLO Detection", last_annotated)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break

        cv2.destroyAllWindows()

    def process_frame(self, frame: np.ndarray, timestamp: datetime.datetime) -> np.ndarray:

        detections = self.model.tracking_frame(frame=frame)

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


if __name__ == '__main__':
    STREAM_URL = "http://localhost:8080/stream"
    WEIGHT_MODEL = "weights/yolov8m.pt"
    DEVICE = torch.device("cuda:0")
    CONF_THRESH = 0.5
    IOU_THRESH = 0.5

    processor = VideoProcessor(
        url=STREAM_URL,
        weight_model=WEIGHT_MODEL,
        device=DEVICE,
        conf_thresh=CONF_THRESH,
        iou_thresh=IOU_THRESH
    )
    processor.process_video()





