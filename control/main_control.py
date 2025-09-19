import re
import shutil
import webbrowser
import zipfile
from datetime import time as pytime
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QThreadPool, Qt, QThread, QUrl, QPoint, QSize
from PyQt6.QtWidgets import QFileDialog, QMessageBox, QMenu, QToolTip
from PyQt6.QtGui import QDesktopServices, QAction, QIcon, QPixmap, QPainter, QPainterPath

from UI.about import AboutWindow
from UI.help import HelpWindow
from control.auth_controller import AuthState
from control.profile_service import get_profile, get_photo
from model.graph_logic import acquire_token
from model.main_logic import find_all_files_for_marks, check_for_misses
from model.SQL_logic import build_pkg_content_list
from model.reports import write_miss_report
from model.settings import SETTINGS
from workers.email_worker import EmailWorker
from workers.scan_worker import ScanWorker
from workers.token_worker import TokenWorker

from control.status_manager import StatusManager

from UI.styles_l import style as style_L
from UI.styles_d import style as style_D


class MainControl:
    """Main controller for JobScan UI actions and threading orchestration."""

    # =========================================================
    # Lifecycle
    # =========================================================
    def __init__(self, view):
        self.view = view
        self.threadpool = QThreadPool()
        self._workers = set()

        # strong refs for QThread/QObject
        self._scan_thread = None
        self._scan_worker = None

        self.status = StatusManager(self.view.status_label, self._base_status)

        self.view.overwrite = self.view.preferences_panel.overwrite_check.isChecked()
        self.view.version = (
            'new' if self.view.preferences_panel.outlook_new_check.isChecked()
                    else 'old')

    # =========================================================
    # Menu Functions
    # =========================================================


    def about(self):
        self.about_window = AboutWindow(self.view.style, self.view)
        self.about_window.show()


    def _theme_toggle(self, theme):
        if theme == 'dark':
            self.view.setStyleSheet(style_L)
            self.view.style = 'light'
            SETTINGS.setValue("theme", 'light')
            print('Stylesheet Set: Light Mode')
        else:
            self.view.setStyleSheet(style_D)
            self.view.style = 'dark'
            SETTINGS.setValue("theme", 'dark')
            print('Stylesheet Set: Dark Mode')

    def outlook__new_ui_handler(self):
        if self.view.preferences_panel.outlook_new_check.isChecked():
            self.view.preferences_panel.outlook_old_check.setChecked(False)
            self.view.version = 'new'
            SETTINGS.setValue("emailVersion", "new")

            print(f'[Controller] Email version set to: {self.view.version}')
            self.status.show("Email version set to: " + self.view.version)

    def outlook__old_ui_handler(self):
        if self.view.preferences_panel.outlook_old_check.isChecked():
            self.view.preferences_panel.outlook_new_check.setChecked(False)
            self.view.version = 'old'
            SETTINGS.setValue("emailVersion", "old")
            print(f'[Controller] Email version set to: {self.view.version}')
            self.status.show("Email version set to: " + self.view.version)


    def overwrite_handler(self):
        if self.view.preferences_panel.overwrite_check.isChecked():
            self.view.preferences_panel.overwrite_check.setChecked(True)
            self.view.overwrite = True
            SETTINGS.setValue("overwrite", True)
            print('Overwrite set to: True')
        else:
            self.view.preferences_panel.overwrite_check.setChecked(False)
            self.view.overwrite = False
            SETTINGS.setValue("overwrite", False)
            print('Overwrite set to: False')



    # =========================================================
    # UI Handlers (signals/slots)
    # =========================================================
    def handle_package_change(self, _=None):
        """Enable/disable scan button based on inputs and set status."""

        job_raw = self.view.job_code_input.text()
        job_clean = re.sub(r"\D", "", job_raw)  # strip non-digits

        if job_raw != job_clean:
            cursor_pos = self.view.job_code_input.cursorPosition()
            self.view.job_code_input.setText(job_clean)
            self.view.job_code_input.setCursorPosition(min(cursor_pos - 1, len(job_clean)))

        job_ok = bool(job_clean)
        pkg_ok = bool(self.view.package_input.text().strip())

        if job_ok and pkg_ok:
            self.view.scan_btn.setEnabled(True)
        elif job_ok:
            self.view.scan_btn.setEnabled(False)
        else:
            self.view.scan_btn.setEnabled(False)
    #
    # def handle_status_change(self):
    #     pytime.sleep(5)
    #     self.view.status_label.setText("Ready.")

    def handle_select_all(self, checked: bool):
        """Toggle all child checkboxes to match 'Select all'."""
        for cb in self.view.get_checkboxes():
            old = cb.blockSignals(True)
            cb.setChecked(checked)
            cb.blockSignals(old)

    def handle_child_checkbox_toggle(self):
        """Mirror child checkbox state on 'Select all'."""
        all_checked = all(cb.isChecked() for cb in self.view.get_checkboxes())
        old = self.view.select_all.blockSignals(True)
        self.view.select_all.setChecked(all_checked)
        self.view.select_all.blockSignals(old)

    def handle_scan_click(self):
        """Validate selection and kick off scan."""
        pkg = self.view.package_input.text().strip()
        targets = self.view.get_selected_targets()
        pkg_pattern = re.compile(r'^(SUB|PKG)#\d+$', re.IGNORECASE)

        if not targets:
            self.status.show("Select at least one type of file to export.")
            return

        if not pkg_pattern.match(pkg):
            self.view.scan_btn.setEnabled(False)
            self.view.package_input.setFocus()
            self.view.package_input.selectAll()
            self.showInvalidTooltip('pkg_input')
            return

        self.status.show(f"Scanning {pkg} → {', '.join(targets)}…")
        self.scan()

    def browse_outpath(self):
        prior = self.view.output_path_input.text().strip()
        start_dir = prior or str(Path.home() / "Desktop")
        chosen = QFileDialog.getExistingDirectory(self.view, "Select Output Folder", start_dir)
        if chosen:
            self.view.output_path_input.setText(chosen)
            SETTINGS.setValue("outputPath", chosen)
            recent = SETTINGS.value("recentPaths", [], type=list) or []
            recent = [p for p in recent if p != chosen]
            recent.insert(0, chosen)
            SETTINGS.setValue("recentPaths", recent[:6])
            self.status.show("Output folder saved.")
            self.view.status_label.setProperty("state", "ok")

    def show_outpath_menu(self, pos: QPoint) -> None:
        menu: QMenu = self.view.output_path_input.createStandardContextMenu()
        menu.addSeparator()

        choose_action = QAction("Choose Folder…", self.view)
        choose_action.triggered.connect(self.browse_outpath)
        menu.addAction(choose_action)

        clear_action = QAction("Clear Saved Path", self.view)
        clear_action.triggered.connect(self._clear_saved_outpath)
        clear_action.setEnabled(bool(self.view.output_path_input.text().strip()))  # <- trim
        clear_action.setShortcut("Ctrl+Alt+X")
        menu.addAction(clear_action)

        recent = SETTINGS.value("recentPaths", [], type=list) or []
        if recent:
            recent_menu = menu.addMenu("Recent")
            for path in recent:
                act = QAction(path, self.view)
                # correct lambda capture
                act.triggered.connect(lambda _, p=path: self._apply_outpath_from_recent(p))
                recent_menu.addAction(act)

        menu.exec(self.view.output_path_input.mapToGlobal(pos))

    def help(self):
        help_window = HelpWindow(self.view.style, self.view)
        help_window.show()

    def showInvalidTooltip(self, location: str = 'job_code_input'):
        if location == 'pkg_input':
            pos = self.view.package_input.mapToGlobal(
                QPoint(0, self.view.package_input.height() - 100)
            )
            QToolTip.showText(
                pos,
                "Package must be in the format SUB#1234 or PKG#1234",
                self.view.job_code_input,
                self.view.job_code_input.rect(),
                3200
            )


        if location == 'job_code_input':
            pos = self.view.job_code_input.mapToGlobal(
                QPoint(0, self.view.job_code_input.height() - 100)
            )
            QToolTip.showText(
                pos,
                "Only whole numbers allowed",
                self.view.job_code_input,
                self.view.job_code_input.rect(),
                1325
            )


        else: return



    def handle_email_toggle(self, checked: bool):
        turning_on = not checked  # your QToggle has checked==OFF

        def _revert_off():
            old = self.view.email_toggle.blockSignals(True)
            self.view.email_toggle.setChecked(True)  # True == OFF
            self.view.email_toggle.blockSignals(old)
            self.view.send_email = False
            SETTINGS.setValue("sendEmail", False)
            self.status.show("Email attachments disabled.")

        if not turning_on:
            # Turning OFF: do it immediately.
            self.view.send_email = False
            SETTINGS.setValue("sendEmail", False)
            self.status.show("Email attachments disabled.")
            return

        # Turning ON: keep UI responsive
        self.status.show("Checking sign-in…")

        # --- SILENT phase ---
        self._tok_thread = QThread(self.view)
        self._tok_worker = TokenWorker(interactive=False)
        self._tok_worker.moveToThread(self._tok_thread)

        def _silent_done(tok: str):
            self._tok_thread.quit()

            if tok:
                # Success quickly
                self.view.auth.refresh_profile(tok, repaint=True)
                self.view.send_email = True
                SETTINGS.setValue("sendEmail", True)
                self.status.show("Email attachments enabled.")
                self.view.email_toggle.setEnabled(True)
                return

            # No silent token → ask once
            ask = QMessageBox.question(
                self.view, "Sign in required",
                "You need to sign in to attach exports to an email.\nSign in now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if ask != QMessageBox.StandardButton.Yes:
                _revert_off()
                self.view.email_toggle.setEnabled(True)
                return

            # --- INTERACTIVE phase ---
            self.status.show("Opening sign-in…")
            self._tok_thread2 = QThread(self.view)
            self._tok_worker2 = TokenWorker(interactive=True)
            self._tok_worker2.moveToThread(self._tok_thread2)

            def _interactive_done(tok2: str):
                self._tok_thread2.quit()
                if tok2:
                    self.view.auth.refresh_profile(tok2, repaint=True)
                    self.view.send_email = True
                    SETTINGS.setValue("sendEmail", True)
                    self.status.show("Email attachments enabled.")
                else:
                    _revert_off()
                    self.status.show("Email attachments require sign-in.")
                self.view.email_toggle.setEnabled(True)

            def _interactive_err(msg: str):
                self._tok_thread2.quit()
                _revert_off()
                self._show_popout('Sign in error', msg, 'warning')
                self.view.email_toggle.setEnabled(True)

            self._tok_thread2.started.connect(self._tok_worker2.run)
            self._tok_worker2.finished.connect(_interactive_done)
            self._tok_worker2.error.connect(_interactive_err)
            self._tok_thread2.finished.connect(self._tok_worker2.deleteLater)
            self._tok_thread2.finished.connect(self._tok_thread2.deleteLater)
            self._tok_thread2.start()

        def _silent_err(msg: str):
            # Treat any silent error like "no token" and fall back to the prompt path
            _silent_done("")

        self._tok_thread.started.connect(self._tok_worker.run)
        self._tok_worker.finished.connect(_silent_done)
        self._tok_worker.error.connect(_silent_err)
        self._tok_thread.finished.connect(self._tok_worker.deleteLater)
        self._tok_thread.finished.connect(self._tok_thread.deleteLater)
        self._tok_thread.start()

    def handle_email(self, attachment_path: Path):

        token = self.view.auth.get_access_token(interactive=False)

        if not token:
            ask = QMessageBox.question(self.view, "No Access Token",
                                       "No access token found. Would you like to sign in?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                                       )

            if ask == QMessageBox.StandardButton.Yes:
                token = self.view.auth.get_access_token(interactive=True)

            if not token:
                QMessageBox.warning(self.view, "Email Error", "No account found. \nExiting.")
                return

        self.status.show("Opening email draft…")

        self._email_thread = QThread(self.view)
        self._email_worker = EmailWorker(self.view.version, Path(attachment_path), token)
        self._email_worker.moveToThread(self._email_thread)

        self._email_thread.started.connect(self._email_worker.run)

        def _on_finished(msg: str):
            self._show_popout('JobScan Email', 'Email Opened Successfully', 'info')
            self.status.show("Ready.")
            self._email_thread.quit()

        def _on_error(msg: str):
            self._show_popout('Email Error', msg, 'critical')
            self.status.show("Ready.")
            self._email_thread.quit()

        self._email_worker.finished.connect(_on_finished)
        self._email_worker.error.connect(_on_error)

        self._email_thread.finished.connect(self._email_worker.deleteLater)
        self._email_thread.finished.connect(self._email_thread.deleteLater)

        # Start
        self._email_thread.start()

    # =========================================================
    # Main pipeline
    # =========================================================
    def scan(self):
        """Parse inputs, fetch SQL data, discover files, and start worker thread."""
        job_code_str = self.view.job_code_input.text().strip()
        package = self.view.package_input.text().strip().upper()

        out_text = self.view.output_path_input.text().strip()
        base = Path(out_text) if out_text else (Path.home() / "Desktop" / "JobScan Exports")
        try:
            base.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self.status.show(f"Cannot create output folder: {e}")
            return

        self.export_root = base / f"{job_code_str} - {self._sanitize(package)}"

        targets = self.view.get_selected_targets()

        print(f"job_code: {job_code_str}")
        print(f"package: {package}")
        print(f"output_path: {self.export_root}")
        print(f"targets: {targets}")

        try:
            job_code = int(job_code_str)
        except ValueError:
            self.status.show("Invalid job code. Must be a number.")
            return

        self.status.show("Loading package data…")
        try:
            mainmarks, parts = build_pkg_content_list(job_code, package)

            if not mainmarks and not parts:
                self.status.show("No marks found for this package.")
                self._show_popout('No Marks Found', f'No marks found for package {package}.', 'warning')
                return

            for mark in mainmarks:
                self.status.show(f'Found: {mark}')
            for part in parts:
                self.status.show(f'Found: {part}')
        except Exception as e:
            self.status.show(f"[SQL Error] {e}")
            return
        print("[MainThread] SQL data loaded successfully")

        all_files = find_all_files_for_marks(job_code, mainmarks, parts)
        print("[MainThread] Files found", all_files)

        if getattr(self, "_scan_thread", None) and self._scan_thread.isRunning():
            self.status.show("Scan already in progress…")
            return

        self._scan_thread = QThread(self.view)
        self._scan_worker = ScanWorker(targets, self.export_root, all_files, overwrite=self.view.overwrite)
        self._scan_worker.moveToThread(self._scan_thread)
        print("[ScanWorker] Worker moved to thread")

        self._scan_thread.started.connect(self._scan_worker.run)
        self._scan_thread.finished.connect(self._scan_thread.deleteLater)

        self._scan_worker.finished.connect(self._scan_thread.quit)
        self._scan_worker.finished.connect(self._scan_worker.deleteLater)
        self._scan_worker.error.connect(self._scan_thread.quit)
        self._scan_worker.error.connect(self._scan_worker.deleteLater)

        self._scan_worker.finished.connect(self.status.show)
        self._scan_worker.error.connect(self.status.show)

        def _cleanup():
            print("[ScanWorker] Cleanup")
            self._scan_thread = None
            self._scan_worker = None

        self._scan_worker.finished.connect(self._post_scan_final)
        self._scan_thread.finished.connect(_cleanup)

        self._scan_thread.start()
        print("[ScanWorker] Thread started")

    # =========================================================
    # File operations
    # =========================================================
    def open_content(self):
        path = Path(self.export_root)
        if not path.exists():
            self.status.show(f"Folder does not exist: {path}")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def zip_content(self, path: Optional[Path] = None, overwrite: bool = False):
        if path is None:
            print("[Controller] No path to zip (None)")
            return

        path = Path(path)

        if not path.exists():
            print(f"[Controller] Path does not exist: {path}")
            return

        if path.is_dir():
            target_zip = path / f"{path.name}.zip"
            tmp_zip = path.parent / f"{path.name}.zip"
            base_name = str(tmp_zip.with_suffix(""))

        else:
            target_zip = path.parent / f"{path.stem}.zip"
            tmp_zip = target_zip
            base_name = str(tmp_zip.with_suffix(""))

        if target_zip.exists():
            if overwrite:
                print("[Controller] Target zip exists; removing before writing")

                try:
                    target_zip.unlink()

                except Exception as e:
                    print(f"[Controller] Could not remove existing target zip: {e}")
                    return

            else:
                print("[Controller] Zip file already exists (overwrite=False); skipping")
                return target_zip

        if tmp_zip.exists():
            if overwrite:
                try:
                    tmp_zip.unlink()

                except Exception as e:
                    print(f"[Controller] Could not remove existing temp zip: {e}")
                    return

            else:
                print("[Controller] Temp zip already exists (overwrite=False); skipping")
                return

        try:
            if path.is_dir():
                shutil.make_archive(
                    base_name,
                    "zip",
                    root_dir=str(path.parent),
                    base_dir=str(path.name),
                )

                try:
                    tmp_zip.replace(target_zip)

                except Exception:
                    shutil.move(str(tmp_zip), str(target_zip))

            else:
                with zipfile.ZipFile(tmp_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                    zf.write(path, arcname=path.name)

            print(f"[Controller] Zipped to: {target_zip}")
            return target_zip

        except Exception as e:
            print(f"[Controller] Zip failed: {e}")

            try:
                if tmp_zip.exists() and tmp_zip != target_zip:
                    tmp_zip.unlink()

            except Exception:
                pass
            return

    # =========================================================
    # Persistence / context-menu helpers (private)
    # =========================================================
    def _persist_output_path(self):
        path = self.view.output_path_input.text().strip()
        SETTINGS.setValue("outputPath", path)

    def _clear_saved_outpath(self):
        self.view.output_path_input.setText("")
        SETTINGS.setValue("outputPath", "")
        self.status.show("Output folder cleared.")
        self.view.status_label.setProperty("state", "info")

    def _apply_outpath_from_recent(self, path: str):
        p = Path(path)
        if not p.exists():
            self.status.show("Saved folder not found. Removing from Recents.")
            recent = SETTINGS.value("recentPaths", [], type=list) or []
            recent = [x for x in recent if x != path]
            SETTINGS.setValue("recentPaths", recent)
            return

        self.view.output_path_input.setText(path)
        SETTINGS.setValue("outputPath", path)

        # move to front
        recent = SETTINGS.value("recentPaths", [], type=list) or []
        recent = [x for x in recent if x != path]
        recent.insert(0, path)
        SETTINGS.setValue("recentPaths", recent)

        self.status.show("Output folder set from Recents.")
        self.view.status_label.setProperty("state", "ok")

    def set_theme(self, theme: str):
        if theme == 'light':
            self.view.setStyleSheet(style_L)
            self.view.style = 'light'
            SETTINGS.setValue("theme", 'light')
            print('Stylesheet Set: Light Mode')
        else:
            self.view.setStyleSheet(style_D)
            self.view.style = 'dark'
            SETTINGS.setValue("theme", 'dark')
            print('Stylesheet Set: Dark Mode')
    # =========================================================
    # Profile helpers
    # =========================================================

    def render_auth(self, state: AuthState):
        btn = self.view.sign_in_button

        if state.signed_in:
            # avatar/menu
            btn.setMenu(self._account_menu(state))
            if state.photo_pixmap:
                btn.setText("")
                btn.setIcon(QIcon(self._circular_pixmap(state.photo_pixmap)))
                btn.setIconSize(QSize(28, 28))
                btn.setText(self.get_initials(state.display_name))
            else:
                btn.setIcon(QIcon())
                btn.setText('    ' + self.get_initials(state.display_name))

            self.view.email_toggle.setToolTip("")
            btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        else:
            btn.setMenu(None)
            btn.setIcon(QIcon())
            btn.setText("Sign in")

            self.view.email_toggle.setChecked(True)

            self.view.send_email = False
            SETTINGS.setValue("sendEmail", False)
            self.view.email_toggle.setToolTip("Sign in to enable email attachments")
            self.view.email_toggle.setChecked(True)

    def _account_menu(self, state: AuthState) -> QMenu:
        m = QMenu(self.view)
        hdr = QAction(f"{state.display_name}  •  {state.email}", self.view)
        hdr.triggered.connect(lambda: webbrowser.open(f"https://www.microsoft.com/en-us/microsoft-365"))
        m.addAction(hdr)
        m.addSeparator()
        signout = QAction("Sign out", self.view)
        signout.triggered.connect(self.view.auth.sign_out_clicked)
        m.addAction(signout)
        return m

    def get_initials(self, name_or_email: str) -> str:
        t = (name_or_email or "").strip()
        if "@" in t and " " not in t:
            return (t[0] + t.split("@")[0][-1]).upper()
        parts = [p for p in t.split() if p]
        if not parts: return "U"
        if len(parts) == 1: return parts[0][0:1].upper()
        return (parts[0][0] + parts[-1][0]).upper()



    # =========================================================
    # Internal helpers
    # =========================================================
    def _sanitize(self, name: str) -> str:
        return re.sub(r'[<>:"/\\|?*]', '-', name).strip()

    def _show_popout(self, title: str, msg: str, msg_type: str = 'info'):
        if msg_type == 'info':
            QMessageBox.information(self.view, title, msg)
        elif msg_type == 'warning':
            QMessageBox.warning(self.view, title, msg)
        elif msg_type == 'critical':
            QMessageBox.critical(self.view, title, msg)
        else:
            QMessageBox.information(self.view, title, msg)

    def _base_status(self):
        job_ok = bool(self.view.job_code_input.text().strip())
        pkg_ok = bool(self.view.package_input.text().strip())
        if job_ok and pkg_ok: return "Ready."
        if job_ok: return "Enter a package to begin."
        return "Enter a job code to begin."

    def _circular_pixmap(self, src: QPixmap, size: int = 28) -> QPixmap:
        src = src.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                         Qt.TransformationMode.SmoothTransformation)
        result = QPixmap(size, size)
        result.fill(Qt.GlobalColor.transparent)

        painter = QPainter(result)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addEllipse(0, 0, size, size)
        painter.setClipPath(path)
        painter.drawPixmap(0, 0, src)
        painter.end()
        return result


    # =========================================================
    # Post-scan finalize
    # =========================================================
    def _post_scan_final(self, *_):
        self.open_content()

        zip_path = self.zip_content(self.export_root, overwrite=self.view.overwrite)
        if zip_path:
            if self.view.overwrite:
                self._show_popout('Scan Complete', f'Scan complete. Exported to: {self.export_root}\n\n'
                                                   f'Overwrote existing files.', 'info')
            else:
                self._show_popout('Scan Complete', f'Scan complete. Exported to: {self.export_root}\n')

            if self.view.send_email:
                self.handle_email(zip_path)
