#!/usr/bin/env python3
"""
ZZZ Bot Build GUI
=================
Tkinter GUI for the build process with persistent configuration.
Settings are saved to build_config.json and restored across sessions.
"""

import importlib.util
import json
import multiprocessing as mp
import os
import queue
import subprocess
import sys
import threading
from pathlib import Path
from typing import Callable, Optional
import tkinter as tk
from tkinter import ttk


# ============================================================
# Dynamic import of build.py CLI functions
# ============================================================
_build_spec = importlib.util.spec_from_file_location(
    "build_cli", Path(__file__).parent / "build.py"
)
_build_mod = importlib.util.module_from_spec(_build_spec)
_build_spec.loader.exec_module(_build_mod)

get_current_version = _build_mod.get_current_version
increment_version = _build_mod.increment_version
update_version_files = _build_mod.update_version_files
stop_conflicting_processes_for_bundle = _build_mod.stop_conflicting_processes_for_bundle


# ============================================================
# BuildConfig
# ============================================================
class BuildConfig:
    """
    Persistent build configuration backed by build_config.json.

    Loads defaults if the file is missing or corrupt. Saves on every build.
    """

    CONFIG_PATH = Path(__file__).parent / "build_config.json"
    DEFAULTS = {
        "increment_version": True,
        "custom_version": "",
        "parallel_prep": True,
        "auto_run_installer": True,
        "steps": {
            "frontend": True,
            "sidecar": True,
            "bundle": True,
        }
    }

    def __init__(self):
        self._data = self._load()

    def _load(self) -> dict:
        try:
            with open(self.CONFIG_PATH, "r") as f:
                data = json.load(f)
            merged = dict(self.DEFAULTS)
            merged.update(data)
            merged["steps"] = dict(self.DEFAULTS["steps"])
            merged["steps"].update(data.get("steps", {}))
            return merged
        except (FileNotFoundError, json.JSONDecodeError):
            return {
                "increment_version": self.DEFAULTS["increment_version"],
                "custom_version": self.DEFAULTS["custom_version"],
                "parallel_prep": self.DEFAULTS["parallel_prep"],
                "auto_run_installer": self.DEFAULTS["auto_run_installer"],
                "steps": dict(self.DEFAULTS["steps"]),
            }

    def save(self):
        with open(self.CONFIG_PATH, "w") as f:
            json.dump(self._data, f, indent=2)

    @property
    def increment_version_flag(self) -> bool:
        return self._data["increment_version"]

    @increment_version_flag.setter
    def increment_version_flag(self, value: bool):
        self._data["increment_version"] = value

    @property
    def custom_version(self) -> str:
        return self._data["custom_version"]

    @custom_version.setter
    def custom_version(self, value: str):
        self._data["custom_version"] = value

    @property
    def parallel_prep(self) -> bool:
        return self._data.get("parallel_prep", self.DEFAULTS["parallel_prep"])

    @parallel_prep.setter
    def parallel_prep(self, value: bool):
        self._data["parallel_prep"] = value

    @property
    def auto_run_installer(self) -> bool:
        return self._data.get(
            "auto_run_installer",
            self.DEFAULTS["auto_run_installer"],
        )

    @auto_run_installer.setter
    def auto_run_installer(self, value: bool):
        self._data["auto_run_installer"] = value

    def step_enabled(self, name: str) -> bool:
        return self._data["steps"].get(name, True)

    def set_step(self, name: str, value: bool):
        self._data["steps"][name] = value


# ============================================================
# Bundle/installer helpers
# ============================================================
def _collect_bundle_artifacts(root_dir: Path) -> list[Path]:
    """Return installer artifacts sorted by newest first."""
    bundle_dir = root_dir / "src-tauri" / "target" / "release" / "bundle"
    artifacts = sorted(bundle_dir.glob("nsis/*.exe")) + sorted(bundle_dir.glob("msi/*.msi"))
    return sorted(artifacts, key=lambda path: path.stat().st_mtime, reverse=True)


def _launch_installer(installer_path: Path) -> None:
    """Launch installer artifact with OS default handler."""
    if sys.platform == "win32":
        os.startfile(str(installer_path))
    else:
        subprocess.Popen([str(installer_path)], cwd=installer_path.parent)


def _parallel_step_worker(
    step_key: str,
    project_root: str,
    output_queue: "mp.Queue",
) -> None:
    """Run one prep step in a child process and stream logs to parent."""
    root_dir = Path(project_root)
    frontend_dir = root_dir / "frontend"
    binaries_dir = root_dir / "src-tauri" / "binaries"

    if not frontend_dir.exists():
        output_queue.put(("done", step_key, False, "Frontend directory not found"))
        return

    if step_key == "frontend":
        cmd = "bun run build"
    elif step_key == "sidecar":
        cmd = "bun run tauri:prepare-sidecar"
    else:
        output_queue.put(("done", step_key, False, f"Unknown step: {step_key}"))
        return

    output_queue.put(("info", step_key, f"Running: {cmd}"))
    try:
        proc = subprocess.Popen(
            cmd,
            cwd=frontend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
            text=True,
            shell=True,
        )
        assert proc.stdout is not None
        for line in proc.stdout:
            output_queue.put(("stdout", step_key, line.rstrip()))
        proc.wait()
        if proc.returncode != 0:
            output_queue.put(
                ("done", step_key, False, f"{step_key} exited with code {proc.returncode}")
            )
            return

        if step_key == "frontend":
            dist_dir = frontend_dir / "dist"
            if dist_dir.exists():
                output_queue.put(("success", step_key, f"Build output: {dist_dir}"))
            else:
                output_queue.put(("info", step_key, "Frontend completed but dist folder missing"))
        else:
            artifacts = sorted(binaries_dir.glob("zzz-backend-*.exe"))
            if artifacts:
                newest = artifacts[-1]
                size_mb = newest.stat().st_size / (1024 * 1024)
                output_queue.put(("success", step_key, f"Sidecar: {newest.name} ({size_mb:.1f} MB)"))
            else:
                output_queue.put(("done", step_key, False, "No sidecar binary found"))
                return

        output_queue.put(("done", step_key, True, "ok"))
    except Exception as exc:
        output_queue.put(("done", step_key, False, str(exc)))


# ============================================================
# Step factory functions
# ============================================================

def _make_frontend_step(q: queue.Queue, cancel: threading.Event) -> Callable[[], bool]:
    """Returns a callable that streams the React/Vite frontend build."""

    def run() -> bool:
        frontend_dir = Path(__file__).parent.parent / "frontend"
        if not frontend_dir.exists():
            q.put(("error", "Frontend directory not found!"))
            return False

        q.put(("info", "Running: bun run build"))
        try:
            proc = subprocess.Popen(
                "bun run build",
                cwd=frontend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1,
                text=True,
                shell=True,
            )
            for line in proc.stdout:
                if cancel.is_set():
                    proc.terminate()
                    return False
                q.put(("stdout", line.rstrip()))
            proc.wait()
            if proc.returncode != 0:
                return False
            dist_dir = frontend_dir / "dist"
            if dist_dir.exists():
                q.put(("success", f"Build output: {dist_dir}"))
            return True
        except Exception as e:
            q.put(("error", f"Frontend error: {e}"))
            return False

    return run


def _make_sidecar_step(q: queue.Queue, cancel: threading.Event) -> Callable[[], bool]:
    """Returns a callable that streams the Tauri sidecar preparation build."""

    def run() -> bool:
        frontend_dir = Path(__file__).parent.parent / "frontend"
        if not frontend_dir.exists():
            q.put(("error", "frontend directory not found!"))
            return False

        q.put(("info", "Running: bun run tauri:prepare-sidecar"))
        try:
            proc = subprocess.Popen(
                "bun run tauri:prepare-sidecar",
                cwd=frontend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1,
                text=True,
                shell=True,
            )
            for line in proc.stdout:
                if cancel.is_set():
                    proc.terminate()
                    return False
                q.put(("stdout", line.rstrip()))
            proc.wait()
            if proc.returncode != 0:
                return False

            binaries_dir = Path(__file__).parent.parent / "src-tauri" / "binaries"
            artifacts = sorted(binaries_dir.glob("zzz-backend-*.exe"))
            if artifacts:
                newest = artifacts[-1]
                size_mb = newest.stat().st_size / (1024 * 1024)
                q.put(("success", f"Sidecar: {newest.name} ({size_mb:.1f} MB)"))
            else:
                q.put(("error", "No sidecar binary found in src-tauri/binaries"))
                return False
            return True
        except Exception as e:
            q.put(("error", f"Sidecar error: {e}"))
            return False

    return run


def _make_parallel_prep_step(q: queue.Queue, cancel: threading.Event) -> Callable[[], bool]:
    """Run frontend and sidecar steps concurrently using multiprocessing."""

    def run() -> bool:
        root_dir = Path(__file__).parent.parent
        ctx = mp.get_context("spawn")
        mp_queue = ctx.Queue()

        processes = {
            "frontend": ctx.Process(
                target=_parallel_step_worker,
                args=("frontend", str(root_dir), mp_queue),
                daemon=True,
            ),
            "sidecar": ctx.Process(
                target=_parallel_step_worker,
                args=("sidecar", str(root_dir), mp_queue),
                daemon=True,
            ),
        }

        q.put(("info", "Running Frontend + Sidecar in parallel (multiprocessing)"))
        for process in processes.values():
            process.start()

        results: dict[str, bool] = {}
        try:
            while len(results) < len(processes):
                if cancel.is_set():
                    for process in processes.values():
                        if process.is_alive():
                            process.terminate()
                    return False

                try:
                    msg = mp_queue.get(timeout=0.2)
                except queue.Empty:
                    continue

                msg_type = msg[0]
                step_key = msg[1]
                prefix = "Frontend" if step_key == "frontend" else "Sidecar"

                if msg_type == "stdout":
                    q.put(("stdout", f"[{prefix}] {msg[2]}"))
                elif msg_type == "info":
                    q.put(("info", f"[{prefix}] {msg[2]}"))
                elif msg_type == "success":
                    q.put(("success", f"[{prefix}] {msg[2]}"))
                elif msg_type == "done":
                    success = bool(msg[2])
                    details = msg[3]
                    results[step_key] = success
                    if not success:
                        q.put(("error", f"[{prefix}] {details}"))
        finally:
            for process in processes.values():
                process.join(timeout=1)
                if process.is_alive():
                    process.terminate()
            mp_queue.close()
            mp_queue.join_thread()

        return all(results.values())

    return run


def _make_bundle_step(q: queue.Queue, cancel: threading.Event) -> Callable[[], bool]:
    """Returns a callable that streams the Tauri desktop bundle build."""

    def _run_tauri_build(root_dir: Path) -> bool:
        proc = subprocess.Popen(
            ["cargo", "tauri", "build"],
            cwd=root_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
            text=True,
        )
        for line in proc.stdout:
            if cancel.is_set():
                proc.terminate()
                return False
            q.put(("stdout", line.rstrip()))
        proc.wait()
        return proc.returncode == 0

    def run() -> bool:
        root_dir = Path(__file__).parent.parent
        q.put(("info", "Running: cargo tauri build"))
        try:
            stopped = stop_conflicting_processes_for_bundle()
            if stopped > 0:
                q.put(("info", f"Stopped {stopped} conflicting process(es) before bundling"))

            if not _run_tauri_build(root_dir):
                q.put(("info", "Retrying tauri build once after another process cleanup"))
                stopped_retry = stop_conflicting_processes_for_bundle()
                if stopped_retry > 0:
                    q.put(("info", f"Stopped {stopped_retry} additional conflicting process(es)"))
                if not _run_tauri_build(root_dir):
                    return False

            artifacts = _collect_bundle_artifacts(root_dir)
            if artifacts:
                newest = artifacts[0]
                size_mb = newest.stat().st_size / (1024 * 1024)
                q.put(("success", f"Bundle: {newest.name} ({size_mb:.1f} MB)"))
            else:
                q.put(("info", "No NSIS/MSI artifacts were found under src-tauri/target/release/bundle"))
            return True
        except Exception as e:
            q.put(("error", f"Bundle error: {e}"))
            return False

    return run


# ============================================================
# BuildRunner
# ============================================================
class BuildRunner:
    """
    Orchestrates build steps in a background thread.

    Pushes (msg_type, text) tuples into the queue for the UI to consume:
      stdout, info, success, error  → display text
      step_start  → "StepName:idx:total"
      step_done   → step label
      step_fail   → step label
      build_done  → "success" | "failed" | "cancelled"
    """

    def __init__(
        self,
        steps: list,
        output_queue: queue.Queue,
        cancel_event: threading.Event,
    ):
        self._steps = steps
        self._q = output_queue
        self._cancel = cancel_event

    def run(self):
        total = len(self._steps)

        for idx, (step_name, step_func) in enumerate(self._steps):
            if self._cancel.is_set():
                self._q.put(("error", "Build cancelled by user."))
                self._q.put(("build_done", "cancelled"))
                return

            self._q.put(("step_start", f"{step_name}:{idx}:{total}"))
            success = step_func()

            if self._cancel.is_set():
                self._q.put(("step_fail", step_name))
                self._q.put(("build_done", "cancelled"))
                return

            if success:
                self._q.put(("step_done", step_name))
            else:
                self._q.put(("step_fail", step_name))
                self._q.put(("error", f"Step '{step_name}' failed — aborting."))
                self._q.put(("build_done", "failed"))
                return

        self._q.put(("build_done", "success"))


# ============================================================
# BuildApp
# ============================================================
class BuildApp(tk.Tk):
    """Main Tkinter GUI for the ZZZ Bot build tool."""

    STEP_DEFS = [
        ("frontend", "Frontend", "React + Vite"),
        ("sidecar", "Sidecar", "PyInstaller for Tauri"),
        ("bundle", "Desktop Bundle", "cargo tauri build"),
    ]

    STEP_MAKERS = {
        "frontend": _make_frontend_step,
        "sidecar": _make_sidecar_step,
        "bundle": _make_bundle_step,
    }

    def __init__(self):
        super().__init__()
        self.title("ZZZ Bot Build Tool")
        self.geometry("820x640")
        self.minsize(640, 480)
        try:
            self.iconbitmap(str(Path(__file__).parent.parent / "images" / "Qingyi02.ico"))
        except (tk.TclError, OSError):
            pass

        self._config = BuildConfig()
        self._queue: queue.Queue = queue.Queue()
        self._cancel_event = threading.Event()
        self._building = False
        self._current_ver = "unknown"
        self._latest_installer: Optional[Path] = None

        # Tk variables
        self._var_increment = tk.BooleanVar(value=self._config.increment_version_flag)
        self._var_custom_ver = tk.StringVar(value=self._config.custom_version)
        self._var_parallel_prep = tk.BooleanVar(value=self._config.parallel_prep)
        self._var_auto_run_installer = tk.BooleanVar(value=self._config.auto_run_installer)
        self._step_vars = {
            key: tk.BooleanVar(value=self._config.step_enabled(key))
            for key, _, _ in self.STEP_DEFS
        }
        self._step_status_labels: dict = {}

        self._build_ui()
        self._refresh_version_display()
        self._var_increment.trace_add("write", self._on_increment_toggle_trace)

    # --------------------------------------------------------
    # UI Construction
    # --------------------------------------------------------
    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)  # Output area expands

        pad = {"padx": 10, "pady": 5}

        # -- Version section --
        ver_frame = ttk.LabelFrame(self, text="VERSION", padding=8)
        ver_frame.grid(row=0, column=0, sticky="ew", **pad)
        ver_frame.columnconfigure(2, weight=1)

        self._lbl_current_ver = ttk.Label(ver_frame, text="Current version: …")
        self._lbl_current_ver.grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 6))

        ttk.Checkbutton(
            ver_frame, text="Increment version", variable=self._var_increment
        ).grid(row=1, column=0, sticky="w", padx=(0, 16))

        ttk.Label(ver_frame, text="New version:").grid(row=1, column=1, sticky="e", padx=(0, 6))
        self._entry_ver = ttk.Entry(ver_frame, textvariable=self._var_custom_ver, width=12)
        self._entry_ver.grid(row=1, column=2, sticky="w")

        # -- Steps section --
        steps_frame = ttk.LabelFrame(self, text="BUILD STEPS", padding=8)
        steps_frame.grid(row=1, column=0, sticky="ew", **pad)
        steps_frame.columnconfigure(1, weight=1)

        for i, (key, label, desc) in enumerate(self.STEP_DEFS):
            ttk.Checkbutton(
                steps_frame,
                text=f"{label}    ({desc})",
                variable=self._step_vars[key],
            ).grid(row=i, column=0, sticky="w", pady=3)

            status_lbl = ttk.Label(steps_frame, text="[ idle ]", width=14, anchor="e")
            status_lbl.grid(row=i, column=1, sticky="e", pady=3)
            self._step_status_labels[key] = status_lbl

        option_row = len(self.STEP_DEFS)
        ttk.Checkbutton(
            steps_frame,
            text="Use multiprocessing for Frontend + Sidecar",
            variable=self._var_parallel_prep,
        ).grid(row=option_row, column=0, sticky="w", pady=(8, 2))

        ttk.Checkbutton(
            steps_frame,
            text="Auto run installer after successful bundle",
            variable=self._var_auto_run_installer,
        ).grid(row=option_row + 1, column=0, sticky="w", pady=(2, 0))

        # -- Buttons --
        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=6)

        self._btn_build = ttk.Button(
            btn_frame, text="Build", command=self._on_build, width=16
        )
        self._btn_build.pack(side="left", padx=(0, 8))

        self._btn_cancel = ttk.Button(
            btn_frame, text="Cancel", command=self._on_cancel, width=16, state="disabled"
        )
        self._btn_cancel.pack(side="left")

        # -- Output area --
        out_frame = ttk.LabelFrame(self, text="BUILD OUTPUT", padding=4)
        out_frame.grid(row=3, column=0, sticky="nsew", **pad)
        out_frame.rowconfigure(0, weight=1)
        out_frame.columnconfigure(0, weight=1)

        self._txt_output = tk.Text(
            out_frame,
            state="disabled",
            font=("Consolas", 9),
            wrap="none",
            bg="#1e1e1e",
            fg="#d4d4d4",
            insertbackground="#d4d4d4",
        )
        self._txt_output.grid(row=0, column=0, sticky="nsew")

        sb_y = ttk.Scrollbar(out_frame, orient="vertical", command=self._txt_output.yview)
        sb_y.grid(row=0, column=1, sticky="ns")
        self._txt_output["yscrollcommand"] = sb_y.set

        sb_x = ttk.Scrollbar(out_frame, orient="horizontal", command=self._txt_output.xview)
        sb_x.grid(row=1, column=0, sticky="ew")
        self._txt_output["xscrollcommand"] = sb_x.set

        # Color tags for output text
        self._txt_output.tag_config("success", foreground="#4ec9b0")
        self._txt_output.tag_config("error",   foreground="#f44747")
        self._txt_output.tag_config("info",    foreground="#569cd6")
        self._txt_output.tag_config("stdout",  foreground="#d4d4d4")
        self._txt_output.tag_config("header",  foreground="#dcdcaa")

        # -- Status bar --
        status_bar = ttk.Frame(self, relief="sunken")
        status_bar.grid(row=4, column=0, sticky="ew")
        status_bar.columnconfigure(0, weight=1)

        self._lbl_status = ttk.Label(status_bar, text="Status: Ready", anchor="w")
        self._lbl_status.grid(row=0, column=0, sticky="w", padx=8, pady=2)

        self._lbl_step_count = ttk.Label(status_bar, text="Step 0/3", anchor="e")
        self._lbl_step_count.grid(row=0, column=1, sticky="e", padx=8, pady=2)

    # --------------------------------------------------------
    # Version helpers
    # --------------------------------------------------------
    def _refresh_version_display(self):
        try:
            self._current_ver = get_current_version()
        except (OSError, ValueError):
            self._current_ver = "unknown"
        self._lbl_current_ver.config(text=f"Current version: {self._current_ver}")
        self._on_increment_toggle()

    def _on_increment_toggle_trace(self, *_args):
        """Bridge Tk trace callback to toggle handler."""
        self._on_increment_toggle()

    def _on_increment_toggle(self):
        """Update entry state and auto-fill suggested version when toggled on."""
        if self._var_increment.get():
            if not self._var_custom_ver.get():
                self._var_custom_ver.set(increment_version(self._current_ver))
            self._entry_ver.config(state="normal")
        else:
            self._var_custom_ver.set("")
            self._entry_ver.config(state="disabled")

    # --------------------------------------------------------
    # Output helpers
    # --------------------------------------------------------
    def _append_output(self, text: str, tag: str = "stdout"):
        self._txt_output.config(state="normal")
        self._txt_output.insert("end", text + "\n", tag)
        self._txt_output.see("end")
        self._txt_output.config(state="disabled")

    def _clear_output(self):
        self._txt_output.config(state="normal")
        self._txt_output.delete("1.0", "end")
        self._txt_output.config(state="disabled")

    def _reset_build_button(self):
        self._btn_build.config(text="Build", command=self._on_build)
        self._latest_installer = None

    def _set_run_installer_button(self, installer_path: Path):
        self._latest_installer = installer_path
        self._btn_build.config(text="Run Installer", command=self._on_run_installer)

    def _on_run_installer(self):
        if self._building:
            return
        if not self._latest_installer or not self._latest_installer.exists():
            self._append_output("Installer artifact not found.", "error")
            return
        try:
            _launch_installer(self._latest_installer)
            self._append_output(f"Launched installer: {self._latest_installer}", "success")
        except Exception as exc:
            self._append_output(f"Failed to launch installer: {exc}", "error")

    # --------------------------------------------------------
    # Build control
    # --------------------------------------------------------
    def _on_build(self):
        if self._building:
            return

        # Persist current settings before build
        self._config.increment_version_flag = self._var_increment.get()
        self._config.custom_version = self._var_custom_ver.get()
        self._config.parallel_prep = self._var_parallel_prep.get()
        self._config.auto_run_installer = self._var_auto_run_installer.get()
        for key, var in self._step_vars.items():
            self._config.set_step(key, var.get())
        self._config.save()

        # Apply version increment before launching subprocesses
        if self._var_increment.get():
            new_ver = self._var_custom_ver.get().strip()
            if new_ver:
                try:
                    update_version_files(new_ver)
                    self._current_ver = new_ver
                    self._lbl_current_ver.config(text=f"Current version: {new_ver}")
                    # Reset so re-opening the GUI doesn't re-increment
                    self._config.increment_version_flag = False
                    self._config.custom_version = ""
                    self._config.save()
                    self._var_increment.set(False)
                except Exception as e:
                    self._append_output(f"Version update failed: {e}", "error")
                    return

        # Collect enabled steps
        steps = []
        run_frontend = self._step_vars["frontend"].get()
        run_sidecar = self._step_vars["sidecar"].get()
        run_bundle = self._step_vars["bundle"].get()

        if run_frontend and run_sidecar and self._var_parallel_prep.get():
            steps.append(
                (
                    "Frontend + Sidecar",
                    _make_parallel_prep_step(self._queue, self._cancel_event),
                )
            )
        else:
            if run_frontend:
                steps.append(("Frontend", _make_frontend_step(self._queue, self._cancel_event)))
            if run_sidecar:
                steps.append(("Sidecar", _make_sidecar_step(self._queue, self._cancel_event)))

        if run_bundle:
            steps.append(("Desktop Bundle", _make_bundle_step(self._queue, self._cancel_event)))

        if not steps:
            self._append_output("No steps selected!", "error")
            return

        self._reset_build_button()
        self._clear_output()
        self._reset_step_statuses()
        self._cancel_event.clear()
        self._set_building(True)

        total = len(steps)
        self._lbl_step_count.config(text=f"Step 0/{total}")
        self._lbl_status.config(text="Status: Building…")

        runner = BuildRunner(steps, self._queue, self._cancel_event)
        threading.Thread(target=runner.run, daemon=True).start()
        self.after(100, self._poll_queue, ())

    def _on_cancel(self):
        """Cancel the running build, or close the window if idle."""
        if self._building:
            self._cancel_event.set()
            self._btn_cancel.config(state="disabled")
            self._lbl_status.config(text="Status: Cancelling…")
        else:
            self.destroy()

    def _set_building(self, building: bool):
        self._building = building
        if building:
            self._btn_build.config(state="disabled")
            self._btn_cancel.config(state="normal", text="Cancel")
            self._entry_ver.config(state="disabled")
        else:
            self._btn_build.config(state="normal")
            self._btn_cancel.config(state="normal", text="Close")
            self._entry_ver.config(
                state="normal" if self._var_increment.get() else "disabled"
            )

    def _reset_step_statuses(self):
        for lbl in self._step_status_labels.values():
            lbl.config(text="[ idle ]", foreground="")

    # --------------------------------------------------------
    # Queue polling (runs on main thread via after())
    # --------------------------------------------------------
    def _poll_queue(self, *_args):
        done = False
        try:
            while True:
                msg_type, text = self._queue.get_nowait()
                self._handle_message(msg_type, text)
                if msg_type == "build_done":
                    done = True
                    break
        except queue.Empty:
            pass

        if not done and self._building:
            self.after(100, self._poll_queue, ())

    def _handle_message(self, msg_type: str, text: str):
        if msg_type == "stdout":
            self._append_output(text, "stdout")

        elif msg_type == "info":
            self._append_output(f"→ {text}", "info")

        elif msg_type == "success":
            self._append_output(f"✓ {text}", "success")

        elif msg_type == "error":
            self._append_output(f"✗ {text}", "error")

        elif msg_type == "step_start":
            # Format: "StepName:idx:total"
            name, idx_s, total_s = text.split(":", 2)
            idx = int(idx_s) + 1
            total = int(total_s)
            self._lbl_step_count.config(text=f"Step {idx}/{total}")
            self._lbl_status.config(text=f"Status: {name}…")
            self._append_output(f"\n{'─' * 54}", "header")
            self._append_output(f"  STEP {idx}/{total}: {name.upper()}", "header")
            self._append_output(f"{'─' * 54}\n", "header")
            if name == "Frontend + Sidecar":
                self._step_status_labels["frontend"].config(
                    text="[ running ]",
                    foreground="#569cd6",
                )
                self._step_status_labels["sidecar"].config(
                    text="[ running ]",
                    foreground="#569cd6",
                )
                return
            key = self._label_to_key(name)
            if key:
                self._step_status_labels[key].config(text="[ running ]", foreground="#569cd6")

        elif msg_type == "step_done":
            if text == "Frontend + Sidecar":
                self._step_status_labels["frontend"].config(
                    text="[ done ]",
                    foreground="#4ec9b0",
                )
                self._step_status_labels["sidecar"].config(
                    text="[ done ]",
                    foreground="#4ec9b0",
                )
                return
            key = self._label_to_key(text)
            if key:
                self._step_status_labels[key].config(text="[ done ]", foreground="#4ec9b0")

        elif msg_type == "step_fail":
            if text == "Frontend + Sidecar":
                self._step_status_labels["frontend"].config(
                    text="[ FAILED ]",
                    foreground="#f44747",
                )
                self._step_status_labels["sidecar"].config(
                    text="[ FAILED ]",
                    foreground="#f44747",
                )
                return
            key = self._label_to_key(text)
            if key:
                self._step_status_labels[key].config(text="[ FAILED ]", foreground="#f44747")

        elif msg_type == "build_done":
            self._on_build_complete(text)

    def _label_to_key(self, label: str) -> Optional[str]:
        for key, lbl, _ in self.STEP_DEFS:
            if lbl == label:
                return key
        return None

    def _on_build_complete(self, result: str):
        self._set_building(False)
        if result == "success":
            installer = _collect_bundle_artifacts(Path(__file__).parent.parent)
            latest_installer = installer[0] if installer else None
            self._lbl_status.config(text="Status: Complete!")
            self._append_output("\n" + "=" * 54, "header")
            self._append_output("  BUILD COMPLETE — All steps succeeded!", "success")
            self._append_output("=" * 54, "header")
            if latest_installer is not None:
                self._set_run_installer_button(latest_installer)
                self._append_output(f"Latest installer: {latest_installer}", "info")
                if self._var_auto_run_installer.get():
                    self._on_run_installer()
        elif result == "cancelled":
            self._lbl_status.config(text="Status: Cancelled")
            self._append_output("\nBuild cancelled by user.", "info")
        else:
            self._lbl_status.config(text="Status: Build failed")
            self._append_output("\n" + "=" * 54, "header")
            self._append_output("  BUILD FAILED", "error")
            self._append_output("=" * 54, "header")


if __name__ == "__main__":
    mp.freeze_support()
    app = BuildApp()
    app.mainloop()
