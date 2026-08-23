import html


def _text(value) -> str:
    if value is None:
        return ""

    name = type(value).__name__
    if name == "TextEmpty":
        return ""
    if name == "TextPlain":
        return html.escape(getattr(value, "text", ""), quote=False)
    if name == "TextConcat":
        return "".join(_text(item) for item in getattr(value, "texts", []))
    if name in {
        "TextBold",
        "TextItalic",
        "TextUnderline",
        "TextStrike",
        "TextFixed",
        "TextSubscript",
        "TextSuperscript",
        "TextMarked",
    }:
        tags = {
            "TextBold": ("<b>", "</b>"),
            "TextItalic": ("<i>", "</i>"),
            "TextUnderline": ("<u>", "</u>"),
            "TextStrike": ("<s>", "</s>"),
            "TextFixed": ("<code>", "</code>"),
            "TextSubscript": ("<sub>", "</sub>"),
            "TextSuperscript": ("<sup>", "</sup>"),
            "TextMarked": ("<mark>", "</mark>"),
        }
        start, end = tags[name]
        return start + _text(getattr(value, "text", None)) + end
    if name in {"TextUrl", "TextEmail"}:
        url = getattr(value, "url", None) or getattr(value, "email", "")
        if name == "TextEmail" and not str(url).startswith("mailto:"):
            url = f"mailto:{url}"
        return f'<a href="{html.escape(str(url), quote=True)}">{_text(getattr(value, "text", None))}</a>'
    if name == "TextPhone":
        phone = str(getattr(value, "phone", ""))
        return f'<a href="tel:{html.escape(phone, quote=True)}">{_text(getattr(value, "text", None))}</a>'
    if name == "TextAnchor":
        return f'<a name="{html.escape(str(getattr(value, "name", "")), quote=True)}">{_text(getattr(value, "text", None))}</a>'
    if name == "TextMention":
        return _text(getattr(value, "text", None))
    if name == "TextImage":
        return _text(getattr(value, "alt", None) or getattr(value, "text", None))
    nested = getattr(value, "text", None)
    return _text(nested) if nested is not None else html.escape(str(value), quote=False)


def _caption(value) -> str:
    if value is None:
        return ""
    text = _text(getattr(value, "text", None))
    credit = _text(getattr(value, "credit", None))
    if credit:
        return f"{text}<cite>{credit}</cite>" if text else f"<cite>{credit}</cite>"
    return text


def _block(value) -> str:
    if value is None:
        return ""

    name = type(value).__name__
    text = _text(getattr(value, "text", None))
    simple = {
        "PageBlockTitle": "h1",
        "PageBlockSubtitle": "h2",
        "PageBlockHeading1": "h1",
        "PageBlockHeading2": "h2",
        "PageBlockHeading3": "h3",
        "PageBlockHeading4": "h4",
        "PageBlockHeading5": "h5",
        "PageBlockHeading6": "h6",
        "PageBlockHeader": "h3",
        "PageBlockSubheader": "h4",
        "PageBlockKicker": "p",
        "PageBlockParagraph": "p",
        "PageBlockFooter": "footer",
    }
    if name in simple:
        tag = simple[name]
        return f"<{tag}>{text}</{tag}>"
    if name == "PageBlockPreformatted":
        language = html.escape(str(getattr(value, "language", "")), quote=True)
        return f'<pre><code class="language-{language}">{text}</code></pre>'
    if name == "PageBlockDivider":
        return "<hr>"
    if name == "PageBlockAnchor":
        return f'<a name="{html.escape(str(getattr(value, "name", "")), quote=True)}"></a>'
    if name in {"PageBlockBlockquote", "PageBlockPullquote"}:
        caption = _caption(getattr(value, "caption", None))
        return f"<blockquote>{text}{f'<cite>{caption}</cite>' if caption else ''}</blockquote>"
    if name == "PageBlockBlockquoteBlocks":
        blocks = "".join(_block(item) for item in getattr(value, "blocks", []))
        return f"<blockquote>{blocks}{_caption(getattr(value, 'caption', None))}</blockquote>"
    if name in {"PageBlockPhoto", "PageBlockVideo", "PageBlockAudio", "PageBlockMap"}:
        caption = _caption(getattr(value, "caption", None))
        return f"<p>{caption}</p>" if caption else ""
    if name in {"PageBlockCollage", "PageBlockSlideshow"}:
        return "".join(_block(item) for item in getattr(value, "items", [])) + _caption(getattr(value, "caption", None))
    if name == "PageBlockTable":
        title = f"<p>{_text(getattr(value, 'title', None))}</p>" if getattr(value, "title", None) else ""
        rows = "".join(
            "<tr>" + "".join(f"<td>{_text(getattr(cell, 'text', None))}</td>" for cell in getattr(row, "cells", [])) + "</tr>"
            for row in getattr(value, "rows", [])
        )
        return title + f"<table>{rows}</table>"
    if name in {"PageBlockList", "PageBlockOrderedList"}:
        tag = "ol" if name.endswith("OrderedList") else "ul"
        items = "".join(_list_item(item) for item in getattr(value, "items", []))
        return f"<{tag}>{items}</{tag}>"
    if name == "PageBlockDetails":
        title = _text(getattr(value, "title", None))
        blocks = "".join(_block(item) for item in getattr(value, "blocks", []))
        return f"<details><summary>{title}</summary>{blocks}</details>"
    if name == "PageBlockMath":
        return f"<pre>{html.escape(str(getattr(value, 'source', '')), quote=False)}</pre>"
    if name == "PageBlockThinking":
        return f"<p>{text}</p>"
    nested = getattr(value, "blocks", None)
    if nested is not None:
        return "".join(_block(item) for item in nested)
    return f"<p>{text}</p>" if text else ""


def _list_item(value) -> str:
    name = type(value).__name__
    if name in {"PageListItemBlocks", "PageListOrderedItemBlocks"}:
        text = "".join(_block(item) for item in getattr(value, "blocks", []))
    else:
        text = _text(getattr(value, "text", None))
    if getattr(value, "checkbox", False):
        text = ("[x] " if getattr(value, "checked", False) else "[ ] ") + text
    return f"<li>{text}</li>"


def rich_message_to_html(rich_message) -> str:
    if rich_message is None:
        return ""
    return "\n".join(rendered for rendered in (_block(item) for item in getattr(rich_message, "blocks", [])) if rendered)
