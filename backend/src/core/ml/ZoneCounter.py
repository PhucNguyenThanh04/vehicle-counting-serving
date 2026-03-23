import cv2
import numpy as np
from dataclasses import dataclass
import supervision as sv
from collections import deque
from copy import copy
from datetime import datetime
from src.core.ml.utils import get_foot_position



@dataclass
class ZoneConfig:
    zone_id: str
    polygon: list[list[int]]
    color: tuple[int,int,int]
    length: float
    name: str = ""

@dataclass
class VehicleEvent:
    track_id: int
    cls: str
    zone_id: str

    first_seen: datetime
    last_seen: datetime

    entry_point: tuple[float, float] = None
    exit_point: tuple[float, float] = None
    speed: float = 0.0  # Tính bằng km/h , có thể cập nhật sau khi rời zone
    direction: str = "unknown"  # "up", "down", "unknown"
    time_in_zone : float = 0.0 # Tính bằng giây, cập nhật khi xe rời zone


class ZoneCounter:
    def __init__(self, config: ZoneConfig, class_names: dict = None):
        self.config = config
        self.polygon = np.array(config.polygon, dtype=np.int32)
        self.counted_ids: set[int] = set()
        self.counts: dict[str, int] = {}
        self.inside_ids: set[int] = set()
        self.events: deque[VehicleEvent] = deque(maxlen=100)
        self.active: dict[int, VehicleEvent] = {}
        self.class_names = class_names or {}

    def update(self, detection: sv.Detections, timestamp: datetime
               ) -> list[VehicleEvent]:

        new_events = []
        current_ids = set()

        for track_id, cls, bbox in zip(
                detection.tracker_id,
                detection.class_id,
                detection.xyxy
        ):
            foot_x, foot_y = get_foot_position(bbox)
            in_zone = self._point_in_polygon(foot_x, foot_y)

            if not in_zone:
                continue

            current_ids.add(track_id)

            # xe di vao zone
            if track_id not in self.inside_ids:
                self.inside_ids.add(track_id)

                self.active[track_id] = VehicleEvent(
                    track_id=track_id,
                    cls=cls,
                    zone_id=self.config.zone_id,
                    first_seen=timestamp,
                    last_seen=timestamp,
                    entry_point=(foot_x, foot_y),
                    exit_point=(foot_x, foot_y),
                )

            self.active[track_id].last_seen = timestamp
            self.active[track_id].exit_point = (foot_x, foot_y)

            # Đếm lần đầu tiên
            if track_id not in self.counted_ids:
                cls_name = self.class_names.get(int(cls), str(cls))
                self.counted_ids.add(track_id)
                self.counts[cls_name] = self.counts.get(cls_name, 0) + 1
                ev = copy(self.active[track_id])
                self.events.append(ev)
                new_events.append(ev)

        # Xe rời zone — tính time_in_zone và direction
        exited = self.inside_ids - current_ids
        for track_id in exited:
            ev = self.active.get(track_id)
            if ev:
                ev.time_in_zone = (ev.last_seen - ev.first_seen).total_seconds()
                ev.direction = self._compute_direction(
                    ev.entry_point, ev.exit_point
                )
                # length (m) / time (s) -> m/s, *3.6 -> km/h
                ev.speed = self.config.length / ev.time_in_zone * 3.6 if ev.time_in_zone > 0 else 0.0
            self.inside_ids.discard(track_id)
            self.active.pop(track_id, None)
            # print(f"{ev.direction}, {ev.first_seen}, {ev.last_seen}, {ev.time_in_zone}s")

        return new_events

    def _compute_direction(self, entry_point, exit_point) -> str:
        if not entry_point or not exit_point:
            return "unknown"

        _, y1 = entry_point
        _, y2 = exit_point
        dy = y2 - y1
        return "down" if dy > 0 else "up"

    def _point_in_polygon(self, foot_x: float, foot_y: float) -> bool:
        return cv2.pointPolygonTest(self.polygon, (foot_x, foot_y), False) >= 0

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
                label = self.config.name or self.config.zone_id
                cv2.putText(frame, f" {total}",
                            (cx - 40, cy),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)


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



class ZoneCounterManager:
    def __init__(self, zone_configs: list[ZoneConfig], class_names = None):
        self.zones = {
            cfg.zone_id: ZoneCounter(cfg, class_names=class_names)
            for cfg in zone_configs
        }

    def update_all(self, detection: sv.Detections, timestamp: datetime):

        if not self.zones:
            return {}

        all_events: dict[str, list[VehicleEvent]] = {}
        for zone_id, zone in self.zones.items():
            new_events = zone.update(detection, timestamp)
            if new_events:
                all_events[zone_id] = new_events


        return all_events

    def get_all_counts(self) -> dict:

        return {
            zone_id: zone.counts
            for zone_id, zone in self.zones.items()
        }

    # def draw_all(self, frame: np.ndarray)-> np.ndarray:
    #     for zone in self.zones.values():
    #         zone.draw(frame)
    #
    #     return frame

    def draw_all(self, frame: np.ndarray) -> np.ndarray:  # bỏ model đi
        for zone in self.zones.values():
            zone.draw(frame)

        x_start = 30
        y_start = 100
        current_x = x_start

        for zone in self.zones.values():
            label = zone.config.name or zone.config.zone_id
            lines = [label] + [f"{cls} : {count}" for cls, count in zone.counts.items()]
            font = cv2.FONT_HERSHEY_SIMPLEX
            max_width = max(
                cv2.getTextSize(line, font, 0.5, 1)[0][0]
                for line in lines
            ) if lines else 80

            zone.draw_info_box(frame, (current_x, y_start))
            current_x += max_width + 30

        return frame
