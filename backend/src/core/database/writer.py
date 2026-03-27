import asyncio
import queue
import traceback
from datetime import datetime
from sqlalchemy.dialects.postgresql import insert as pg_insert
from src.core.database.db import AsyncSessionLocal
from src.api.entities import Vehicle, ZoneCount
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class DBWriter:
    def __init__(
        self,
        event_queue: queue.Queue,
        batch_size: int = 50,
        flush_interval: float = 2.0,    # giây
        count_interval: float = 30.0,   # giây
    ):
        self._event_queue = event_queue
        self._batch_size = batch_size
        self._flush_interval = flush_interval
        self._count_interval = count_interval
        self._pending: list = []
        self._running = False

    async def start(self, processor):
        self._running   = True
        self._processor = processor
        await asyncio.gather(
            self._event_writer_loop(),
            self._count_snapshot_loop(),
        )

    async def stop(self):
        self._running = False
        await self._flush()    # flush nốt phần còn lại trước khi tắt


    async def _event_writer_loop(self):
        last_flush = asyncio.get_event_loop().time()

        while self._running:
            try:
                while True:
                    ev = self._event_queue.get_nowait()
                    self._pending.append(ev)
            except queue.Empty:
                pass

            now = asyncio.get_event_loop().time()
            should_flush = (
                len(self._pending) >= self._batch_size
                or (now - last_flush) >= self._flush_interval
            )

            if should_flush and self._pending:
                await self._flush()
                last_flush = now

            await asyncio.sleep(0.5)   # check mỗi 0.5s

    async def _flush(self):
        if not self._pending:
            return

        batch = self._pending.copy()
        self._pending.clear()

        async with AsyncSessionLocal() as session:
            try:
                # Sử dụng entities.Vehicle (tên class là Vehicle) và map đúng tên trường
                vehicles = [
                    Vehicle(
                        track_id=getattr(ev, "track_id", None),
                        cls_name=str(getattr(ev, "cls", getattr(ev, "cls_name", ""))),
                        zone_id=getattr(ev, "zone_id", None),
                        first_seen=getattr(ev, "first_seen", None),
                        last_seen=getattr(ev, "last_seen", None),
                        time_in_zone=int(getattr(ev, "time_in_zone", 0)),
                        direction=str(getattr(ev, "direction", "")),
                        speed=int(getattr(ev, "speed", 0)),
                    )
                    for ev in batch
                ]
                session.add_all(vehicles)
                await session.commit()
                # logger.info(f"Inserted {len(vehicles)} vehicle events successfully")
            except Exception as e:
                await session.rollback()
                traceback.print_exc()
                # Đẩy lại batch nếu lỗi
                self._pending.extend(batch)


    async def _count_snapshot_loop(self):
        while self._running:
            await asyncio.sleep(self._count_interval)
            await self._save_count_snapshot()

    async def _save_count_snapshot(self):
        counts = self._processor.get_counts()
        now = datetime.utcnow().replace(microsecond=0)

        async with AsyncSessionLocal() as session:
            try:
                for zone_id, class_counts in counts.items():
                    for cls, count in class_counts.items():
                        stmt = pg_insert(ZoneCount).values(
                            zone_id=str(zone_id),
                            cls=cls,
                            count=count,
                            snapshot_at=now,
                        ).on_conflict_do_update(
                            index_elements=["zone_id", "cls"],  # unique constraint
                            set_={
                                "count": count,
                                "snapshot_at": now,
                            }
                        )
                        await session.execute(stmt)
                await session.commit()
                logger.info("zone count records successfully")
            except Exception as e:
                await session.rollback()
                logger.error(f"loi insert db cua zone counter: {str(e)}")