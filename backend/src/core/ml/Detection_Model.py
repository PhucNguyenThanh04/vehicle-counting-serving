import cv2
import numpy as np
from ultralytics import YOLO
import torch
import supervision as sv
from src.core.ml.utils import get_foot_position

class DetectionModel:
    def __init__(self,
                 model_path: str,
                 device: torch.device,
                 conf_thresh: float,
                 iou_thresh: float
                 ) -> None:
        self.model = YOLO(model_path)
        self.model.to(device)
        # print(self.model.names)
        self.conf_thresh = conf_thresh
        self.iou_thresh = iou_thresh

        self.tracker = sv.ByteTrack(track_buffer=90, frame_rate=30, match_thresh=0.9)
        # self.palette = sv.ColorPalette.default()

        self.palette = sv.ColorPalette.from_hex([
            "#336666", "#00FF00", "#00FFFF",
            # "#FF99CC", "#FF6633"
        ])

    def tracking_frame(self, frame: np.ndarray) -> sv.Detections:

        results = self.model(
            frame, verbose=False, conf=self.conf_thresh, iou=self.iou_thresh, half=True
        )[0]
        detections =sv.Detections.from_ultralytics(results)
        detections =self.tracker.update_with_detections(detections=detections)
        return detections

    def annotation_frame(self, frame: np.ndarray,
                         detections: sv.Detections) -> np.ndarray:

        annotator_frame = frame.copy()
        detections = detections[detections.class_id>=0]

        for bbox, class_id in zip(
                detections.xyxy,
                detections.class_id
        ):
            x1, y1, x2, y2 = map(int, bbox)

            color = self.palette.by_idx(class_id).as_bgr()
            cv2.rectangle(annotator_frame, (x1, y1), (x2, y2), color, 2)

            cv2.putText(
                annotator_frame,
                self.model.names[class_id],
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                2
            )

            foot_x, foot_y = get_foot_position(bbox)
            cv2.circle(annotator_frame, (foot_x, foot_y), 5, color, -1)

        return annotator_frame

    def map_zone(self, detections: sv.Detections, tracker_to_zone):
        pass


if __name__ == '__main__':

    from mjpeg_reader import MJPEGReader

    model = DetectionModel(
        model_path="../../../weights/yolov8m.pt",
        device=torch.device("cuda:0"),
        conf_thresh=0.5,
        iou_thresh=0.5
    )
    STREAM_URL = "http://localhost:8080/stream"

    delay = 1.0 / 25


    with MJPEGReader(STREAM_URL) as reader:
        frame_count = 0  # Đếm số lượng frame đã đọc

        for frame_data in reader.frames():
            frame_count += 1

            # Chỉ xử lý frame thứ 3
            if frame_count % 1 == 0:
                results = model.tracking_frame(frame_data.image)
                annotated_frame = model.annotation_frame(frame_data.image, results)
                cv2.imshow("YOLO Detection", annotated_frame)

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
            # else:
            #     # Hiển thị frame trước đó nếu không xử lý
            #     if 'annotated_frame' in locals():
            #         cv2.imshow("YOLO Detection", annotated_frame)

                if cv2.waitKey(1 % 25) & 0xFF == ord("q"):
                    break

    cv2.destroyAllWindows()
