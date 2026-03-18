from ultralytics import YOLO
import cv2
import numpy as np
import torch
import os
import yt_dlp

# ── Config ────────────────────────────────────────────────
URL= "https://youtu.be/wqctLW0Hb_0?si=5iYIOopWsMvobQ9e"
MODEL_PATH = "weights/best_s.pt"
OUTPUT_DIR = "../videos"
FRAME_SKIP = 1
IMGSZ = 640
CONF = 0.25
SHOW_WIN= True


def download_youtube_video(url: str, output_dir: str = "./videos") -> str:
    os.makedirs(output_dir, exist_ok=True)

    ydl_opts = {
        "format": "bestvideo[height<=720][ext=mp4]+bestaudio/best[height<=720]",
        "outtmpl": f"{output_dir}/%(id)s.%(ext)s",
        "quiet": True,
        "no_warnings": True,
        "merge_output_format": "mp4",
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        # prepare_filename có thể trả .webm nếu merge chưa xong — fix chắc chắn:
        filename = ydl.prepare_filename(info)
        filename = os.path.splitext(filename)[0] + ".mp4"

    print(f"Đã tải : {filename}")
    print(f"Độ dài : {info['duration']//60}p{info['duration']%60}s")
    print(f"Độ phân giải: {info.get('width')}x{info.get('height')}")
    return filename


def get_video_info(video_path: str) -> dict:
    cap = cv2.VideoCapture(video_path)
    info = {
        "total_frames": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
        "fps":          cap.get(cv2.CAP_PROP_FPS),
        "width":        int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
        "height":       int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
    }
    info["duration_min"] = info["total_frames"] / max(info["fps"], 1) / 60
    cap.release()
    return info


def letterbox_resize(frame: np.ndarray, size: int = 640) -> np.ndarray:
    """Resize giữ tỉ lệ, không méo hình."""
    h, w = frame.shape[:2]
    scale = size / max(h, w)
    if scale >= 1.0:
        return frame
    return cv2.resize(frame, (int(w * scale), int(h * scale)),
                      interpolation=cv2.INTER_LINEAR)


def run(url: str):
    print("Đang tải video YouTube...")
    video_path = download_youtube_video(url, OUTPUT_DIR)

    info = get_video_info(video_path)
    fps          = info["fps"] or 30
    total_frames = info["total_frames"]
    print(f"\nVideo info: {total_frames} frames | {fps:.1f} fps | "
          f"{info['width']}x{info['height']} | "
          f"{info['duration_min']:.1f} phút")
    print(f"Sẽ infer ~{total_frames // FRAME_SKIP:,} frames (skip={FRAME_SKIP})\n")

    # Device: giữ cả torch.device và chuỗi để truyền cho ultralytics
    device_torch = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    device_str = "cuda:0" if torch.cuda.is_available() else "cpu"

    # Debug info về CUDA / môi trường
    print(f"Using device_torch={device_torch}, device_str={device_str}")
    print('torch', torch.__version__, 'torch.cuda', torch.version.cuda, 'cuda_available', torch.cuda.is_available())
    print('CUDA_VISIBLE_DEVICES=', os.environ.get('CUDA_VISIBLE_DEVICES'))

    model = YOLO(MODEL_PATH)
    # Ép model sang device dạng chuỗi (ultralytics đôi khi chấp nhận string)
    try:
        model.to(device_str)
    except Exception:
        # fall back to torch.device if needed
        model.to(device_torch)

    # In thiết bị của tham số đầu tiên nếu khả dụng
    try:
        pdev = next(p.device for p in model.parameters() if p.numel() > 0)
    except Exception:
        # ultralytics YOLO wrapper có thể không expose parameters() trực tiếp
        try:
            pdev = next(p.device for p in getattr(model, 'model').parameters() if p.numel() > 0)
        except Exception:
            pdev = 'unknown'
    print('model params device:', pdev)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Lỗi: không mở được file {video_path}")
        return

    # Delay giữa các frame khi hiển thị (ms) — giữ tốc độ xem tự nhiên
    display_delay = max(1, int(1000 / fps))

    frame_idx   = 0
    last_annotated = None   # giữ frame annotated cuối để hiển thị frame skip

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % FRAME_SKIP == 0:
            # Resize trước khi infer (tiết kiệm compute)
            frame_small = letterbox_resize(frame, IMGSZ)

            # Thay device (torch.device) bằng chuỗi device_str để ultralytics nhận chính xác
            results = model(frame_small, conf=CONF, verbose=False, device = device_str)
            last_annotated = results[0].plot()

        # Hiển thị — dùng last_annotated để không skip frame trên màn hình
        if SHOW_WIN and last_annotated is not None:
            cv2.imshow("YOLO Detection", last_annotated)
            if cv2.waitKey(display_delay) & 0xFF == ord('q'):
                print("Người dùng dừng.")
                break

        frame_idx += 1

    cap.release()
    if SHOW_WIN:
        cv2.destroyAllWindows()

    print(f"\nHoàn tất. Đã xử lý {frame_idx} frames.")


# --- Thêm function test nhanh (dummy forward) để kiểm tra GPU mà không cần tải video ---

def run_dummy_test():
    """Forward một tensor giả qua model để kiểm tra device và thời gian nhanh."""
    device_torch = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    device_str = "cuda:0" if torch.cuda.is_available() else "cpu"
    print('--- RUN DUMMY TEST ---')
    print('torch', torch.__version__, 'torch.cuda', torch.version.cuda, 'cuda_available', torch.cuda.is_available())
    print('CUDA_VISIBLE_DEVICES=', os.environ.get('CUDA_VISIBLE_DEVICES'))

    model = YOLO(MODEL_PATH)
    try:
        model.to(device_str)
    except Exception:
        model.to(device_torch)

    # Tạo tensor giả trên device torch để ép forward dùng GPU
    x = torch.zeros((1, 3, IMGSZ, IMGSZ), dtype=torch.float32, device=device_torch)
    print('input device:', x.device)

    try:
        import time
        t0 = time.time()
        _ = model(x, device = device_str)
        t1 = time.time()
        print(f'Dummy forward OK, took {(t1-t0):.3f}s')
    except Exception as e:
        print('Dummy forward failed:', e)


if __name__ == "__main__":
    # Nếu muốn chỉ test model/device nhanh: export DEBUG_ONLY_MODEL=1
    if os.environ.get('DEBUG_ONLY_MODEL') == '1':
        run_dummy_test()
    else:
        run(URL)
