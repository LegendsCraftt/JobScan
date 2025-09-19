# main.py  —  test harness with updater UI inlined
import sys, json, pathlib, tempfile, multiprocessing, contextlib

from PyQt6.QtWidgets import QApplication

from UI.ui import MainUI

# --- updater pieces from your model.update / model.update_ui ---
from model.update import (
    apply_pending_update_if_any,     # applies deferred installer then exits
    check_latest_against_current,    # -> {"name","url","version"} or None
    download_installer_with_progress,# streams with % callback
    run_installer_silent,            # runs Inno (/VERYSILENT ...) or MSI
    APPDATA, MARKER,                 # %LOCALAPPDATA%\JobScan\pending_update.json
)
from UI.update_ui import UpdateUI, DownloadWorker


def main():
    with contextlib.suppress(SystemExit):
        apply_pending_update_if_any()

    app = QApplication(sys.argv)

    try:
        info = check_latest_against_current()  # dict or None
    except Exception as e:
        print(f"[Update] Check failed: {e}")
        info = None

    if info:
        tmp_path = str(pathlib.Path(tempfile.gettempdir()) / info["name"])
        dlg = UpdateUI(title="JobScan Update")
        worker = DownloadWorker(info["url"], tmp_path, download_installer_with_progress)
        dlg.bind_worker(worker)

        def restart_now(installer_path: str):
            run_installer_silent(installer_path)
            sys.exit(0)

        def restart_later(installer_path: str):
            APPDATA.mkdir(parents=True, exist_ok=True)
            MARKER.write_text(json.dumps({"installer_path": installer_path}), encoding="utf-8")


        dlg.on_restart_now_clicked(restart_now)
        dlg.on_restart_later_clicked(restart_later)
        dlg.exec()

    # 4) Launch your app normally
    window = MainUI()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
