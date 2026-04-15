import asyncio

from src.pipeline import Pipeline, Record, filter_nonzero, transform_uppercase


def test_record_creation():
    r = Record(id="a", payload={"x": 1})
    assert r.id == "a"
    assert r.payload == {"x": 1}


def test_transform_uppercase():
    r = Record(id="a", payload={"foo": 1, "bar": 2})
    out = transform_uppercase(r)
    assert out.payload == {"FOO": 1, "BAR": 2}


def test_filter_nonzero():
    r = Record(id="a", payload={"x": 0, "y": 3})
    out = filter_nonzero(r)
    assert out.payload == {"y": 3}


def test_pipeline_end_to_end():
    pipe = Pipeline(source_url="https://example.com", batch_size=5)
    pipe.add_stage("upper", transform_uppercase)
    records = asyncio.run(pipe.run(max_records=10))
    assert len(records) == 10
