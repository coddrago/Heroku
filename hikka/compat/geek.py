# ©️ Dan Gazizullin, 2021-2023
# This file is a part of Hikka Userbot
# 🌐 https://github.com/hikariatama/Hikka
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

import re


def compat(code: str) -> str:
    """
    Reformats modules, built for GeekTG to work with Hikka.
    :param code: code to reformat
    :return: reformatted code
    :rtype: str
    """
    code = code.replace("GeekInlineQuery", "InlineQuery").replace(
        "self.inline._bot", "self.inline.bot"
    )

    def repl_imports(match):
        indent, imports = match.groups()
        imports = [i.strip() for i in imports.split(",")]
        if "rand" in imports:
            imports_wo_rand = [i for i in imports if i != "rand"]
            lines = []
            if imports_wo_rand:
                lines.append(
                    f"{indent}from ..inline.types import {', '.join(imports_wo_rand)}"
                )
            lines.append(f"{indent}from ..utils import rand")
            return "\n".join(lines)
        else:
            return f"{indent}from ..inline.types import {', '.join(imports)}"

    code = re.sub(
        r"^( *)from \.\.inline import (.+)$",
        repl_imports,
        code,
        flags=re.M,
    )

    return code
