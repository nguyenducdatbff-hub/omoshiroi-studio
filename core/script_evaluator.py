"""
OMOSHIROI - Jev / TypeSafe Script Evaluator
Module đánh giá kịch bản video ngắn trước khi render theo rubric viral-short-v1.
Chỉ đánh giá (Evaluate-only), không sửa kịch bản và không phân tích video MP4.
"""

import os
import json
import hashlib
import logging
import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("omoshiroi.evaluator")

# Phiên bản rubric
RUBRIC_VERSION = "viral-short-v1"
DEFAULT_MODEL = "jev-latest"
DEFAULT_TIMEOUT_SECONDS = 15.0

# Định nghĩa 4 tiêu chí và trọng số
DIMENSIONS_SPEC = {
    "hook_strength": {
        "name_vi": "Hook / Chặn lướt",
        "weight": 0.30,
        "instructions": (
            "Evaluate how strong and scroll-stopping the hook is in the first 1-3 seconds of the dialogue. "
            "Does it immediately grab the viewer's attention with a bizarre, shocking, or high-stakes detail?"
        ),
        "criteria": [
            "Mở đầu chung chung, cần nhiều ngữ cảnh, không có sự kiện hoặc mâu thuẫn",
            "Có chủ đề nhưng chưa có chi tiết cụ thể hoặc stakes",
            "Có tình huống đáng chú ý nhưng câu mở đầu còn dài hoặc dễ đoán",
            "Mở thẳng bằng chi tiết cụ thể, bất thường, mâu thuẫn hoặc hậu quả rõ",
            "Ngay câu đầu vừa cụ thể vừa bất ngờ, tạo câu hỏi bắt buộc phải xem tiếp"
        ]
    },
    "curiosity_emotion": {
        "name_vi": "Tò mò hoặc cảm xúc",
        "weight": 0.25,
        "instructions": (
            "Evaluate how well the script creates an open curiosity gap or sharp emotional reaction. "
            "Does the tension escalate instead of resolving the mystery too quickly?"
        ),
        "criteria": [
            "Không có câu hỏi mở, bất ngờ hoặc cảm xúc rõ",
            "Có tín hiệu tò mò/cảm xúc nhẹ nhưng giải đáp quá sớm",
            "Có một khoảng trống tò mò hoặc cảm xúc vừa phải",
            "Tò mò/cảm xúc tăng dần qua nhiều nhịp và chưa bị giải đáp sớm",
            "Mỗi nhịp mở thêm thông tin hoặc nâng stakes, tạo phản ứng cảm xúc mạnh"
        ]
    },
    "retention_payoff": {
        "name_vi": "Giữ chân và payoff",
        "weight": 0.25,
        "instructions": (
            "Evaluate pacing momentum and narrative payoff. Does every line advance the conflict, "
            "and does the conclusion answer the initial promise with a punchy satirical moral?"
        ),
        "criteria": [
            "Không có tiến triển hoặc không có kết thúc/payoff",
            "Có nhiều đoạn lặp, kết thúc không liên quan lời hứa đầu",
            "Có cấu trúc cơ bản nhưng phần giữa chùng hoặc payoff yếu",
            "Diễn biến gọn, mỗi đoạn có chức năng, payoff rõ",
            "Nhịp tăng liên tục, không có câu thừa, payoff vừa thỏa mãn vừa đáng nhớ"
        ]
    },
    "share_comment": {
        "name_vi": "Khả năng chia sẻ/bình luận",
        "weight": 0.20,
        "instructions": (
            "Evaluate how likely this script is to provoke debate, strong identification, "
            "tagging friends, or sharing in the comments section."
        ),
        "criteria": [
            "Không có góc nhìn, câu hỏi hoặc phản ứng đáng chia sẻ",
            "Nội dung dễ hiểu nhưng không tạo nhu cầu phản hồi",
            "Có một chi tiết relatable hoặc gây ý kiến trái chiều nhẹ",
            "Có lựa chọn đạo đức, twist hoặc tình huống khiến người xem muốn bình luận/tag",
            "Có tranh luận tự nhiên, bản sắc mạnh hoặc payoff khiến người xem muốn gửi ngay cho người khác"
        ]
    }
}

DEFAULT_RECOMMENDATIONS = {
    "hook_strength": {
        "code": "STRENGTHEN_HOOK",
        "message": "Đưa chi tiết bất thường/hậu quả cụ thể vào câu đầu; bỏ phần chào hỏi và setup có thể suy ra."
    },
    "curiosity_emotion": {
        "code": "RAISE_CURIOSITY_STAKES",
        "message": "Trì hoãn lời giải; thêm một thông tin làm tình huống khó hiểu hoặc stakes cao hơn ở nhịp kế tiếp."
    },
    "retention_payoff": {
        "code": "CUT_REPETITION_TIGHTEN_PAYOFF",
        "message": "Cắt câu lặp; mỗi 5–8 giây phải có thông tin, hành động hoặc đảo chiều mới; kết phải trả lời hook."
    },
    "share_comment": {
        "code": "PROVOKE_DEBATE",
        "message": "Thêm lựa chọn gây tranh luận, câu hỏi đạo đức hoặc góc nhìn khiến người xem muốn chọn phe."
    }
}


# ==========================================
# CÁC NGOẠI LỆ TỰ ĐỊNH NGHĨA (TYPED ERRORS)
# ==========================================

class EvaluatorError(Exception):
    """Lớp cha cho các ngoại lệ của module evaluator."""
    def __init__(self, code: str, message: str, status_code: int = 500):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


class EvaluatorValidationError(EvaluatorError):
    def __init__(self, message: str):
        super().__init__("INVALID_SCRIPT", message, status_code=400)


class EvaluatorConfigError(EvaluatorError):
    def __init__(self, message: str = "Chưa cấu hình TYPESAFE_API_KEY trên server."):
        super().__init__("TYPESAFE_NOT_CONFIGURED", message, status_code=503)


class EvaluatorTimeoutError(EvaluatorError):
    def __init__(self, message: str = "Không thể chấm điểm lúc này do quá thời gian chờ (15s). Bạn vẫn có thể xuất video."):
        super().__init__("TYPESAFE_TIMEOUT", message, status_code=504)


class EvaluatorUpstreamError(EvaluatorError):
    def __init__(self, message: str = "Dịch vụ TypeSafe trả về lỗi hoặc phản hồi không hợp lệ. Bạn vẫn có thể xuất video."):
        super().__init__("TYPESAFE_UPSTREAM_ERROR", message, status_code=502)


# ==========================================
# CÁC HÀM THUẦN (PURE FUNCTIONS ĐỂ KIỂM THỬ)
# ==========================================

def calculate_viral_score(scores: Dict[str, float]) -> int:
    """
    Tính điểm tổng hợp viral_score (0-100) theo công thức Section 6.3:
    viral_score = round(100 * sum(weight * score / 4))
    """
    weighted_sum = 0.0
    for dim_key, dim_info in DIMENSIONS_SPEC.items():
        score_val = float(scores.get(dim_key, 0.0))
        # Kẹp điểm trong khoảng 0.0 - 4.0
        clamped_score = max(0.0, min(4.0, score_val))
        weighted_sum += dim_info["weight"] * (clamped_score / 4.0)
    
    return int(round(100.0 * weighted_sum))


def classify_score(score: int) -> str:
    """
    Phân loại điểm tổng quát:
    75-100: recommended
    60-74: revise
    0-59: major_revision
    """
    if score >= 75:
        return "recommended"
    if score >= 60:
        return "revise"
    return "major_revision"


def fingerprint_state(state: Dict[str, Any]) -> str:
    """
    Tạo mã băm SHA-256 xác thực state canonical, dùng để phát hiện đánh giá đã cũ (stale).
    """
    # Chỉ băm các trường cốt lõi ảnh hưởng đến kịch bản
    canonical_payload = {
        "platform": state.get("platform", "tiktok"),
        "content_profile": state.get("content_profile", "irasutoya_short"),
        "target_audience": state.get("target_audience", ""),
        "target_duration_seconds": state.get("target_duration_seconds", 45),
        "matchup": state.get("matchup", ""),
        "title_main": state.get("title_main", ""),
        "title_sub": state.get("title_sub", ""),
        "moral_lesson": state.get("moral_lesson", ""),
        "dialogue": [
            {
                "speaker": d.get("speaker") or "",
                "text": d.get("text") or "",
                "text_vi": d.get("text_vi") or "",
                "emotion": d.get("emotion") or "normal"
            }
            for d in state.get("dialogue", [])
        ]

    }
    dumped = json.dumps(canonical_payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return f"sha256:{hashlib.sha256(dumped.encode('utf-8')).hexdigest()}"


def build_recommendations(dimensions: Dict[str, Any], state: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Ánh xạ các điểm yếu sang tối đa 3 khuyến nghị ngắn gọn, có thể hành động được:
    - Ưu tiên tiêu chí có weighted_gap = weight * (4 - score) lớn nhất.
    - Không khuyến nghị duy nhất dựa trên tiêu chí uncertain (confidence < 0.45).
    - Hỗ trợ khuyến nghị thích ứng cho asian_myth_3d.
    """
    gaps = []
    content_profile = state.get("content_profile", "irasutoya_short")

    for dim_key, dim_info in DIMENSIONS_SPEC.items():
        dim_data = dimensions.get(dim_key, {})
        score = float(dim_data.get("score", 0.0))
        confidence = float(dim_data.get("confidence", 1.0))
        uncertain = dim_data.get("uncertain", confidence < 0.45)
        
        weight = dim_info["weight"]
        gap = weight * (4.0 - score)
        
        if gap > 0.05 and not uncertain:  # Không suy ra khuyến nghị chỉ từ điểm thiếu tin cậy
            gaps.append({
                "dim_key": dim_key,
                "gap": gap,
                "score": score,
                "uncertain": uncertain
            })

    # Sắp xếp theo weighted_gap giảm dần
    gaps.sort(key=lambda x: x["gap"], reverse=True)

    recommendations = []
    for item in gaps[:3]:
        dim_key = item["dim_key"]
        rec = DEFAULT_RECOMMENDATIONS[dim_key].copy()
        
        # Quy tắc đặc thù cho asian_myth_3d
        if content_profile == "asian_myth_3d" and dim_key == "hook_strength":
            rec = {
                "code": "STRENGTHEN_HOOK_LONG_FORM",
                "message": "Dùng mini-hook hoặc bước ngoặt kịch tính ở phần đầu thay vì dồn toàn bộ setup vào 3 giây."
            }
            
        recommendations.append({
            "code": rec["code"],
            "dimension": dim_key,
            "message": rec["message"]
        })

    return recommendations


def sanitize_and_validate_state(script_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Chuẩn hóa và kiểm tra giới hạn của kịch bản đầu vào:
    - Tối đa 100 câu thoại.
    - Tối đa 12.000 ký tự sau serialize.
    - Loại bỏ thông tin nhạy cảm, secrets, internal paths.
    """
    if not script_data:
        raise EvaluatorValidationError("Dữ liệu kịch bản không được để trống.")

    title_sub = (script_data.get("title_sub") or "").strip()
    if not title_sub:
        raise EvaluatorValidationError("Thiếu tiêu đề kịch bản (title_sub).")

    dialogue_raw = script_data.get("dialogue") or []
    if not isinstance(dialogue_raw, list) or len(dialogue_raw) == 0:
        raise EvaluatorValidationError("Kịch bản phải có ít nhất 1 dòng thoại.")

    if len(dialogue_raw) > 100:
        raise EvaluatorValidationError(f"Kịch bản vượt quá giới hạn 100 câu thoại (hiện có {len(dialogue_raw)} câu).")

    sanitized_dialogue = []
    for idx, d in enumerate(dialogue_raw):
        if not isinstance(d, dict):
            raise EvaluatorValidationError(f"Dòng thoại thứ {idx + 1} không hợp lệ.")
        speaker = str(d.get("speaker") or "speaker").strip()
        text = str(d.get("text") or "").strip()
        text_vi = str(d.get("text_vi") or "").strip() if d.get("text_vi") else None
        emotion = str(d.get("emotion") or "normal").strip()

        if not text:
            raise EvaluatorValidationError(f"Dòng thoại thứ {idx + 1} không có nội dung chữ.")

        item = {
            "speaker": speaker,
            "text": text,
            "emotion": emotion
        }
        if text_vi:
            item["text_vi"] = text_vi
        sanitized_dialogue.append(item)

    clean_state = {
        "platform": str(script_data.get("platform") or "tiktok").strip().lower(),
        "content_profile": str(script_data.get("content_profile") or "irasutoya_short").strip(),
        "target_audience": str(script_data.get("target_audience") or "Người xem Việt Nam thích anime và hài châm biếm").strip(),
        "target_duration_seconds": int(script_data.get("target_duration_seconds") or 45),
        "matchup": str(script_data.get("matchup") or "").strip(),
        "title_main": str(script_data.get("title_main") or "").strip(),
        "title_sub": title_sub,
        "moral_lesson": str(script_data.get("moral_lesson") or "").strip(),
        "dialogue": sanitized_dialogue,
        "estimated_duration_seconds": int(script_data.get("estimated_duration_seconds") or script_data.get("target_duration_seconds") or 45)
    }

    serialized = json.dumps(clean_state, ensure_ascii=False)
    if len(serialized) > 12000:
        raise EvaluatorValidationError(f"Kịch bản vượt quá giới hạn 12.000 ký tự (hiện có {len(serialized)} ký tự).")

    return clean_state


# ==========================================
# ENGINE ĐÁNH GIÁ CHÍNH
# ==========================================

async def evaluate_script(
    script_data: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None,
    api_key: Optional[str] = None,
    client: Any = None
) -> Dict[str, Any]:
    """
    Thực hiện chấm điểm kịch bản bằng Jev / TypeSafe System One API.
    Hỗ trợ mock client phục vụ unit testing mà không cần gọi API thật.
    """
    start_time = datetime.now(timezone.utc)
    clean_state = sanitize_and_validate_state(script_data)
    fingerprint = fingerprint_state(clean_state)

    # Lấy API Key và Model từ môi trường nếu không truyền vào
    resolved_api_key = api_key or os.environ.get("TYPESAFE_API_KEY")
    resolved_model = os.environ.get("TYPESAFE_MODEL", DEFAULT_MODEL)
    try:
        resolved_timeout = float(os.environ.get("TYPESAFE_TIMEOUT_SECONDS", str(DEFAULT_TIMEOUT_SECONDS)))
    except (ValueError, TypeError):
        resolved_timeout = DEFAULT_TIMEOUT_SECONDS

    if not client and not resolved_api_key:
        raise EvaluatorConfigError("Chưa cấu hình TYPESAFE_API_KEY trên server.")

    # Chuẩn bị câu hỏi (Score primitives)
    try:
        from typesafe_sdk import Score
    except ImportError:
        raise EvaluatorUpstreamError(
            "Thiếu TypeSafe SDK trên môi trường này. Hãy cài dependencies bằng pip install -r requirements.txt."
        ) from None

    questions = {}
    for dim_key, dim_info in DIMENSIONS_SPEC.items():
        questions[dim_key] = Score(
            instructions=dim_info["instructions"],
            criteria=dim_info["criteria"]
        )

    # Gọi API TypeSafe
    try:
        if client is not None:
            # Client được inject phục vụ testing
            response = await client.system_one(
                state=clean_state,
                questions=questions,
                model=resolved_model,
                timeout=resolved_timeout
            )
        else:
            from typesafe_sdk import AsyncTypeSafeClient
            async with AsyncTypeSafeClient(api_key=resolved_api_key) as active_client:
                response = await active_client.system_one(
                    state=clean_state,
                    questions=questions,
                    model=resolved_model,
                    timeout=resolved_timeout
                )
    except EvaluatorError:
        raise
    except Exception as exc:
        err_type = type(exc).__name__
        # Không ghi/log nội dung exception: upstream có thể chứa dữ liệu nhạy cảm.
        logger.warning("TypeSafe API invocation failed (%s)", err_type)

        if "timeout" in err_type.lower():
            raise EvaluatorTimeoutError() from None
        if "auth" in err_type.lower() or "unauthorized" in err_type.lower():
            raise EvaluatorUpstreamError("TypeSafe từ chối xác thực. Hãy kiểm tra cấu hình API key trên server.") from None
        raise EvaluatorUpstreamError() from None

    # Phân tích và trích xuất điểm từng tiêu chí
    raw_answers = getattr(response, "answers", None)
    if raw_answers is None and isinstance(response, dict):
        raw_answers = response.get("answers", {})

    if not isinstance(raw_answers, dict) or not raw_answers:
        raise EvaluatorUpstreamError("Phản hồi từ TypeSafe không chứa kết quả chấm điểm hợp lệ.")

    dim_results = {}
    scores_for_total = {}
    confidences = []

    for dim_key, dim_info in DIMENSIONS_SPEC.items():
        ans = raw_answers.get(dim_key)
        if ans is None:
            raise EvaluatorUpstreamError(f"Phản hồi từ TypeSafe thiếu tiêu chí bắt buộc: '{dim_key}'.")

        # Hỗ trợ cả SDK object và dict
        try:
            score_val = float(getattr(ans, "score", None) if hasattr(ans, "score") else ans.get("score"))
            conf_val = float(getattr(ans, "confidence", None) if hasattr(ans, "confidence") else ans.get("confidence"))
        except (TypeError, ValueError, AttributeError):
            raise EvaluatorUpstreamError("Phản hồi từ TypeSafe có điểm hoặc confidence không hợp lệ.") from None
        if not math.isfinite(score_val) or not 0 <= score_val <= 4:
            raise EvaluatorUpstreamError("Phản hồi từ TypeSafe có điểm ngoài khoảng 0–4.")
        if not math.isfinite(conf_val) or not 0 <= conf_val <= 1:
            raise EvaluatorUpstreamError("Phản hồi từ TypeSafe có confidence ngoài khoảng 0–1.")
        
        prob_raw = getattr(ans, "probabilities", None) if hasattr(ans, "probabilities") else ans.get("probabilities")
        prob_list = None
        if prob_raw is not None:
            if isinstance(prob_raw, dict):
                # Sắp xếp theo key số 0, 1, 2, 3, 4
                try:
                    prob_list = [float(prob_raw.get(k, prob_raw.get(str(k)))) for k in range(5)]
                except (TypeError, ValueError):
                    raise EvaluatorUpstreamError("Phản hồi từ TypeSafe có probabilities không hợp lệ.") from None
            elif isinstance(prob_raw, list):
                try:
                    prob_list = [float(p) for p in prob_raw]
                except (TypeError, ValueError):
                    raise EvaluatorUpstreamError("Phản hồi từ TypeSafe có probabilities không hợp lệ.") from None
            else:
                raise EvaluatorUpstreamError("Phản hồi từ TypeSafe có probabilities không hợp lệ.")
            if (len(prob_list) != 5 or any(not math.isfinite(p) or p < 0 or p > 1 for p in prob_list)
                    or not 0.95 <= sum(prob_list) <= 1.05):
                raise EvaluatorUpstreamError("Phản hồi từ TypeSafe có probabilities không hợp lệ.")

        is_uncertain = conf_val < 0.45

        dim_results[dim_key] = {
            "score": round(score_val, 2),
            "normalized": round(score_val / 4.0, 4),
            "confidence": round(conf_val, 2),
            "uncertain": is_uncertain,
            "probabilities": prob_list
        }
        scores_for_total[dim_key] = score_val
        confidences.append(dim_info["weight"] * conf_val)

    # Tính điểm tổng hợp và phân loại
    viral_score = calculate_viral_score(scores_for_total)
    classification = classify_score(viral_score)
    overall_confidence = round(sum(confidences), 2)

    # Tìm weakest_dimension theo weighted gap
    weakest_dim = max(
        DIMENSIONS_SPEC.keys(),
        key=lambda k: DIMENSIONS_SPEC[k]["weight"] * (4.0 - dim_results[k]["score"])
    )

    # Tạo khuyến nghị
    recommendations = build_recommendations(dim_results, clean_state)

    evaluated_at = datetime.now(timezone.utc).isoformat()
    latency_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)

    # Log sự kiện có cấu trúc (không chứa API key hay full text nhạy cảm)
    logger.info(
        json.dumps({
            "event": "script_evaluated",
            "model": resolved_model,
            "rubric_version": RUBRIC_VERSION,
            "latency_ms": latency_ms,
            "viral_score": viral_score,
            "classification": classification,
            "content_profile": clean_state.get("content_profile"),
            "success": True
        })
    )

    return {
        "status": "ok",
        "model": getattr(response, "model", resolved_model) or resolved_model,
        "rubric_version": RUBRIC_VERSION,
        "viral_score": viral_score,
        "classification": classification,
        "overall_confidence": overall_confidence,
        "dimensions": dim_results,
        "weakest_dimension": weakest_dim,
        "recommendations": recommendations,
        "warnings": [f"Tiêu chí '{weakest_dim}' có độ tin cậy thấp ({dim_results[weakest_dim]['confidence']})"] if dim_results[weakest_dim]["uncertain"] else [],
        "evaluated_at": evaluated_at,
        "input_fingerprint": fingerprint,
        "platform": clean_state["platform"],
        "content_profile": clean_state["content_profile"],
        "target_audience": clean_state["target_audience"],
        "target_duration_seconds": clean_state["target_duration_seconds"]
    }
