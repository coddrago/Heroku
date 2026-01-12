# ©️ Codrago, 2024-2030
# This file is a part of Heroku Userbot
# 🌐 https://github.com/coddrago/Heroku
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

import logging
import typing
import asyncio

import git
import herokutl

parser = herokutl.utils.sanitize_parse_mode("html")
logger = logging.getLogger(__name__)

# GeekTG Compatibility
def get_git_info() -> typing.Tuple[str, str]:
    """
    Get git info
    :return: Git info
    """
    hash_ = get_git_hash()
    return (
        hash_,
        f"https://github.com/coddrago/Heroku/commit/{hash_}" if hash_ else "",
    )

def get_git_hash() -> typing.Union[str, bool]:
    """
    Get current Heroku git hash
    :return: Git commit hash
    """
    try:
        return git.Repo().head.commit.hexsha
    except Exception:
        return False


def get_commit_url() -> str:
    """
    Get current Heroku git commit url
    :return: Git commit url
    """
    try:
        hash_ = get_git_hash()
        return f'<a href="https://github.com/coddrago/Heroku/commit/{hash_}">#{hash_[:7]}</a>'
    except Exception:
        return "Unknown"

async def get_git_status() -> str:
    """
    :return: 'Clean' or 'X files modified'.
    """
    try:
        process = await asyncio.create_subprocess_shell(
            "git status --porcelain",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await process.communicate()

        if process.returncode != 0:
            return "Not a Git repo"

        output = stdout.decode().strip()

        if not output:
            return "Clean"
        
        count = len(output.splitlines())
        word = "file" if count == 1 else "files"
        return f"{count} {word} modified"

    except Exception:
        return "Unknown"


def get_last_commit_message() -> str:
    """
    Get the message of the last commit
    :return: Last commit message
    """
    try:
        repo = git.Repo()
        return repo.head.commit.message.strip()
    except Exception:
        return "Unknown"


def get_commit_count() -> int:
    """
    Get the total number of commits in the repository
    :return: Number of commits
    """
    try:
        repo = git.Repo()
        return len(list(repo.iter_commits()))
    except Exception:
        return 0