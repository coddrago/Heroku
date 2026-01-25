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

<<<<<<< HEAD
__version__ = (2, 0, 0)
=======
__version__ = (1, 7, 2)
>>>>>>> pr-242

import os

import git
from ._internal import (
    get_branch_name,
    check_commit_ancestor,
    reset_to_master,
    restore_worktree,
    restart,
)

try:
    branch = git.Repo(
        path=os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    ).active_branch.name
except Exception:
    branch = "master"


async def check_branch(me_id: int, allowed_ids: list, self):
    repo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    try:
        repo = git.Repo(path=repo_path)
    except Exception:
        return

    if me_id in allowed_ids:
        return
    else:
        branch_name = get_branch_name(repo_path)
        is_ancestor = check_commit_ancestor(repo, branch_name)
        if is_ancestor:
            return
        else:
            try:
                reset_to_master(repo_path)
                restore_worktree(repo_path)
                self.client.log_out()
            except Exception:
                pass

    restart()
