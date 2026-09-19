"""Transactional, code-only updates with an independent startup supervisor."""

import asyncio
import contextlib
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time
import uuid

GUARD_PROTOCOL = 1
ACTIVE = {"prepared", "starting", "rolling_back"}
RESTART_EXIT = 75
STARTUP_TIMEOUT = 300
STABILITY_SECONDS = 10


class UpdateError(RuntimeError):
    pass


def repository_root():
    return Path(__file__).resolve().parent.parent


def git(root, *args, timeout=120):
    result = subprocess.run(
        ["git", *args], cwd=root, capture_output=True, timeout=timeout,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0", "GIT_ASKPASS": "echo"},
    )
    if result.returncode:
        raise UpdateError(f"git {args[0]} failed (exit {result.returncode})")
    return result.stdout


def storage(root=None):
    root = Path(root or repository_root())
    directory = Path(os.fsdecode(git(root, "rev-parse", "--absolute-git-dir")).strip())
    return directory / "heroku-safe-update"


def atomic_json(path, value):
    path = Path(path)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("x", encoding="utf-8") as file:
            os.chmod(temporary, 0o600)
            json.dump(value, file, ensure_ascii=False)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary, path)
        fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    finally:
        temporary.unlink(missing_ok=True)


def read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None


def status(root=None):
    return read_json(storage(root) / "transaction.json")


def trial_active():
    return bool(os.environ.get("HEROKU_UPDATE_TRIAL"))


def clean(root):
    return not git(root, "status", "--porcelain", "--untracked-files=no").strip()


def head(root):
    return git(root, "rev-parse", "HEAD").decode().strip()


def _preflight(root, old, target):
    if not clean(root):
        raise UpdateError("Local changes or unfinished Git operations detected; update cancelled.")
    git_dir = storage(root).parent
    if any((git_dir / name).exists() for name in (
        "MERGE_HEAD", "CHERRY_PICK_HEAD", "REVERT_HEAD", "rebase-merge", "rebase-apply",
    )):
        raise UpdateError("Complete the current Git operation first.")
    git(root, "merge-base", "--is-ancestor", old, target)
    changed = git(root, "diff", "--name-only", "-z", old, target).split(b"\0")
    dependency_files = {
        b"requirements.txt", b"optional_requirements.txt", b"pyproject.toml",
        b"uv.lock", b"poetry.lock", b"setup.py", b"setup.cfg",
    }
    if dependency_files.intersection(changed) or any(
        b"requirements" in name.lower() for name in changed if name
    ):
        raise UpdateError("The update changes dependencies; safe environment rollback is not supported yet.")
    guard = git(root, "show", f"{target}:heroku/update_guard.py")
    entry = git(root, "show", f"{target}:heroku/main.py")
    if b"GUARD_PROTOCOL = 1" not in guard or b"update_guard.monitor_client" not in entry:
        raise UpdateError("The new version does not support the safe update validation protocol.")
    files = git(root, "ls-tree", "-r", "--name-only", "-z", target).split(b"\0")
    for name in files:
        if name.startswith(b"heroku/") and name.endswith(b".py"):
            filename = os.fsdecode(name)
            try:
                compile(git(root, "show", f"{target}:{filename}"), filename, "exec")
            except (SyntaxError, ValueError) as error:
                raise UpdateError(f"Syntax error in {filename}") from error
    requirement = Path(root) / "requirements.txt"
    if requirement.is_file():
        marker = Path(root) / ".requirements_hash"
        digest = hashlib.sha256(requirement.read_bytes()).hexdigest()
        if not marker.is_file() or marker.read_text().strip() != digest:
            raise UpdateError("Environment not verified by .requirements_hash; complete a successful normal startup first.")


def prepare(root, expected, *, timeout=STARTUP_TIMEOUT):
    if not sys.platform.startswith("linux") or "--sandbox" in sys.argv:
        raise UpdateError("Safe updates are currently supported only on Linux without --sandbox.")
    import fcntl

    root = Path(root).resolve()
    directory = storage(root)
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    with (directory / "prepare.lock").open("a") as lock:
        os.chmod(lock.name, 0o600)
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise UpdateError("Another update is already being prepared.") from error
        previous = read_json(directory / "transaction.json")
        if previous and previous["phase"] in ACTIVE:
            raise UpdateError("An unfinished safe update already exists.")
        if not expected or any(not modules for modules in expected.values()):
            raise UpdateError("Not all accounts and modules are ready for the update.")
        old = head(root)
        branch = git(root, "symbolic-ref", "--short", "HEAD").decode().strip()
        upstream = git(root, "rev-parse", "--abbrev-ref", "@{upstream}").decode().strip()
        remote = git(root, "config", "--get", f"branch.{branch}.remote").decode().strip()
        if remote == ".":
            raise UpdateError("Safe updates require a separate Git remote.")
        git(root, "fetch", "--quiet", "--", remote)
        target = git(root, "rev-parse", f"{upstream}^{{commit}}").decode().strip()
        if target == old:
            return None
        _preflight(root, old, target)
        token = uuid.uuid4().hex
        backup_ref = f"refs/heroku/safe-update/{token}"
        git(root, "update-ref", backup_ref, old)
        runner = directory / f"runner-{token}.py"
        shutil.copyfile(__file__, runner)
        os.chmod(runner, 0o600)
        state = {
            "protocol": GUARD_PROTOCOL, "token": token, "phase": "prepared",
            "root": str(root), "old": old, "target": target, "branch": branch,
            "backup_ref": backup_ref, "runner": str(runner),
            "expected": {str(key): sorted(value) for key, value in expected.items()},
            "created": time.time(), "timeout": timeout,
            "stability": STABILITY_SECONDS, "args": sys.argv[1:],
        }
        atomic_json(directory / "transaction.json", state)
        return state


def cancel_prepared(root, token, reason):
    directory = storage(root)
    state = read_json(directory / "transaction.json")
    if state and state["token"] == token and state["phase"] == "prepared":
        state.update(phase="aborted", reason=reason, finished=time.time())
        atomic_json(directory / "transaction.json", state)


def bootstrap():
    if os.environ.get("HEROKU_UPDATE_SUPERVISED"):
        return
    try:
        state = status()
    except UpdateError:
        return
    if state and state["phase"] in ACTIVE:
        os.execv(sys.executable, [sys.executable, state["runner"], "supervise", state["root"]])


def launch_pending():
    if os.environ.get("HEROKU_UPDATE_SUPERVISED"):
        raise SystemExit(RESTART_EXIT)
    bootstrap()


def _rollback(root, state):
    current = head(root)
    branch = git(root, "symbolic-ref", "--short", "HEAD").decode().strip()
    if branch != state["branch"] or current not in {state["old"], state["target"]} or not clean(root):
        raise UpdateError("Concurrent Git changes detected; automatic rollback stopped to preserve local changes.")
    git(root, "reset", "--keep", state["old"])
    _clear_bytecode(root)
    if head(root) != state["old"] or not clean(root):
        raise UpdateError("Could not verify source code restoration.")


def _health(directory, state):
    now = time.time()
    for account, expected in state["expected"].items():
        record = read_json(directory / f"health-{state['token']}-{account}.json")
        if not record or now - record["time"] > 5:
            return False, None
        if record.get("error"):
            return False, record["error"]
        missing = set(expected) - set(record.get("modules", []))
        if missing:
            return False, "Modules failed to load: " + ", ".join(sorted(missing))
        if not record.get("connected"):
            return False, None
    return True, None


def _stop(child):
    with contextlib.suppress(ProcessLookupError):
        os.killpg(child.pid, signal.SIGKILL)
    child.wait(timeout=15)


def _child_setup():
    import ctypes

    parent = os.getppid()
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(1, signal.SIGKILL, 0, 0, 0) != 0:
        raise OSError(ctypes.get_errno(), "prctl(PR_SET_PDEATHSIG) failed")
    if os.getppid() != parent:
        os._exit(1)


def _clear_bytecode(root):
    for path in (Path(root) / "heroku").rglob("__pycache__"):
        if path.is_dir() and not path.is_symlink():
            shutil.rmtree(path)


def supervise(root):
    import fcntl

    root = Path(root)
    directory = storage(root)
    with (directory / "supervisor.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise UpdateError("Supervisor is already running")
        return _supervise(root, directory)


def _supervise(root, directory):
    child = None
    stopping = False

    def stop(signum, frame):
        nonlocal stopping
        stopping = True
        if child is not None and child.poll() is None:
            os.killpg(child.pid, signum)

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    while not stopping:
        state = read_json(directory / "transaction.json")
        trial = state["phase"] == "prepared"
        if state["phase"] in {"starting", "rolling_back"}:
            state["reason"] = "The previous startup was interrupted before readiness was confirmed."
            try:
                _rollback(root, state)
                state.update(phase="rolled_back", finished=time.time())
            except Exception as error:
                state.update(phase="rollback_failed", reason=str(error))
                atomic_json(directory / "transaction.json", state)
                return 1
            atomic_json(directory / "transaction.json", state)
        if state["phase"] == "rollback_failed":
            return 1
        if trial:
            try:
                if head(root) != state["old"]:
                    raise UpdateError("The original commit changed after preparation.")
                branch = git(root, "symbolic-ref", "--short", "HEAD").decode().strip()
                if branch != state["branch"]:
                    raise UpdateError("The branch changed after preparation.")
                _preflight(root, state["old"], state["target"])
                state.update(phase="starting", started=time.time())
                atomic_json(directory / "transaction.json", state)
                git(root, "merge", "--ff-only", "--no-edit", "--no-overwrite-ignore", state["target"])
                _clear_bytecode(root)
            except Exception as error:
                state["reason"] = str(error)
                if head(root) != state["old"]:
                    try:
                        _rollback(root, state)
                    except Exception as rollback_error:
                        state.update(phase="rollback_failed", reason=str(rollback_error))
                        atomic_json(directory / "transaction.json", state)
                        return 1
                state.update(phase="aborted", finished=time.time())
                atomic_json(directory / "transaction.json", state)
                trial = False
        env = {**os.environ, "HEROKU_UPDATE_SUPERVISED": "1", "HEROKU_UPDATE_STATE_DIR": str(directory)}
        for name in ("HEROKU_DO_NOT_RESTART", "HEROKU_DO_NOT_RESTART2", "HEROKU_UPDATE_TRIAL"):
            env.pop(name, None)
        if trial:
            env["HEROKU_UPDATE_TRIAL"] = state["token"]
        try:
            child = subprocess.Popen(
                [sys.executable, "-m", "heroku", *state["args"]], cwd=root,
                env=env, start_new_session=True, preexec_fn=_child_setup,
            )
        except Exception as error:
            state["reason"] = f"Failed to start the process: {type(error).__name__}"
            if trial:
                try:
                    _rollback(root, state)
                    state.update(phase="rolled_back", finished=time.time())
                except Exception as rollback_error:
                    state.update(phase="rollback_failed", reason=str(rollback_error))
            atomic_json(directory / "transaction.json", state)
            return 1
        started = time.monotonic()
        stable_since = None
        failure = None
        while child.poll() is None and not stopping:
            if trial:
                try:
                    healthy, failure = _health(directory, state)
                except (ValueError, KeyError, TypeError, OSError):
                    healthy, failure = False, "Invalid startup health report."
                if failure:
                    break
                if healthy:
                    if stable_since is None:
                        stable_since = time.monotonic()
                    if time.monotonic() - stable_since >= state["stability"]:
                        state.update(phase="healthy", finished=time.time())
                        atomic_json(directory / "transaction.json", state)
                        trial = False
                else:
                    stable_since = None
                if trial and time.monotonic() - started >= state["timeout"]:
                    failure = "Startup and Telegram connectivity check timeout expired."
                    break
            time.sleep(0.25)
        if stopping:
            try:
                return child.wait(timeout=15)
            except subprocess.TimeoutExpired:
                _stop(child)
                return 0
        if trial:
            failure = failure or f"The new version exited before becoming ready (exit {child.returncode})."
            _stop(child)
            state.update(phase="rolling_back", reason=failure)
            atomic_json(directory / "transaction.json", state)
            try:
                _rollback(root, state)
            except Exception as error:
                state.update(phase="rollback_failed", reason=str(error))
                atomic_json(directory / "transaction.json", state)
                return 1
            state.update(phase="rolled_back", finished=time.time())
            atomic_json(directory / "transaction.json", state)
            continue
        if child.returncode == RESTART_EXIT:
            continue
        return child.returncode or 0
    return 0


async def monitor_client(client, modules):
    directory_name = os.environ.get("HEROKU_UPDATE_STATE_DIR")
    if not directory_name:
        return
    directory = Path(directory_name)
    state = read_json(directory / "transaction.json")
    if not state:
        return
    account = str(client.tg_id)
    token = os.environ.get("HEROKU_UPDATE_TRIAL")
    while token == state["token"] and state["phase"] == "starting":
        module_loader = modules.lookup("LoaderMod")
        if module_loader and module_loader.fully_loaded:
            from herokutl.tl.functions.updates import GetStateRequest

            connected = False
            if client.is_connected():
                try:
                    await asyncio.wait_for(client(GetStateRequest()), timeout=15)
                    connected = True
                except Exception:
                    pass
            errors = getattr(modules, "_startup_errors", [])
            record = {
                "time": time.time(), "connected": connected,
                "modules": [mod.__class__.__name__ for mod in modules.modules
                            if getattr(mod, "_heroku_ready", False)],
                "error": ("Module loading errors: " + ", ".join(errors)) if errors else None,
            }
            atomic_json(directory / f"health-{token}-{account}.json", record)
        await asyncio.sleep(1)
        state = read_json(directory / "transaction.json")
    if token == state["token"] and state["phase"] == "healthy":
        os.environ.pop("HEROKU_UPDATE_TRIAL", None)
        updater = modules.lookup("UpdaterMod")
        if updater:
            await updater.full_restart_complete()
    if state["phase"] in {"rolled_back", "aborted"}:
        receipt = directory / f"notice-{state['token']}-{account}.json"
        if not receipt.exists():
            import logging

            # Route the record to this account's standard Telegram logs handler.
            _heroku_client_id_logging_tag = client.tg_id
            logging.getLogger(__name__).error(
                "Safe update not applied (%s). "
                "Working commit: %s. Reason: %s",
                state["phase"],
                state["old"][:12],
                state.get("reason", "Startup validation failed."),
            )
            atomic_json(receipt, {"logged": time.time()})


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "supervise":
        raise SystemExit(supervise(sys.argv[2]))
    raise SystemExit("Usage: update_guard.py supervise REPOSITORY")
