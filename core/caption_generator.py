import re
import os
from pathlib import Path
from typing import List, Dict, Optional

def sanitize_folder_name(name: str) -> str:
    """
    Sanitizes title string to be a safe, clean Windows folder name.
    Preserves Japanese kanji/kana, brackets 【】, spaces, hyphens.
    """
    cleaned = re.sub(r'[\x00-\x1f\\/:*?"<>|]', '_', name)
    cleaned = cleaned[:80].strip('. ')
    return cleaned if cleaned else "omoshiroi_video"


def resolve_output_file(output_dir: str | Path, file_path: str) -> Path | None:
    root = Path(output_dir).resolve()
    candidate = (root / file_path).resolve()
    if candidate.is_relative_to(root) and candidate.is_file():
        return candidate
    return None

def generate_viral_caption(
    title_sub: str,
    moral_lesson: Optional[str] = None,
    moral_lesson_vi: Optional[str] = None,
    dialogue: Optional[List[Dict]] = None
) -> str:
    """
    Generates a sensational, concise, high-converting caption for TikTok, Shorts, Reels.
    Includes catchy Japanese hook, punchline synopsis, moral lesson, CTA, and hashtags.
    Also appends a clear Vietnamese reference at the bottom for channel management.
    """
    keywords = []
    if dialogue:
        for d in dialogue:
            t = d.get("text", "")
            kw = re.findall(r'「([^」]+)」', t)
            keywords.extend(kw)

    kw_str = f"「{keywords[0]}」" if keywords else ""

    # Sensational hook tailored to the 10 drama genres
    if "診察" in title_sub or "病院" in title_sub:
        hook_header = "🏥【医療崩壊!?】"
        action_phrase = "医者も頭を抱えるヤバすぎる患者の末路…🏥😱"
    elif "オフィス" in title_sub or "職場" in title_sub:
        hook_header = "💼【社内トラブル】"
        action_phrase = "会社でやらかしたZ世代社員の衝撃の結末…👔💥"
    elif "学園" in title_sub or "学校" in title_sub:
        hook_header = "🏫【学園崩壊】"
        action_phrase = "ズルがバレた生徒の言い訳がヤバすぎるww🎒😂"
    elif "コンビニ" in title_sub:
        hook_header = "🏪【修羅場】"
        action_phrase = "理不尽クレーマーを撃退した店員の神対応ww🛒🔥"
    elif "面接" in title_sub:
        hook_header = "📑【面接自爆】"
        action_phrase = "履歴書を盛りすぎた就活生の悲惨な末路…💼💦"
    elif "デート" in title_sub:
        hook_header = "💔【大修羅場】"
        action_phrase = "ケチすぎる彼氏にブチギレた彼女の反撃ww💔😂"
    elif "騒音" in title_sub or "マンション" in title_sub:
        hook_header = "🏢【近隣トラブル】"
        action_phrase = "深夜の迷惑住人に管理人ブチギレの瞬間…🔊💥"
    elif "警察" in title_sub or "交番" in title_sub:
        hook_header = "🚨【警察沙汰】"
        action_phrase = "取り調べで言い逃れしようとした結果…😱"
    elif "裁判" in title_sub or "法廷" in title_sub:
        hook_header = "⚖️【衝撃の結末】"
        action_phrase = "法廷で下された驚きの判決とは…！？💥"
    elif "探偵" in title_sub or "推理" in title_sub:
        hook_header = "🔍【完全論破】"
        action_phrase = "完全犯罪を企てた犯人のボロが出まくりw⚡"
    else:
        hook_header = "🔥【爆笑コント】"
        action_phrase = "まさかの展開にツッコミが追いつかないww😂"

    clean_title = title_sub.replace("【", "").replace("】", " ")

    lines_jp = [
        f"{hook_header}{clean_title}",
        f"{action_phrase}",
        "",
        f"軽い気持ちでやらかした代償がデカすぎる…！{kw_str}",
        ""
    ]

    if moral_lesson:
        lines_jp.extend([
            "📜【本日の教訓】",
            f"{moral_lesson}",
            ""
        ])

    lines_jp.extend([
        "💬 あなたならこの件、どう思う？コメント欄で教えて！👇",
        "",
        "#スカッとする話 #風刺 #裁判 #コント #アニメ #あるある #教訓 #雑学 #TikTok短尺 #omoshiroi"
    ])

    caption_jp = "\n".join(lines_jp)

    lines_vi = [
        "",
        "=" * 44,
        "🇻🇳 BẢN DỊCH & CAPTION TIẾNG VIỆT (DÙNG ĐĂNG KÊNH HOẶC QUẢN LÝ):",
        f"📌 Chủ đề: {title_sub}"
    ]

    if moral_lesson_vi:
        lines_vi.append(f"💡 Bài học răn đe: {moral_lesson_vi}")
    elif moral_lesson:
        lines_vi.append(f"💡 Bài học răn đe (JP): {moral_lesson}")

    lines_vi.extend([
        "🎯 Gợi ý Caption tiếng Việt ngắn giật gân:",
        f"   \"{clean_title}: Cái kết đắng lòng không kịp hối hận! Xem ngay để không mắc phải sai lầm này! #omoshiroi #baihoccuocsong #haihuoc #chambiem\"",
        "=" * 44
    ])

    return caption_jp + "\n" + "\n".join(lines_vi)
