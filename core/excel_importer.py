"""
OMOSHIROI - Script Excel / CSV Importer Module
Converts Excel (.xlsx/.xls) or CSV files into structured dialogue scripts.
Includes zero-dependency fallback parser using Python standard library (zipfile + xml.etree.ElementTree / csv).
"""

import os
import io
import csv
import logging
import zipfile
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Tuple, Optional

logger = logging.getLogger("omoshiroi.excel_importer")

# Standard emotion key mapping
EMOTION_KEYWORDS = [
    ("regret", ["hối hận", "hoi han", "day dứt", "day dut", "ăn ăn", "an an", "hối", "hối hận"]),
    ("angry", ["tức giận", "tuc gian", "giận", "gian", "nổi giận", "truy vấn", "chất vấn", "gắt", "phẫn", "nghiêm nghị"]),
    ("shocked", ["sốc", "soc", "bất ngờ", "bat ngo", "há hốc", "ha hoc", "bàng hoàng", "kinh ngạc", "ngạc nhiên"]),
    ("sweat", ["mồ hôi", "mo hoi", "lo sợ", "lo so", "căng thẳng", "cang thang", "hoảng", "bí ẩn", "e ngại", "do dự"]),
    ("blush", ["ngượng", "nguong", "xấu hổ", "xau ho", "ngại", "ngai", "bối rối", "boi roi", "thẹn"]),
]

# Character speaker mapping rules
SPEAKER_A_KEYWORDS = [
    "thẩm phán", "tham phan", "bác sĩ", "bac si", "cảnh sát", "canh sat",
    "sếp", "sep", "thầy", "thay", "luật sư", "luat su", "giám khảo",
    "giam khao", "chủ cửa hàng", "chu cua hang", "người dẫn", "nguoi dan",
    "nữ cảnh sát", "thẩm phán ⚖️", "⚖️"
]

SPEAKER_B_KEYWORDS = [
    "tội phạm", "toi pham", "bị cáo", "bi cao", "bệnh nhân", "benh nhan",
    "trộm", "trom", "học sinh", "hoc sinh", "nhân viên", "nhan vien",
    "người dân", "nguoi dan", "phạm nhân", "pham nhan", "nghi phạm", "🔴"
]

def map_emotion(text: str) -> str:
    """Map Vietnamese / English emotion text to standard system emotion key."""
    if not text:
        return "normal"
    text_lower = text.strip().lower()
    for emotion_key, keywords in EMOTION_KEYWORDS:
        for kw in keywords:
            if kw in text_lower:
                return emotion_key
    return "normal"

def map_speaker(speaker_raw: str, row_idx: int, matchup_info: Optional[Dict[str, Any]] = None) -> str:
    """
    Map raw speaker name to 'speaker_a' or 'speaker_b'.
    Checks raw string against keywords or active matchup names.
    Fallback: Even row index -> speaker_a, Odd -> speaker_b.
    """
    if not speaker_raw:
        return "speaker_a" if row_idx % 2 == 0 else "speaker_b"
    
    clean_spk = speaker_raw.strip().lower()
    
    # Check matchup names if available
    if matchup_info:
        char_a_name = matchup_info.get("speaker_a_name", "").lower()
        char_b_name = matchup_info.get("speaker_b_name", "").lower()
        if char_a_name and char_a_name in clean_spk:
            return "speaker_a"
        if char_b_name and char_b_name in clean_spk:
            return "speaker_b"

    # Check Speaker A keywords
    for kw in SPEAKER_A_KEYWORDS:
        if kw in clean_spk:
            return "speaker_a"
            
    # Check Speaker B keywords
    for kw in SPEAKER_B_KEYWORDS:
        if kw in clean_spk:
            return "speaker_b"
            
    # Fallback by row index
    return "speaker_a" if row_idx % 2 == 0 else "speaker_b"

def _clean_text(val: Any) -> str:
    if val is None:
        return ""
    return str(val).strip()

def parse_excel_with_openpyxl(file_bytes: bytes) -> Tuple[List[List[str]], List[List[str]]]:
    """Parse sheets using openpyxl library."""
    import openpyxl
    wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
    sheet_names = wb.sheetnames
    
    sheet1_rows = []
    if len(sheet_names) > 0:
        ws1 = wb[sheet_names[0]]
        for row in ws1.iter_rows(values_only=True):
            sheet1_rows.append([_clean_text(cell) for cell in row])
            
    sheet2_rows = []
    if len(sheet_names) > 1:
        ws2 = wb[sheet_names[1]]
        for row in ws2.iter_rows(values_only=True):
            sheet2_rows.append([_clean_text(cell) for cell in row])
            
    return sheet1_rows, sheet2_rows

def parse_excel_with_zipxml(file_bytes: bytes) -> Tuple[List[List[str]], List[List[str]]]:
    """Zero-dependency fallback XML parser for .xlsx files using zipfile + ElementTree."""
    with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:
        shared_strings = []
        if 'xl/sharedStrings.xml' in z.namelist():
            tree = ET.fromstring(z.read('xl/sharedStrings.xml'))
            ns = {'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
            for elem in tree.findall('.//main:si', ns):
                t_parts = [t.text or '' for t in elem.findall('.//main:t', ns)]
                shared_strings.append("".join(t_parts))

        sheets_data = []
        sheet_files = sorted([f for f in z.namelist() if f.startswith('xl/worksheets/sheet') and f.endswith('.xml')])
        for sname in sheet_files[:2]:
            tree = ET.fromstring(z.read(sname))
            ns = {'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
            rows = []
            for row in tree.findall('.//main:row', ns):
                r_cells = []
                for cell in row.findall('main:c', ns):
                    cell_type = cell.attrib.get('t')
                    val = ""
                    if cell_type == 's':
                        v = cell.find('main:v', ns)
                        if v is not None and v.text and v.text.isdigit():
                            idx = int(v.text)
                            if 0 <= idx < len(shared_strings):
                                val = shared_strings[idx]
                    elif cell_type in ('inlineStr', 'str'):
                        t = cell.find('.//main:t', ns)
                        if t is not None and t.text:
                            val = t.text
                    else:
                        v = cell.find('main:v', ns)
                        if v is not None and v.text:
                            val = v.text
                    r_cells.append(_clean_text(val))
                rows.append(r_cells)
            sheets_data.append(rows)

        sheet1 = sheets_data[0] if len(sheets_data) > 0 else []
        sheet2 = sheets_data[1] if len(sheets_data) > 1 else []
        return sheet1, sheet2

def parse_csv_data(file_bytes: bytes) -> Tuple[List[List[str]], List[List[str]]]:
    """Parse CSV text into sheet1 format."""
    text = file_bytes.decode('utf-8-sig', errors='replace')
    reader = csv.reader(io.StringIO(text))
    rows = [[_clean_text(cell) for cell in row] for row in reader]
    return rows, []

def parse_script_file(file_bytes: bytes, filename: str, matchup_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Main entry point: Parse script Excel or CSV file.
    Returns:
    {
      "title_sub": str,
      "moral_lesson": str,
      "moral_lesson_vi": str,
      "dialogue": List[Dict[str, Any]]
    }
    """
    ext = os.path.splitext(filename)[1].lower()
    sheet1_rows: List[List[str]] = []
    sheet2_rows: List[List[str]] = []

    if ext in ['.csv', '.txt']:
        sheet1_rows, sheet2_rows = parse_csv_data(file_bytes)
    elif ext in ['.xlsx', '.xlsm', '.xls']:
        try:
            sheet1_rows, sheet2_rows = parse_excel_with_openpyxl(file_bytes)
        except Exception as e:
            logger.warning(f"openpyxl failed or not available ({e}), falling back to zipxml parser")
            sheet1_rows, sheet2_rows = parse_excel_with_zipxml(file_bytes)
    else:
        raise ValueError("Định dạng file không hỗ trợ! Vui lòng tải file .xlsx, .xls hoặc .csv")

    if not sheet1_rows:
        raise ValueError("File Excel/CSV không có dữ liệu!")

    # Find header row
    header_idx = -1
    col_map = {
        "speaker": -1,
        "emotion": -1,
        "jp_text": -1,
        "vi_text": -1,
        "stage": -1
    }

    for idx, row in enumerate(sheet1_rows[:5]):
        row_str = " ".join(row).lower()
        if any(kw in row_str for kw in ["nhân vật", "nhan vat", "cảm xúc", "cam xuc", "thoại", "thoai"]):
            header_idx = idx
            for col_i, cell in enumerate(row):
                c = cell.lower()
                if any(k in c for k in ["nhân vật", "nhan vat", "speaker", "character", "người nói"]):
                    col_map["speaker"] = col_i
                elif any(k in c for k in ["cảm xúc", "cam xuc", "emotion", "biểu cảm"]):
                    col_map["emotion"] = col_i
                elif any(k in c for k in ["nhật", "nhiệt", "japanese", "jp", "🇯🇵"]):
                    col_map["jp_text"] = col_i
                elif any(k in c for k in ["việt", "vietnamese", "vi", "🇻🇳"]):
                    col_map["vi_text"] = col_i
                elif any(k in c for k in ["dàn dựng", "nhịp cắt", "stage", "ghi chú"]):
                    col_map["stage"] = col_i
            break

    # If no header detected, use defaults
    if col_map["speaker"] == -1 and col_map["jp_text"] == -1:
        # Check standard layout: Col 2 Speaker, Col 3 Emotion, Col 4 JP, Col 5 VI
        col_map = {
            "speaker": 2,
            "emotion": 3,
            "jp_text": 4,
            "vi_text": 5,
            "stage": 6
        }

    data_rows = sheet1_rows[header_idx + 1:] if header_idx != -1 else sheet1_rows

    dialogue_list = []
    line_count = 0

    for row in data_rows:
        if not any(row):
            continue
            
        spk_raw = row[col_map["speaker"]] if 0 <= col_map["speaker"] < len(row) else ""
        emo_raw = row[col_map["emotion"]] if 0 <= col_map["emotion"] < len(row) else ""
        jp_raw = row[col_map["jp_text"]] if 0 <= col_map["jp_text"] < len(row) else ""
        vi_raw = row[col_map["vi_text"]] if 0 <= col_map["vi_text"] < len(row) else ""

        # Skip header-like rows that were missed
        if "nhân vật" in spk_raw.lower() or "thoại" in jp_raw.lower():
            continue

        # If both JP and VI text are empty, skip
        if not jp_raw and not vi_raw:
            continue

        # If JP is empty but VI has text (or vice versa), handle nicely
        if not jp_raw and vi_raw:
            jp_raw = vi_raw
        elif jp_raw and not vi_raw:
            vi_raw = jp_raw

        spk_key = map_speaker(spk_raw, line_count, matchup_info)
        emo_key = map_emotion(emo_raw)

        dialogue_list.append({
            "speaker": spk_key,
            "text": jp_raw,
            "emotion": emo_key,
            "text_vi": vi_raw
        })
        line_count += 1

    if not dialogue_list:
        raise ValueError("Không tìm thấy dòng thoại hợp lệ trong file Excel/CSV!")

    # Title & Moral Lesson extraction
    base_filename = os.path.splitext(filename)[0]
    clean_title_name = base_filename.replace("_", " ").replace("-", " ")
    
    title_sub = f"【裁判】{clean_title_name}"
    moral_lesson = ""
    moral_lesson_vi = ""

    # Check Sheet 2 for metadata
    if sheet2_rows:
        for r in sheet2_rows:
            if len(r) >= 2:
                key_col = r[0].lower()
                val_col = r[1]
                if any(k in key_col for k in ["bài học", "răn đe", "moral"]):
                    moral_lesson = val_col
                    moral_lesson_vi = val_col
                elif any(k in key_col for k in ["tiêu đề", "tên", "title"]):
                    title_sub = val_col

    return {
        "title_sub": title_sub,
        "moral_lesson": moral_lesson,
        "moral_lesson_vi": moral_lesson_vi,
        "dialogue": dialogue_list
    }
