import os
os.environ["KMP_DUPLICATE_LIB_OK"]="TRUE"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

import torch.backends.cudnn as cudnn
from src.core.ml.Video_Processor import VideoProcessor
import torch
from src.core.config import configs
if __name__ == '__main__':
    cudnn.benchmark = True

    STREAM_URL = configs.STREAM_URL
    DEVICE = torch.device("cuda:0")
    CONF_THRESH = 0.5
    IOU_THRESH = 0.5

    print(configs.WEIGHT_MODEL_PATH)

    processor = VideoProcessor(
        url=STREAM_URL,
        weight_model=configs.WEIGHT_MODEL_PATH,
        device=DEVICE,
        conf_thresh=CONF_THRESH,
        iou_thresh=IOU_THRESH
    )
    processor.run_local()
