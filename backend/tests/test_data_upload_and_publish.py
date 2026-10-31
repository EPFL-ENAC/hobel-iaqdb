"""The data upload's dry run and the publish background load, on the fixture files."""

import asyncio
import json
import shutil
import sys
import zipfile
from pathlib import Path

import pytest
from api.models.catalog import Dataset, StudyDraft
from api.scripts import data_upload
from api.services import publish
from api.services.catalog_version import CatalogVersionService
from api.services.parameter import read_parameters
from sqlalchemy import text
from tests.fixtures import D1_REPORT, d1_rows, make_catalog, write_csv


def upload_folder(tmp_path: Path, rows) -> Path:
    """An UPLOAD_DATA study folder: metadata.json plus one processed CSV whose
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


def test_data_upload_check_reports_every_bin(tmp_path: Path):
    from tests.fixtures import Fixture

    fx = Fixture(study_id=0, buildings={}, spaces={}, datasets={}, files={})
    folder = upload_folder(tmp_path, d1_rows(fx))
    study = data_upload.load_study(folder)
    lines = data_upload.check_measurements(study, read_parameters())
    assert len(lines) == 1
    line = lines[0]
    assert line.startswith("D1: loaded ")
    assert f"missing {D1_REPORT['missing']}" in line
    assert "unknown parameter 1 (1 slugs)" in line
    assert "unknown unit 1 (co2|mg/m³)" in line
    assert "unparseable timestamp 2" in line
    assert "unlinked space 1" in line


def test_data_upload_skips_csv_that_is_not_processed(tmp_path: Path):
    from tests.fixtures import Fixture

    fx = Fixture(study_id=0, buildings={}, spaces={}, datasets={}, files={})
    folder = upload_folder(tmp_path, d1_rows(fx))
    (folder / "META").mkdir()
    (folder / "META" / "home.csv").write_text("ID,Country\nH01,Ireland\n")
    study = data_upload.load_study(folder)
    assert [d.name for d, _ in study.dataset_files] == ["D1"]
    assert study.warnings == ["META/home.csv skipped: no `source_outer_file` column"]


def test_report_study_colors_only_on_a_terminal(tmp_path: Path, capsys, monkeypatch):
    from tests.fixtures import Fixture

    fx = Fixture(study_id=0, buildings={}, spaces={}, datasets={}, files={})
    study = data_upload.load_study(upload_folder(tmp_path, d1_rows(fx)))

    data_upload.report_study(study, data_upload.Outcome())
    assert capsys.readouterr().out.startswith("    ok: ")

    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
    data_upload.report_study(study, data_upload.Outcome())
    assert capsys.readouterr().out.startswith("\033[32m    ok: ")


def test_report_study_failed_dataset_is_red_and_not_ok(
    tmp_path: Path, capsys, monkeypatch
):
    from tests.fixtures import Fixture

    fx = Fixture(study_id=0, buildings={}, spaces={}, datasets={}, files={})
    study = data_upload.load_study(upload_folder(tmp_path, d1_rows(fx)))

    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
    data_upload.report_study(study, data_upload.Outcome(errors=["D1: boom"]))
    out = capsys.readouterr().out
    assert out == "\033[31m    FAILED D1: boom\033[0m\n"


def zip_csv(csv: Path, path: Path) -> Path:
    """A zip as macOS Finder makes it: the CSV in a sub-folder, plus
    `__MACOSX/` metadata entries that are not CSVs despite their name."""
    with zipfile.ZipFile(path, "w") as archive:
        archive.write(csv, f"series/{csv.name}")
        archive.writestr(f"__MACOSX/series/._{csv.name}", b"\x00\x05\x16\x07")
    return path


def test_data_upload_check_reads_zips(tmp_path: Path):
    from tests.fixtures import Fixture

    fx = Fixture(study_id=0, buildings={}, spaces={}, datasets={}, files={})
    folder = upload_folder(tmp_path, d1_rows(fx))
    csv = folder / "time_series" / "d1_long.csv"
    expected = data_upload.check_measurements(
        data_upload.load_study(folder), read_parameters()
    )
    zip_csv(csv, folder / "time_series" / "d1_long.zip")
    csv.unlink()
    study = data_upload.load_study(folder)
    assert data_upload.check_measurements(study, read_parameters()) == expected


async def test_publish_loads_zipped_csvs(session, clean_db, tmp_path, monkeypatch):
    fx = await make_catalog(session)
    local = zip_csv(
        write_csv(tmp_path / "d1_long.csv", d1_rows(fx)), tmp_path / "d1.zip"
    )
    empty = tmp_path / "empty.zip"
    zipfile.ZipFile(empty, "w").close()
    files = {"D1": local, "D2": empty}
    for name, path in files.items():
        dataset = await session.get(Dataset, fx.datasets[name])
        dataset.folder = {"children": [{"name": path.name, "path": f"k/{name}.zip"}]}
        session.add(dataset)
    await session.commit()

    async def fake_download(key: str, path: Path) -> Path:
        shutil.copy(files[key.removeprefix("k/").removesuffix(".zip")], path)
        return path

    monkeypatch.setattr(publish, "download_object", fake_download)
    with pytest.raises(RuntimeError, match="1 dataset\\(s\\) failed"):
        await publish.load_published_study(clean_db, fx.study_id)
    d1 = await session.get(Dataset, fx.datasets["D1"])
    await session.refresh(d1)
    assert d1.summary_status == "ready", d1.summary_error
    assert d1.load_report["loaded"] > 0
    assert d1.load_report["unlinked_space"] == D1_REPORT["unlinked_space"]
    d2 = await session.get(Dataset, fx.datasets["D2"])
    await session.refresh(d2)
    assert d2.summary_status == "failed"
    assert d2.summary_error == "ValueError: no CSV file in empty.zip"


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
    assert d2.load_started_at == d2.load_finished_at is not None
    hours = (await session.exec(text("SELECT count(*) FROM measurement_hour"))).scalar()
    assert hours > 0
    # the version is bumped once the aggregates are refreshed, even on failure
    assert await CatalogVersionService(session).get() == 2
    # the delete path leaves no stale aggregate rows behind
    await session.delete(dataset)
    await session.commit()
    await publish.refresh_after_delete(clean_db)
    hours = (await session.exec(text("SELECT count(*) FROM measurement_hour"))).scalar()
    assert hours == 0
    assert await CatalogVersionService(session).get() == 3


async def test_concurrent_publish_loads_are_serialized(
    session, clean_db, tmp_path, monkeypatch
):
    """Several publishes at once: their background loads must not interleave
    (DELETE/COPY/refresh/compress of one racing another's)."""
    fx = await make_catalog(session)
    local = write_csv(tmp_path / "d1_long.csv", d1_rows(fx))
    for name in ("D1", "D2"):
        dataset = await session.get(Dataset, fx.datasets[name])
        dataset.folder = {"children": [{"name": "d.csv", "path": f"k/{name}.csv"}]}
        session.add(dataset)
    await session.commit()

    async def fake_download(key: str, path: Path) -> Path:
        await asyncio.sleep(0)
        shutil.copy(local, path)
        return path

    monkeypatch.setattr(publish, "download_object", fake_download)
    await asyncio.gather(
        *(publish.load_published_study(clean_db, fx.study_id) for _ in range(4))
    )
    count = "SELECT count(*) FROM measurement WHERE dataset_id = :id"
    for name in ("D1", "D2"):
        dataset = await session.get(Dataset, fx.datasets[name])
        await session.refresh(dataset)
        assert dataset.summary_status == "ready", dataset.summary_error
        n = (await session.exec(text(count).bindparams(id=dataset.id))).scalar()
        assert n == dataset.load_report["loaded"] > 0


def test_csv_keys_unquote_and_filter():
    dataset = Dataset(
        name="D",
        description="d",
        folder={
            "children": [
                {"name": "a b.csv", "path": "p/a%20b.csv"},
                {"name": "x.zip", "path": "p/x.zip"},
                {"name": "raw.xlsx", "path": "p/raw.xlsx"},
            ]
        },
    )
    assert publish.csv_keys(dataset) == [
        ("p/a b.csv", "a b.csv"),
        ("p/x.zip", "x.zip"),
    ]
    assert publish.csv_keys(Dataset(name="D", description="d", folder=None)) == []
    assert json.dumps(D1_REPORT)  # the report is JSON serialisable
