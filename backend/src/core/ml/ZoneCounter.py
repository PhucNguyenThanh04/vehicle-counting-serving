import cv2
import numpy as np
from dataclasses import dataclass, field
from typing import Optional
import supervision as sv
from collections import deque
from copy import copy
from datetime import datetime
from src.core.ml.utils import get_foot_position


@dataclass
class ZoneConfig:
    zone_id: str
    polygon: list[list[int]]
    color: tuple[int, int, int]
    length: float          # Chiều dài thực của zone (m) — dùng làm fallback
    name: str = ""


@dataclass
class VehicleEvent:
    track_id: int
    cls: str               # Tên class (str), không phải class_id (int)
    zone_id: str

    first_seen: datetime
    last_seen: datetime

    entry_point: Optional[tuple[float, float]] = None
    exit_point: Optional[tuple[float, float]] = None
    speed: float = 0.0
    direction: str = "unknown"
    time_in_zone: float = 0.0


_FONT = cv2.FONT_HERSHEY_SIMPLEX
_INFO_FONT_SCALE = 0.5
_INFO_THICKNESS = 1
_LINE_HEIGHT = 20


class ZoneCounter:
    def __init__(self, config: ZoneConfig, class_names: dict = None):
        self.config = config
        self.polygon = np.array(config.polygon, dtype=np.int32)

        # track_id đã từng đi vào (để đếm đúng 1 lần / lượt)
        self.counted_ids: set[int] = set()

        # {cls_name: count}
        self.counts: dict[str, int] = {}

        # track_id hiện đang ở trong zone
        self.inside_ids: set[int] = set()

        # Events đã hoàn chỉnh (xe đã rời zone, có đủ speed + direction)
        self.events: deque[VehicleEvent] = deque(maxlen=100)

        # Events đang theo dõi (xe còn trong zone)
        self.active: dict[int, VehicleEvent] = {}

        self.class_names = class_names or {}

    # ── public ──

    def update(
        self,
        detection: sv.Detections,
        timestamp: datetime,
    ) -> list[VehicleEvent]:

        if detection.tracker_id is None or len(detection.tracker_id) == 0:
            return self._flush_exited(set(), timestamp)

        current_ids: set[int] = set()

        for track_id, cls_id, bbox in zip(
            detection.tracker_id,
            detection.class_id,
            detection.xyxy,
        ):
            foot_x, foot_y = get_foot_position(bbox)
            if not self._point_in_polygon(foot_x, foot_y):
                continue

            current_ids.add(track_id)
            cls_name = self.class_names.get(int(cls_id), str(cls_id))

            # ── Xe vừa vào zone ──
            if track_id not in self.inside_ids:
                self.inside_ids.add(track_id)
                self.active[track_id] = VehicleEvent(
                    track_id=track_id,
                    cls=cls_name,           # lưu str ngay từ đầu
                    zone_id=self.config.zone_id,
                    first_seen=timestamp,
                    last_seen=timestamp,
                    entry_point=(foot_x, foot_y),
                    exit_point=(foot_x, foot_y),
                )

            # ── Cập nhật vị trí mới nhất ──
            ev = self.active[track_id]
            ev.last_seen = timestamp
            ev.exit_point = (foot_x, foot_y)

            if track_id not in self.counted_ids:
                self.counted_ids.add(track_id)
                self.counts[cls_name] = self.counts.get(cls_name, 0) + 1

        return self._flush_exited(current_ids, timestamp)

    def _flush_exited(
        self,
        current_ids: set[int],
        timestamp: datetime,
    ) -> list[VehicleEvent]:
        completed: list[VehicleEvent] = []
        exited = self.inside_ids - current_ids

        for track_id in exited:
            ev = self.active.pop(track_id, None)
            if ev is None:
                continue

            dt = (ev.last_seen - ev.first_seen).total_seconds()
            ev.time_in_zone = dt
            ev.direction = self._compute_direction(ev.entry_point, ev.exit_point)
            ev.speed = self._compute_speed(ev.entry_point, ev.exit_point, dt)

            self.events.append(copy(ev))
            completed.append(ev)

        self.inside_ids -= exited
        return completed

    def _compute_direction(self, entry: tuple, exit_: tuple) -> str:
        if entry is None or exit_ is None:
            return "unknown"
        dy = exit_[1] - entry[1]
        threshold = 20
        if abs(dy) < threshold:
            return "unknown"
        return "down" if dy > 0 else "up"
    def _compute_speed(
        self,
        entry: Optional[tuple[float, float]],
        exit_: Optional[tuple[float, float]],
        dt: float,
    ) -> float:
        if dt <= 0 or entry is None or exit_ is None:
            return 0.0

        pixel_dist = float(np.hypot(exit_[0] - entry[0], exit_[1] - entry[1]))

        if pixel_dist < 1.0:
            return round(self.config.length / dt * 3.6, 2)

        return round(self.config.length / dt * 3.6, 2)

    def _point_in_polygon(self, x: float, y: float) -> bool:
        return cv2.pointPolygonTest(self.polygon, (x, y), False) >= 0

    def draw(self, frame: np.ndarray, show_count: bool = True) -> np.ndarray:
        color = self.config.color

        cv2.polylines(frame, [self.polygon], True, color, 2)

        overlay = frame.copy()
        cv2.fillPoly(overlay, [self.polygon], color)
        cv2.addWeighted(overlay, 0.2, frame, 0.8, 0, frame)
        if show_count:
            M = cv2.moments(self.polygon)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                total = sum(self.counts.values())
                # cv2.putText(
                #     frame,
                #     f"{self.config.zone_id} + \n + {str(total)}",
                #     (cx - 10, cy),
                #     _FONT, 0.9, color, 2,
                # )
                line1 = str(self.config.zone_id)
                line2 = str(total)

                (text_w1, text_h1), _ = cv2.getTextSize(line1, _FONT, 0.9, 2)
                (text_w2, text_h2), _ = cv2.getTextSize(line2, _FONT, 0.9, 2)

                # căn giữa
                cv2.putText(frame, line1, (cx - text_w1 // 2, cy - 10), _FONT, 0.9, color, 2)
                cv2.putText(frame, line2, (cx - text_w2 // 2, cy + text_h2 +5), _FONT, 0.9, color, 2)


        return frame

    def draw_info_box(self, frame: np.ndarray, position: tuple[int, int]) -> np.ndarray:
        x, y = position
        color = self.config.color
        label = self.config.zone_id

        lines = [f"len {label}:"] + [f"{cls} : {count}" for cls, count in self.counts.items()]

        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        thickness = 2
        line_height = 20

        for i, line in enumerate(lines):
            cv2.putText(frame, line,
                        (x, y + line_height * i),
                        font, font_scale, color, thickness)

        return frame
    def info_box_width(self) -> int:

        label = self.config.name or self.config.zone_id
        lines = [f"[{label}]"] + [f"  {cls}: {cnt}" for cls, cnt in self.counts.items()]
        if not lines:
            return 80
        return max(
            cv2.getTextSize(line, _FONT, _INFO_FONT_SCALE, _INFO_THICKNESS)[0][0]
            for line in lines
        )


class ZoneCounterManager:
    def __init__(self, zone_configs: list[ZoneConfig], class_names: dict = None):
        self.zones: dict[str, ZoneCounter] = {
            cfg.zone_id: ZoneCounter(cfg, class_names=class_names)
            for cfg in zone_configs
        }

    def update_all(
        self,
        detection: sv.Detections,
        timestamp: datetime,
    ) -> dict[str, list[VehicleEvent]]:
        if not self.zones:
            return {}

        all_events: dict[str, list[VehicleEvent]] = {}
        for zone_id, zone in self.zones.items():
            completed = zone.update(detection, timestamp)
            if completed:
                all_events[zone_id] = completed

        return all_events

    def get_all_counts(self) -> dict[str, dict[str, int]]:
        return {
            zone_id: zone.counts
            for zone_id, zone in self.zones.items()
        }

    def draw_all(self, frame: np.ndarray) -> np.ndarray:
        # Vẽ polygon của từng zone
        for zone in self.zones.values():
            zone.draw(frame)

        x_cursor = 30
        y_start = 100
        gap = 20

        for zone in self.zones.values():
            zone.draw_info_box(frame, (x_cursor, y_start))
            x_cursor += zone.info_box_width() + gap

        return frame