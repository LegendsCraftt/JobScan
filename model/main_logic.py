import os
import re
import shutil
from pathlib import Path
from collections.abc import Iterable
from typing import Any

from model.SQL_logic import build_pkg_content_list

NC_drive = Path(r'\\mfcsa1\NC Files')
drawing_drive = Path(r'\\mfcsa1\Shop Drawings\Jobs')


def get_nc_job_folders(job_code: int):
    """Return NC job folders whose names start with the given job code."""
    job_prefix = str(job_code)
    try:
        return [
            folder for folder in NC_drive.iterdir()
            if folder.is_dir() and folder.name.startswith(job_prefix)
        ]
    except Exception as e:
        print(f"[ERROR] Failed to iterate NC drive: {e}")
        return []


def _safe_iterdir(path: Path):
    """Yield children of a directory, warning instead of raising on failure."""
    try:
        for p in path.iterdir():
            yield p
    except Exception as e:
        print(f"[WARN] iterdir failed: {path} :: {e}")


def _safe_walk(top: Path):
    """
    A safe, recursive generator similar to os.walk created in pain trying to debug errors :P
    """
    dirs, files = [], []
    try:
        with os.scandir(top) as it:
            for entry in it:
                try:
                    if entry.is_dir(follow_symlinks=False):
                        dirs.append(entry.path)
                    else:
                        files.append(entry.name)
                except Exception as e:
                    print(f"[WARN] stat failed: {entry.path} :: {e}")
    except Exception as e:
        print(f"[WARN] scandir failed: {top} :: {e}")
        return

    yield str(top), dirs, files
    for d in dirs:
        yield from _safe_walk(Path(d))


def find_all_files_for_marks(job_code: int, mainmarks: list[str], parts: list[str]):
    """
    Scan NC and Drawings drives for files matching provided marks.
    """
    try:
        print("Finding Files:")
        mm_set = {m.lower() for m in mainmarks}
        pt_set = {p.lower() for p in parts}

        # Return which bucket ("mainmark"/"part") AND the actual matched mark string.
        def match_type_and_mark(file: str) -> tuple[str, str] | None:
            stem = Path(file).stem.lower()
            for chunk in re.split(r"[-_ ]+", stem):
                if chunk in mm_set:
                    return ("mainmark", chunk)
                if chunk in pt_set:
                    return ("part", chunk)
            return None

        _pdf = {"mainmark": [], "part": []}
        _nc  = {"mainmark": [], "part": []}
        _dxf = {"mainmark": [], "part": []}
        _enc = []

        # Track which marks we actually found per category so we can compute "misses".
        found_marks = {
            "nc":  {"mainmark": set(), "part": set()},
            "dxf": {"mainmark": set(), "part": set()},
            "pdf": {"mainmark": set(), "part": set()},
        }

        # --- NC side ---
        print(f"[NC] Scanning drive")
        for folder in _safe_iterdir(NC_drive):
            try:
                if folder.is_dir() and folder.name.startswith(str(job_code)):
                    for root, dirs, files in _safe_walk(folder):
                        for file in files:
                            lower = file.lower()
                            filepath = os.path.join(root, file)

                            if lower.endswith(".enc"):
                                _enc.append(filepath)
                                continue

                            match = match_type_and_mark(file)
                            if not match:
                                continue
                            mtype, mark = match

                            if lower.endswith(".nc1"):
                                _nc[mtype].append(filepath)
                                found_marks["nc"][mtype].add(mark)
                            elif lower.endswith(".dxf"):
                                _dxf[mtype].append(filepath)
                                found_marks["dxf"][mtype].add(mark)
            except Exception as e:
                print(f"[WARN] NC folder skipped: {folder} :: {e}")

        # --- Drawing side ---
        print(f"[DRAWINGS] Scanning drive")
        job_prefix = str(job_code)
        for job_folder in _safe_iterdir(drawing_drive):
            try:
                if not (job_folder.is_dir() and job_folder.name.startswith(job_prefix)):
                    continue

                parts_dir = job_folder / "Drawings" / "Parts"
                fab_dir   = job_folder / "Drawings" / "Fabrication"

                for base in (parts_dir, fab_dir):
                    if not base.exists():
                        continue

                    for root, dirs, files in _safe_walk(base):
                        for file in files:
                            if not file.lower().endswith(".pdf"):
                                continue

                            match = match_type_and_mark(file)
                            if match:
                                mtype, mark = match
                                path = os.path.join(root, file)
                                _pdf[mtype].append(path)
                                found_marks["pdf"][mtype].add(mark)

            except Exception as e:
                print(f"[WARN] Job folder skipped: {job_folder} :: {e}")

        # ---- compute miss buckets (expected marks that had zero hits in each category) ----
        mm_all = set(mm_set)
        pt_all = set(pt_set)

        misses = {
            "nc": {
                "mainmark": sorted(mm_all - found_marks["nc"]["mainmark"]),
                "part":     sorted(pt_all - found_marks["nc"]["part"]),
            },
            "dxf": {
                "mainmark": sorted(mm_all - found_marks["dxf"]["mainmark"]),
                "part":     sorted(pt_all - found_marks["dxf"]["part"]),
            },
            "pdf": {
                "mainmark": sorted(mm_all - found_marks["pdf"]["mainmark"]),
                "part":     sorted(pt_all - found_marks["pdf"]["part"]),
            },
        }

        return {
            "nc":  {k: sorted(v) for k, v in _nc.items()},
            "dxf": {k: sorted(v) for k, v in _dxf.items()},
            "enc": sorted(_enc),
            "pdf": {k: sorted(v) for k, v in _pdf.items()},
            "misses": misses,
        }
    except Exception as e:
        print(f"[ERROR] Failed to gather files: {e}")
        return {
            "nc": {"mainmark": [], "part": []},
            "dxf": {"mainmark": [], "part": []},
            "enc": [],
            "pdf": {"mainmark": [], "part": []},
            "misses": {"nc": {"mainmark": [], "part": []},
                       "dxf": {"mainmark": [], "part": []},
                       "pdf": {"mainmark": [], "part": []}}
        }


def check_for_misses(found_report):
    misses = found_report.get("misses") or {}
    total_misses = sum(
        len(misses.get(cat, {}).get(kind, []))
        for cat in ("nc", "dxf", "pdf")
        for kind in ("mainmark", "part")
    )
    if total_misses > 0:
        print(f"[WARN] {total_misses} files were not found.")
        return misses
    return {}

def sort_to_dirs(types: list[str], all_files: dict[str, Any], output_root: Path = Path("files"), overwrite: bool = False):
    """
    Copy discovered files into an output folder structure.
    Only creates subfolders when there are files to copy.
    Honors `overwrite` flag to control replacement of existing files.
    """
    print(f"[sort_to_dirs] Copying to: {output_root} | Overwrite: {overwrite}")
    output_root.mkdir(parents=True, exist_ok=True)

    def has_files(group: Any) -> bool:
        """True only if group is a non-empty iterable (and not a str/bytes)."""
        if group is None:
            return False
        if isinstance(group, (str, bytes)):
            return False
        try:
            return len(group) > 0
        except TypeError:
            if isinstance(group, Iterable):
                for _ in group:
                    return True
            return False

    def copy_group(file_list: Iterable, subdir: str) -> None:
        if isinstance(file_list, dict):
            print(f"[WARNING] Expected list of paths, got dict for {subdir}; skipping.")
            return

        target_dir = output_root / subdir
        target_dir.mkdir(parents=True, exist_ok=True)

        for path in file_list:
            p = Path(path)
            if not p.exists():
                print(f"[WARNING] File {p} does not exist")
                continue

            dest = target_dir / p.name
            if dest.exists() and not overwrite:
                print(f"[SKIP] File exists and overwrite is False: {dest}")
                continue

            try:
                shutil.copy2(p, dest)  # preserve mtime/metadata
            except Exception as e:
                print(f"[ERROR] Failed to copy {p}: {e}")

    def maybe_copy(group: Any, dest: str) -> bool:
        if has_files(group):
            copy_group(group, dest)
            return True
        return False

    # --- NC ---
    if "NC" in types:
        nc = all_files.get("nc") or {}
        maybe_copy(nc.get("part"), "NC/PARTS")
        maybe_copy(nc.get("mainmark"), "NC/ASSEMBLIES")

    # --- DXF ---
    if "DXF" in types:
        dxf = all_files.get("dxf") or {}
        maybe_copy(dxf.get("part"), "DXF/PARTS")
        maybe_copy(dxf.get("mainmark"), "DXF/ASSEMBLIES")

    # --- ENC ---
    if "ENC" in types:
        enc = all_files.get("enc")
        maybe_copy(enc, "ENC")

    # --- PDF: PART / ASSEMBLY ---
    if "PART" in types:
        maybe_copy(all_files.get("pdf", {}).get("part"), "PDF/PARTS")

    if "ASSEMBLY" in types:
        maybe_copy(all_files.get("pdf", {}).get("mainmark"), "PDF/ASSEMBLIES")

    print("[sort_to_dirs] Complete")


