"""Represents current userbot version"""
# ©️ Dan Gazizullin, 2021-2023
# This file is a part of Hikka Userbot
# 🌐 https://github.com/hikariatama/Hikka
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

# ©️ Codrago, 2024-2030
# This file is a part of Heroku Userbot
# 🌐 https://github.com/coddrago/Heroku
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

__version__ = (2, 0, 0)

import os

import git
import subprocess
from heroku._internal import restart

try:
    branch = git.Repo(
        path=os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    ).active_branch.name
except Exception:
    branch = "master"


async def check_branch(me_id: int, allowed_ids: list):
    if me_id in allowed_ids:
        return

    repo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    try:
        repo = git.Repo(path=repo_path)
    except Exception:
        return

    branch_name = None

    try:
        branch_name = repo.active_branch.name
    except Exception:
        branch_name = None

    if not branch_name:
        try:
            head_path = os.path.join(repo_path, ".git", "HEAD")
            with open(head_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
            if content.startswith("ref:"):
                branch_name = content.split("/")[-1]
        except Exception:
            branch_name = branch_name

    if not branch_name:
        try:
            proc = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=3,
            )
            if proc.returncode == 0:
                candidate = proc.stdout.strip()
                if candidate:
                    branch_name = candidate
        except Exception:
            pass

    if isinstance(branch_name, str):
        branch_name = branch_name.strip().lstrip("refs/heads/")

    if branch_name and branch_name != "master":

        try:
            commit = repo.head.commit.hexsha
        except Exception:
            commit = None

        is_ancestor = False
        if commit:
            try:
                proc = subprocess.run(
                    ["git", "merge-base", "--is-ancestor", commit, "refs/remotes/origin/master"],
                    cwd=repo_path,
                )
                is_ancestor = proc.returncode == 0
            except Exception:
                is_ancestor = False

        try:
            repo.git.reset("--hard", "HEAD")
            repo.git.checkout("master", force=True)
        except Exception:
            try:
                subprocess.run(["git", "reset", "--hard", "HEAD"], cwd=repo_path)
                subprocess.run(["git", "checkout", "master", "-f"], cwd=repo_path)
            except Exception:
                pass

        restart()
