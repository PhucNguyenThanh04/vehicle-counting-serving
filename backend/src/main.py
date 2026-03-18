from src.core.ml.Video_Processor import  VideoProcessor
import torch


if __name__ == '__main__':
    STREAM_URL = "http://localhost:8080/stream"
    WEIGHT_MODEL = "../weights/yolov8m.pt"
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

