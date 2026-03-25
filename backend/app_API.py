from contextlib import asynccontextmanager
import asyncio
import torch

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from src.core.ml.Video_Processor import VideoProcessor
from src.core.config import configs
from src.utils.logger import setup_logger
from src.core.db import get_db, init_db
from src.api import entities
from src.api.repositories.writer import DBWriter
import queue
import logging


# set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

logger = setup_logger(__name__)

event_queue: queue.Queue = queue.Queue(maxsize=500)
processor: VideoProcessor | None = None
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()

    global processor
    processor = VideoProcessor(
        url_camera_ip=configs.STREAM_URL,
        weight_model=configs.WEIGHT_MODEL_PATH,
        device=torch.device("cuda:0"),
        conf_thresh=0.5,
        iou_thresh=0.5,
        event_queue=event_queue
    )
    db_writer = DBWriter(
        event_queue=event_queue,
        batch_size=50,
        flush_interval=2.0,
        count_interval=30.0,
    )

    logger.info("load xong model + preprocess cho stream")
    processor.start()

    asyncio.create_task(db_writer.start(processor))

    yield
    await db_writer.stop()
    processor.stop()

app = FastAPI(
    title="Vehicle Tracking API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins  = ["*"],
    allow_methods  = ["*"],
    allow_headers  = ["*"],
)


@app.get("/")
async def root():
    return {"message": "Vehicle Tracking API is running"}


async def _mjpeg_generator():
    while True:
        jpg = processor.get_jpg()
        if jpg is not None:
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n"
                + jpg
                + b"\r\n"
            )
        await asyncio.sleep(0.04)


@app.get("/stream")
async def stream():
    logger.info("start stream video")
    return StreamingResponse(
        _mjpeg_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )

@app.get("/counts")
async def get_counts():
    logger.info("lay so xe dem duoc tung vung")
    return processor.get_counts()


# if __name__ == '__main__':
#     import uvicorn
#
#     uvicorn.run(app, host="0.0.0.0", port=8000)
