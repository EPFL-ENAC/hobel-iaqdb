"""The seed's dry run and the publish background load, on the fixture files."""

import json
import shutil
from pathlib import Path

import pytest
from api.models.catalog import Dataset, StudyDraft
from api.scripts import seed
from api.services import publish
from api.services.measurement import MeasurementService
from api.services.parameter import read_parameters
from sqlalchemy import text
from tests.fixtures import D1_REPORT, d1_rows, make_catalog, write_csv


def seed_folder(tmp_path: Path, rows) -> Path:
    """A SEED_DATA study folder: metadata.json plus one processed CSV whose
    `source_outer_file` names the dataset's uploaded file."""
    folder = tmp_path / "study-a"
    (folder / "time_series").mkdir(parents=True)
    draft = StudyDraft(
        identifier="study-a",
        name="Study A",
        buildings=[
            {"identifier": "B1", "spaces": [{"identifier": "S1"}, {"identifier": "S2"}]}
        ],
        instruments=[{"identifier": "I1"}],
        datasets=[
            {
                "name": "D1",
                "description": "d1",
                "folder": {
                    "name": "D1",
                    "path": "x",
                    "is_file": False,
                    "children": [{"name": "d1.csv", "path": "x/d1.csv"}],
                },
            }
        ],
    )
    (folder / "metadata.json").write_text(draft.model_dump_json())
    path = write_csv(folder / "time_series" / "d1_long.csv", rows)
    content = path.read_text().splitlines()
    header = content[0].split(",")
    index = header.index("source_outer_file")
    fixed = [content[0]] + [
        ",".join(v if i != index else "d1.csv" for i, v in enumerate(line.split(",")))
        for line in content[1:]
    ]
    path.write_text("\n".join(fixed) + "\n")
    return folder


def test_seed_check_reports_every_bin(tmp_path: Path):
    from tests.fixtures import Fixture

    fx = Fixture(study_id=0, buildings={}, spaces={}, datasets={}, files={})
    folder = seed_folder(tmp_path, d1_rows(fx))
    study = seed.load_study(folder)
    lines = seed.check_measurements(study, read_parameters())
    assert len(lines) == 1
    line = lines[0]
    assert line.startswith("D1: loaded ")
    assert f"missing {D1_REPORT['missing']}" in line
    assert "unknown parameter 1 (1 slugs)" in line
    assert "unknown unit 1 (co2|mg/m³)" in line
    assert "unparseable timestamp 2" in line
    assert "unlinked space 1" in line


async def test_publish_loads_from_s3_and_refreshes(
    session, clean_db, tmp_path, monkeypatch
):
    fx = await make_catalog(session)
    rows = d1_rows(fx)
    local = write_csv(tmp_path / "d1_long.csv", rows)
    dataset = await session.get(Dataset, fx.datasets["D1"])
    dataset.folder = {
        "name": "D1",
        "path": "iaqdb/test/pub/study-a/files/D1",
        "is_file": False,
        "children": [
            {
                "name": "d1_long.csv",
                "path": "iaqdb/test/pub/study-a/files/D1/d1_long.csv",
            },
            {"name": "raw.xlsx", "path": "iaqdb/test/pub/study-a/files/D1/raw.xlsx"},
        ],
    }
    session.add(dataset)
    await session.commit()
    downloaded = []

    async def fake_download(key: str, path: Path) -> Path:
        downloaded.append(key)
        shutil.copy(local, path)
        return path

    monkeypatch.setattr(publish, "download_object", fake_download)
    # D2 has no CSV: it fails visibly, D1 still loads
    with pytest.raises(RuntimeError, match="1 dataset\\(s\\) failed"):
        await publish.load_published_study(clean_db, fx.study_id)
    assert downloaded == ["iaqdb/test/pub/study-a/files/D1/d1_long.csv"]
    await session.refresh(dataset)
    assert dataset.summary_status == "ready"
    assert dataset.load_report["unlinked_space"] == 1
    d2 = await session.get(Dataset, fx.datasets["D2"])
    await session.refresh(d2)
    assert d2.summary_status == "failed"
    assert d2.summary_error == "no CSV file in the dataset folder"
    hours = (await session.exec(text("SELECT count(*) FROM measurement_hour"))).scalar()
    assert hours > 0
    # the delete path leaves no stale aggregate rows behind
    await session.delete(dataset)
    await session.commit()
    await MeasurementService(clean_db).refresh_all()
    hours = (await session.exec(text("SELECT count(*) FROM measurement_hour"))).scalar()
    assert hours == 0


def test_csv_keys_unquote_and_filter():
    dataset = Dataset(
        name="D",
        description="d",
        folder={
            "children": [
                {"name": "a b.csv", "path": "p/a%20b.csv"},
                {"name": "x.zip", "path": "p/x.zip"},
            ]
        },
    )
    assert publish.csv_keys(dataset) == [("p/a b.csv", "a b.csv")]
    assert publish.csv_keys(Dataset(name="D", description="d", folder=None)) == []
    assert json.dumps(D1_REPORT)  # the report is JSON serialisable
