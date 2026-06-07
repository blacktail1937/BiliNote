import re


def prepend_source_link(markdown: str | None, source_url: str) -> str | None:
    """
    在笔记开头添加来源链接；若首个非空行已包含来源链接，则更新该行并避免重复。
    """
    if markdown is None:
        return None

    source = (source_url or "").strip()
    if not source:
        return markdown

    header = f"> 来源链接：{source}"
    lines = markdown.splitlines()
    first_non_empty_idx = None
    for idx, line in enumerate(lines):
        if line.strip():
            first_non_empty_idx = idx
            break

    if first_non_empty_idx is not None:
        first_line = lines[first_non_empty_idx].strip()
        if first_line.startswith("> 来源链接：") or first_line.startswith("来源链接："):
            lines[first_non_empty_idx] = header
            return "\n".join(lines)

    if markdown.strip():
        return f"{header}\n\n{markdown}"
    return header


def _slugify(text: str) -> str:
    """生成匹配 rehype-slug (github-slugger) 的锚点 ID。"""
    text = text.lower().strip()
    text = re.sub(r'\s+', '-', text)
    text = re.sub(r'[^\w\u4e00-\u9fff\-]', '', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')


def prepend_toc(markdown: str) -> str:
    """提取所有 ## 标题，自动生成目录并插入笔记开头。"""
    if not markdown:
        return markdown

    headings = re.findall(r'^##\s+(.+)$', markdown, re.MULTILINE)
    if len(headings) < 2:
        return markdown

    toc_items = []
    seen_slugs = {}
    for h in headings:
        clean = re.sub(r'\*?(?:Content|Screenshot)-\[.*?\]\*?', '', h).strip()
        if not clean:
            clean = h.strip()
        slug = _slugify(clean)
        if slug in seen_slugs:
            seen_slugs[slug] += 1
            slug = f'{slug}-{seen_slugs[slug]}'
        else:
            seen_slugs[slug] = 0
        toc_items.append(f'  - [{clean}](#{slug})')

    toc = '## 目录\n\n' + '\n'.join(toc_items) + '\n\n---\n'
    return toc + markdown


def replace_content_markers(markdown: str, video_id: str, platform: str = 'bilibili') -> str:
    """
    替换 *Content-04:16*、Content-04:16、Content-[04:16] 或 *Content-[01:09:30] 为超链接
    """
    pattern = r"(?:\*?)Content-(?:\[(?:(\d{1,2}):)?(\d{1,3}):(\d{1,2})\]|(?:(\d{1,2}):)?(\d{1,3}):(\d{1,2}))"

    def replacer(match):
        h = match.group(1) or match.group(4)
        mm = match.group(2) or match.group(5)
        ss = match.group(3) or match.group(6)
        total_seconds = (int(h or 0) * 3600) + int(mm) * 60 + int(ss)

        if h:
            time_str = f"{h}:{mm}:{ss}"
        elif int(mm) >= 60:
            h_norm = int(mm) // 60
            mm_norm = int(mm) % 60
            time_str = f"{h_norm}:{mm_norm:02d}:{ss}"
        else:
            time_str = f"{mm}:{ss}"

        if platform == 'bilibili':
            if "_p" in video_id:
                parsed_video_id = video_id.replace("_p", "?p=")
                url = f"https://www.bilibili.com/video/{parsed_video_id}&t={total_seconds}"
            else:
                url = f"https://www.bilibili.com/video/{video_id}/?t={total_seconds}"
        elif platform == 'youtube':
            url = f"https://www.youtube.com/watch?v={video_id}&t={total_seconds}s"
        elif platform == 'douyin':
            url = f"https://www.douyin.com/video/{video_id}"
            return f"[原片 @ {time_str}]({url})"
        else:
            return f"({time_str})"

        return f"[原片 @ {time_str}]({url})"

    return re.sub(pattern, replacer, markdown)

