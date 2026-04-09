"""End-to-end dbt smoke: isolated DuckDB + synthetic parquet (mirrors CI assumptions)."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

from finops_capex.generators import GenerationConfig, SyntheticBillingGenerator
from finops_capex.ingestion.lake_writer import write_raw_billing_batch

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def isolated_dbt_env(tmp_path: Path) -> dict[str, str]:
    """Point DuckDB at a fresh file under tmp_path; keep profiles in-repo."""

    warehouse_dir = tmp_path / "warehouse"
    warehouse_dir.mkdir(parents=True, exist_ok=True)
    db_file = warehouse_dir / "finops.duckdb"

    env = os.environ.copy()
    env["DBT_PROFILES_DIR"] = str((REPOSITORY_ROOT / "dbt").resolve())
    env["FINOPS_DUCKDB_PATH"] = db_file.as_posix()
    return env


def _run_dbt(
    *args: str,
    cwd: Path,
    env: dict[str, str],
    vars_payload: str,
) -> subprocess.CompletedProcess[str]:
    cmd = [
        "dbt",
        *args,
        "--project-dir",
        "dbt",
        "--vars",
        vars_payload,
    ]
    return subprocess.run(
        cmd,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.integration
def test_dbt_seed_run_test_against_synthetic_parquet(
    tmp_path: Path,
    isolated_dbt_env: dict[str, str],
) -> None:
    """Land a minimal parquet batch, then run the same dbt stages as CI."""

    generator = SyntheticBillingGenerator(GenerationConfig(days=14, seed=42))
    dataframe = generator.generate_dataframe()
    write_raw_billing_batch(
        dataframe=dataframe,
        repository_root=tmp_path,
        run_date="2026-04-06",
        output_format="parquet",
        sample_size=10,
    )

    raw_partition = tmp_path / "local_lake/raw/cloud_costs/run_date=*"
    raw_glob = (raw_partition / "cloud_cost_usage.parquet").as_posix()
    manifest_glob = (raw_partition / "manifest.json").as_posix()
    vars_payload = json.dumps(
        {
            "raw_cloud_cost_glob": raw_glob,
            "raw_manifest_glob": manifest_glob,
        }
    )

    for stage in ("seed", "run", "test"):
        result = _run_dbt(
            stage,
            cwd=REPOSITORY_ROOT,
            env=isolated_dbt_env,
            vars_payload=vars_payload,
        )
        if result.returncode != 0:
            pytest.fail(
                f"dbt {stage} failed (exit {result.returncode})\n"
                f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
            )
