"""DataFlow Pipeline — Core ETL module."""

import asyncio
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Record:
    id: str
    payload: dict[str, Any]
    metadata: dict[str, str] = field(default_factory=dict)


class Pipeline:
    """Async ETL pipeline with configurable processing stages."""

    def __init__(self, source_url: str, batch_size: int = 100):
        self.source_url = source_url
        self.batch_size = batch_size
        self._stages: list = []

    def add_stage(self, name: str, func):
        self._stages.append({"name": name, "func": func})
        return self

    async def _fetch_batch(self, offset: int) -> list[Record]:
        await asyncio.sleep(0.1)  # simulate network
        return [
            Record(id=f"rec_{offset + i}", payload={"value": i * 2})
            for i in range(self.batch_size)
        ]

    async def run(self, max_records: int = 1000) -> list[Record]:
        results = []
        for offset in range(0, max_records, self.batch_size):
            batch = await self._fetch_batch(offset)
            for stage in self._stages:
                batch = [stage["func"](r) for r in batch]
            results.extend(batch)
        return results


def transform_uppercase(record: Record) -> Record:
    record.payload = {k.upper(): v for k, v in record.payload.items()}
    return record


def filter_nonzero(record: Record) -> Record:
    record.payload = {k: v for k, v in record.payload.items() if v != 0}
    return record


async def main():
    pipe = Pipeline(source_url="https://api.example.com/stream", batch_size=50)
    pipe.add_stage("uppercase", transform_uppercase)
    pipe.add_stage("filter", filter_nonzero)
    records = await pipe.run(max_records=200)
    print(f"Processed {len(records)} records")


if __name__ == "__main__":
    asyncio.run(main())
