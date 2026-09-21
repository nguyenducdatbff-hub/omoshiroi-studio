import json
import os
from core.character_registry import get_matchup, get_character


class GeminiGenerationError(Exception):
    """A safe, user-facing Gemini failure message."""


def gemini_error_message(error):
    code = getattr(error, "code", None)
    message = str(getattr(error, "message", "") or "").lower()
    if code in (400, 401) and "key" in message:
        return f"Gemini từ chối API key ({code}). Hãy kiểm tra hoặc tạo key mới trong Google AI Studio."
    if code in (401, 403):
        return f"Gemini từ chối quyền truy cập ({code}). Hãy kiểm tra trạng thái và giới hạn key trong Google AI Studio."
    if code == 429:
        return "Gemini đã hết hạn mức hoặc đang giới hạn yêu cầu (429). Hãy kiểm tra quota trong Google AI Studio."
    if code == 503:
        return "Gemini đang quá tải hoặc tạm ngưng (503). Hãy thử lại sau ít phút."
    if code == 404:
        return "Gemini không tìm thấy model đang dùng (404). Hãy kiểm tra quyền truy cập model."
    if code:
        return f"Gemini không tạo được kịch bản (mã {code}). Hãy thử lại hoặc kiểm tra Google AI Studio."
    if isinstance(error, (json.JSONDecodeError, AttributeError)):
        return "Gemini trả về kịch bản không đúng định dạng. Hãy thử lại."
    return "Không kết nối hoặc xử lý được phản hồi từ Gemini. Hãy kiểm tra mạng rồi thử lại."

PRESET_SCRIPTS = [
    # 1. Tòa Án (Courtroom)
    {
        "id": "sushi_terrorist",
        "matchup": "courtroom",
        "title_main": "サクッと笑える",
        "title_sub": "【裁判】スシロー迷惑テロの末路",
        "topic": "迷惑行為・炎上",
        "topic_vi": "Sống ảo phá hoại quán ăn",
        "moral_lesson": "ネットの10秒の目立ちたがり、代償は数千万円の借金地獄。",
        "moral_lesson_vi": "10 giây thể hiện sống ảo trên mạng, cái giá phải trả là địa ngục nợ nần hàng chục triệu Yên.",
        "dialogue": [
            {
                "speaker": "judge",
                "text": "被告人、前へ！回転寿司の「醤油差しを舐めた罪」、認めるか？",
                "text_vi": "Bị cáo, bước lên! Ngươi có nhận tội 「liếm chai xì dầu」 ở quán sushi băng chuyền không?",
                "emotion": "normal"
            },
            {
                "speaker": "prisoner",
                "text": "裁判長！あれは「除菌チェック」だったんです！悪気はありません！",
                "text_vi": "Thưa chủ tọa! Đó chỉ là 「kiểm tra khử khuẩn」 thôi ạ! Tôi không hề có ác ý!",
                "emotion": "sweat"
            },
            {
                "speaker": "judge",
                "text": "バカを言うな！店側から「6700万円」の損害賠償を請求されておるぞ！",
                "text_vi": "Đừng nói nhảm! Phía nhà hàng đang kiện đòi bồi thường thiệt hại 「67 triệu Yên」 kìa!",
                "emotion": "angry"
            },
            {
                "speaker": "prisoner",
                "text": "ろ、6700万！？僕のお小遣い「月3000円」なんですけど…",
                "text_vi": "6... 67 triệu Yên á!? Tiền tiêu vặt của tôi mỗi tháng chỉ có 「3.000 Yên」 thôi mà...",
                "emotion": "shocked"
            },
            {
                "speaker": "judge",
                "text": "主文！被告人を「一生自炊の刑」に処する！二度と皿を舐めるな！",
                "text_vi": "Tuyên án! Phạt bị cáo 「tội tự nấu ăn cả đời」! Cấm tiệt không được liếm đĩa nữa!",
                "emotion": "normal"
            },
            {
                "speaker": "prisoner",
                "text": "そんなぁ〜！一生外食禁止ですかー！？",
                "text_vi": "Trời đất ơi~! Chẳng lẽ cấm tôi đi ăn ngoài cả đời sao trời!?",
                "emotion": "shocked"
            }
        ]
    },

    # 2. Đồn Cảnh Sát (Koban)
    {
        "id": "cosme_shoplifting",
        "matchup": "koban",
        "title_main": "サクッと笑える",
        "title_sub": "【警察】高級コスメを万引きした女",
        "topic": "万引き・窃盗",
        "topic_vi": "Trộm mỹ phẩm cao cấp",
        "moral_lesson": "美しさは盗めない。一瞬の虚栄心で失うのは一生の信用。",
        "moral_lesson_vi": "Vẻ đẹp không thể trộm cắp. Một giây phù phiếm sẽ đánh mất danh dự cả đời.",
        "dialogue": [
            {
                "speaker": "police",
                "text": "おい！お前、ドラッグストアで「高級化粧品」をカバンに入れたな？",
                "text_vi": "Này! Cô vừa lén nhét 「mỹ phẩm cao cấp」 vào túi xách ở cửa hàng đúng không?",
                "emotion": "normal"
            },
            {
                "speaker": "citizen_female",
                "text": "ち、違います！お肌の「緊急パッチテスト」をしてただけです！",
                "text_vi": "Đ, đâu có! Tôi chỉ đang làm 「thử nghiệm da khẩn cấp」 thôi mà!",
                "emotion": "sweat"
            },
            {
                "speaker": "police",
                "text": "防犯カメラに「10本全部」ポッケに突っ込む姿がバッチリ映っとるぞ。",
                "text_vi": "Camera an ninh quay rõ mồn một cảnh cô nhét 「cả 10 thỏi son」 vào túi đấy.",
                "emotion": "normal"
            },
            {
                "speaker": "citizen_female",
                "text": "えっ！？あのカメラ…ダミーじゃなかったんですか！？",
                "text_vi": "Hả!? Cái camera đó... không phải là camera giả gắn tượng trưng sao trời!?",
                "emotion": "shocked"
            },
            {
                "speaker": "police",
                "text": "ほな署でゆっくり「事情聴取」や！メイク落とし持参で来い！",
                "text_vi": "Thế thì về đồn mà từ từ 「lấy lời khai」 nhé! Nhớ mang theo nước tẩy trang đấy!",
                "emotion": "angry"
            },
            {
                "speaker": "citizen_female",
                "text": "すっぴん晒されるのは勘弁してください〜！！",
                "text_vi": "Xin đừng bắt tôi để mặt mộc mà hu hu~!!",
                "emotion": "shocked"
            }
        ]
    },

    # 3. Bệnh Viện & Bác Sĩ Google (Hospital)
    {
        "id": "doctor_google",
        "matchup": "hospital",
        "title_main": "サクッと笑える",
        "title_sub": "【診察室】Googleで不治の病になった男",
        "topic": "自己診断・ネット検索",
        "topic_vi": "Bác sĩ Google & Bệnh nhân đòi viết di chúc",
        "moral_lesson": "ネットの自己診断は病気より危険。不安なら検索する前に病院へ行け。",
        "moral_lesson_vi": "Tự chẩn đoán trên mạng còn nguy hiểm hơn bệnh tật. Lo lắng thì hãy đi khám bác sĩ thay vì tự tra Google.",
        "dialogue": [
            {
                "speaker": "patient",
                "text": "先生！助けてください！僕の余命…あと「3日」なんです！遺言書にサインを！",
                "text_vi": "Bác sĩ ơi cứu tôi với! Tôi chỉ còn sống được 「3 ngày」 nữa thôi! Bác sĩ ký làm chứng di chúc với!",
                "emotion": "shocked"
            },
            {
                "speaker": "doctor",
                "text": "ちょ、落ち着け！何があった？どんな「重篤な症状」が出てるんだ？",
                "text_vi": "Khoan đã, bình tĩnh ngồi xuống! Cậu bị 「triệu chứng nghiêm trọng」 cỡ nào?",
                "emotion": "normal"
            },
            {
                "speaker": "patient",
                "text": "昨晩、激辛ラーメン食べたらお腹が鳴って…検索したら「死亡率99%の奇病」って！",
                "text_vi": "Tối qua ăn mì cay xong bụng cứ sôi ùng ục... Lên mạng tra thì nó bảo là 「bệnh lạ tử vong 99%」!",
                "emotion": "sweat"
            },
            {
                "speaker": "doctor",
                "text": "レントゲン撮ったぞ。診断結果は…ただの「オナラの我慢しすぎ」だ！ガスが溜まっとるだけ！",
                "text_vi": "Phim chụp có rồi đây. Chẩn đoán chính xác là... cậu chỉ bị 「nhịn đánh rắm quá lâu」 thôi! Đầy hơi nghẽn ruột!",
                "emotion": "angry"
            },
            {
                "speaker": "doctor",
                "text": "遺言書書く前に、早くトイレ行って「全弾発射」してこい！！",
                "text_vi": "Trước khi viết di chúc, mau chạy vào nhà vệ sinh mà 「xả hết van ga」 đi giùm tôi cái!!",
                "emotion": "angry"
            },
            {
                "speaker": "patient",
                "text": "ええっ！？僕の涙の遺言書…ただの「オナラ」で無効ですかーー！？",
                "text_vi": "Hả trời đất ơi!? Tờ di chúc tiền tỷ của tôi... lại bị vô hiệu hóa bởi một cú 「xì hơi」 sao trờiーー!?",
                "emotion": "shocked"
            }
        ]
    },

    # 4. Công Sở & Gen Z (Office)
    {
        "id": "genz_overtime",
        "matchup": "office",
        "title_main": "サクッと笑える",
        "title_sub": "【オフィス】定時1秒で帰るZ世代社員",
        "topic": "定時退社・ワークライフバランス",
        "topic_vi": "Nhân viên Gen Z tan làm đúng 17:00 từ chối OT",
        "moral_lesson": "権利を主張するなら義務も果たせ。信頼は小さな誠実さの積み重ね。",
        "moral_lesson_vi": "Muốn đòi hỏi quyền lợi thì phải hoàn thành nghĩa vụ. Sự tín nhiệm được xây dựng từ trách nhiệm mỗi ngày.",
        "dialogue": [
            {
                "speaker": "boss",
                "text": "おい！もう「17時01分」だが、クライアントへの重要メール送ったのか！？",
                "text_vi": "Này! Đã 「17 giờ 01 phút」 rồi đấy, cậu đã gửi email quan trọng cho đối tác chưa!?",
                "emotion": "angry"
            },
            {
                "speaker": "worker",
                "text": "部長、私の定時は「17時00分」です。1分過ぎてるので業務終了でーす！",
                "text_vi": "Trưởng phòng ơi, giờ tan làm của em là 「17 giờ 00」. Quá 1 phút rồi nên em hết nhiệm vụ nhé!",
                "emotion": "normal"
            },
            {
                "speaker": "boss",
                "text": "馬鹿者！「契約金5000万円」がかかっとるんだぞ！明日じゃ遅いんだ！",
                "text_vi": "Đồ ngốc! Hợp đồng này trị giá 「50 triệu Yên」 đấy! Đến mai thì khách hủy mất!",
                "emotion": "angry"
            },
            {
                "speaker": "worker",
                "text": "タイパ重視なんで、残業は「1分あたり1万円」の手当なら考えますけど？",
                "text_vi": "Em sống theo hệ tối ưu thời gian, tăng ca phải trả 「10.000 Yên mỗi phút」 thì em mới nghĩ lại nha?",
                "emotion": "sweat"
            },
            {
                "speaker": "boss",
                "text": "よし分かった！お前の席のタイパも考えた！明日から「無期限テレワーク」や！",
                "text_vi": "Được lắm! Tôi cũng tối ưu luôn chỗ ngồi của cậu! Từ mai 「làm việc từ xa vô thời hạn」 luôn đi!",
                "emotion": "normal"
            },
            {
                "speaker": "worker",
                "text": "えっ…それって実質「クビ」ってことですかーー！？",
                "text_vi": "Hả... nói vậy chẳng khác nào em bị 「đuổi việc」 luôn rồi sao sếpーー!?",
                "emotion": "shocked"
            }
        ]
    },

    # 5. Học Đường & Lớp Học (School)
    {
        "id": "school_ai_cheat",
        "matchup": "school",
        "title_main": "サクッと笑える",
        "title_sub": "【学園】ChatGPTで読書感想文を書いた生徒",
        "topic": "AI不正・宿題カンニング",
        "topic_vi": "Dùng AI viết văn cảm nghĩ bị giáo viên bắt bài",
        "moral_lesson": "AIは道具であって自分の頭ではない。ズルで得た点数は何の力にもならない。",
        "moral_lesson_vi": "AI chỉ là công cụ chứ không thay thế được tư duy. Điểm số gian lận không bao giờ trở thành thực lực.",
        "dialogue": [
            {
                "speaker": "teacher",
                "text": "山田！お前の読書感想文、やけに「哲学的で文豪レベル」なのは何故だ？",
                "text_vi": "Yamada! Bài văn cảm nghĩ của em, sao tự dưng lại 「triết lý tầm cỡ đại văn hào」 thế này?",
                "emotion": "normal"
            },
            {
                "speaker": "boy",
                "text": "先生！僕の「隠れた文才」がついに覚醒したんですよ！徹夜で書きました！",
                "text_vi": "Thưa thầy! 「Thiên phú văn học」 tiềm ẩn của em cuối cùng đã thức tỉnh đấy ạ! Em thức trắng đêm viết đó!",
                "emotion": "sweat"
            },
            {
                "speaker": "teacher",
                "text": "ほな聞くが、最後の行の「AIとしてお答えします」は何のギャグや！？",
                "text_vi": "Thế thầy hỏi em, dòng cuối cùng có chữ 「Với tư cách là mô hình AI...」 là tấu hài kiểu gì hả!?",
                "emotion": "angry"
            },
            {
                "speaker": "boy",
                "text": "ぎゃああ！コピペの「末尾の挨拶」消し忘れてたーー！！",
                "text_vi": "Ái chà chà! Em quên xóa dòng 「chào tạm biệt」 cuối đoạn copy paste rồiーー!!",
                "emotion": "shocked"
            },
            {
                "speaker": "teacher",
                "text": "罰として！原稿用紙「50枚」に手書きで反省文を提出せよ！",
                "text_vi": "Phạt em chép phạt bản tự kiểm điểm 「50 trang giấy thi」 bằng bút mực nộp cho tôi!",
                "emotion": "angry"
            },
            {
                "speaker": "boy",
                "text": "手書き50枚！？僕の右手が爆発しちゃいますーー！！",
                "text_vi": "Viết tay 50 trang á!? Tay em sẽ gãy mất thôi thầy ơiーー!!",
                "emotion": "shocked"
            }
        ]
    },

    # 6. Cửa Hàng Tiện Lợi (Conbini)
    {
        "id": "conbini_refund",
        "matchup": "conbini",
        "title_main": "サクッと笑える",
        "title_sub": "【コンビニ】完食してから「不味い」と返品を迫る客",
        "topic": "理不尽クレーム・モンスター客",
        "topic_vi": "Khách ăn hết nửa hộp cơm rồi đòi đổi trả",
        "moral_lesson": "店員はお前の召使いではない。礼儀を知らぬ者に人としての尊厳なし。",
        "moral_lesson_vi": "Nhân viên phục vụ không phải là người hầu. Kẻ không biết tôn trọng người khác sẽ không nhận lại sự tôn trọng.",
        "dialogue": [
            {
                "speaker": "customer",
                "text": "おい店員！この唐揚げ弁当「味が薄くてクソ不味かった」ぞ！今すぐ全額返金しろ！",
                "text_vi": "Này nhân viên! Hộp cơm gà rán này 「dở tệ nhạt thếch」! Mau hoàn tiền 100% cho tôi ngay!",
                "emotion": "angry"
            },
            {
                "speaker": "clerk",
                "text": "お客様…お弁当の容器、米粒一つ残らず「完食」されておられますが…",
                "text_vi": "Dạ thưa quý khách... nhưng hộp cơm của quý khách không còn sót lại dù chỉ 「1 hạt cơm」 nào ạ...",
                "emotion": "sweat"
            },
            {
                "speaker": "customer",
                "text": "毒が入ってないか「命がけで検証」してやったんだよ！感謝しろ！",
                "text_vi": "Tôi phải 「đánh cược mạng sống ăn hết」 để kiểm tra xem có độc không đấy! Phải biết ơn tôi đi chứ!",
                "emotion": "normal"
            },
            {
                "speaker": "clerk",
                "text": "それなら安心ですね！当店自慢の「空容器リサイクル料1000円」頂戴いたします！",
                "text_vi": "Thế thì yên tâm quá ạ! Xin phép thu thêm 「1.000 Yên phí tái chế hộp rỗng」 của cửa hàng nhé!",
                "emotion": "normal"
            },
            {
                "speaker": "customer",
                "text": "はあ！？なんでゴミ箱に捨てるだけで金取られんだよ！！",
                "text_vi": "Hả!? Tại sao vứt hộp rỗng vào thùng rác mà lại bị đòi tiền là sao trời!!",
                "emotion": "shocked"
            },
            {
                "speaker": "clerk",
                "text": "またの「命がけのご来店」を心よりお待ちしております♪",
                "text_vi": "Rất mong được tiếp đón lần 「đánh cược mạng sống」 tiếp theo của quý khách ạ♪",
                "emotion": "normal"
            }
        ]
    },

    # 7. Phỏng Vấn Xin Việc (Interview)
    {
        "id": "interview_exaggeration",
        "matchup": "interview",
        "title_main": "サクッと笑える",
        "title_sub": "【面接】履歴書を盛りすぎて自爆した就活生",
        "topic": "学歴経歴詐称・就職活動",
        "topic_vi": "Ứng viên nổ CV biết 10 thứ tiếng đòi lương nghìn đô",
        "moral_lesson": "身の丈に合わない嘘はすぐバレる。最大の武器は背伸びしない誠実さ。",
        "moral_lesson_vi": "Lời nói dối quá đà sớm muộn cũng bị vạch trần. Vũ khí mạnh nhất luôn là sự chân thành và năng lực thực tế.",
        "dialogue": [
            {
                "speaker": "interviewer",
                "text": "履歴書を拝見しました。「英語・中国語・フランス語がネイティブ級」とありますが？",
                "text_vi": "Tôi đã xem qua CV. Em ghi ở đây là 「thông thạo như người bản xứ tiếng Anh, Trung, Pháp」 đúng không?",
                "emotion": "normal"
            },
            {
                "speaker": "candidate",
                "text": "はい！世界中を飛び回るビジネスリーダーになるのが「私の天命」ですから！",
                "text_vi": "Dạ đúng ạ! Trở thành nhà lãnh đạo kinh doanh toàn cầu chính là 「sứ mệnh cuộc đời em」 mà!",
                "emotion": "sweat"
            },
            {
                "speaker": "interviewer",
                "text": "Alors, parlez-moi de votre projet. (ではフランス語で自己PRをどうぞ)",
                "text_vi": "Alors, parlez-moi de votre projet. (Vậy mời em giới thiệu bản thân bằng tiếng Pháp nào)",
                "emotion": "normal"
            },
            {
                "speaker": "candidate",
                "text": "え…あ…ボンジュール！…クロワッサン！…オ・トワレ・スィル・ヴ・プレ…！",
                "text_vi": "Ơ... dạ... Bonjour! ...Croissant! ...Où sont les toilettes s'il vous plaît... (Toilet ở đâu ạ)...!",
                "emotion": "shocked"
            },
            {
                "speaker": "interviewer",
                "text": "不採用！パン屋とトイレしか行けないグローバル人材はお断りです！",
                "text_vi": "Trượt phỏng vấn! Công ty tôi không nhận nhân tài toàn cầu chỉ biết mua bánh sừng bò và đi vệ sinh!",
                "emotion": "angry"
            },
            {
                "speaker": "candidate",
                "text": "メルシーボクゥゥゥーー！！（ありがとうございました…）",
                "text_vi": "Merci beaucoup hu hu huーー!! (Cảm ơn nhà tuyển dụng ạ...)",
                "emotion": "shocked"
            }
        ]
    },

    # 8. Hẹn Hò Drama (Dating)
    {
        "id": "dating_split_bill",
        "matchup": "dating",
        "title_main": "サクッと笑える",
        "title_sub": "【デート】初デートで「1円単位」の割り勘を迫る男",
        "topic": "ケチ彼氏・初デート修羅場",
        "topic_vi": "Buổi hẹn hò đầu chia tiền đến từng 1 Yên",
        "moral_lesson": "お金のケチさは心のケチさ。大切な人を計算機で測るな。",
        "moral_lesson_vi": "Bủn xỉn về tiền bạc cũng là bủn xỉn về tâm hồn. Đừng bao giờ đong đếm người mình thương bằng máy tính bỏ túi.",
        "dialogue": [
            {
                "speaker": "boyfriend",
                "text": "今日のディナー合計「8763円」だから…君の支払いは「4381.5円」ね！",
                "text_vi": "Bữa tối nay tổng cộng 「8.763 Yên」... vậy phần của em là 「4.381,5 Yên」 nhé!",
                "emotion": "normal"
            },
            {
                "speaker": "girlfriend",
                "text": "は？「0.5円」って何！？初デートで端数まで電卓叩くの…？",
                "text_vi": "Hả? 「0,5 Yên」 là cái gì cơ!? Buổi hẹn hò đầu tiên mà anh bấm máy tính đến từng nửa đồng xu à...?",
                "emotion": "angry"
            },
            {
                "speaker": "boyfriend",
                "text": "男女平等でしょ？あ、君「水2杯」飲んだから水道代＋10円ね！PayPayで送金して！",
                "text_vi": "Nam nữ bình đẳng mà? À em uống tận 「2 cốc nước lọc」 nên cộng thêm 10 Yên tiền nước nhé! Bắn tiền qua ví đi!",
                "emotion": "sweat"
            },
            {
                "speaker": "girlfriend",
                "text": "はい「1万円」。お釣りは全額チップにあげるから、今すぐ私の視界から消えて！",
                "text_vi": "Đây 「10.000 Yên」. Tiền thừa cho anh làm tiền tip luôn đấy, biến khỏi tầm mắt tôi ngay lập tức!",
                "emotion": "angry"
            },
            {
                "speaker": "boyfriend",
                "text": "えっ！？ラッキー！実質「5618円」の儲けだぁぁ！！",
                "text_vi": "Hả!? Trúng mánh rồi! Thế là mình tự dưng lãi đậm 「5.618 Yên」 luôn ta ơi!!",
                "emotion": "blush"
            },
            {
                "speaker": "girlfriend",
                "text": "一生ひとりで計算機と付き合ってろーー！！",
                "text_vi": "Cả đời này anh đi mà cưới cái máy tính bỏ túi làm vợ đi nhéーー!!",
                "emotion": "shocked"
            }
        ]
    },

    # 9. Đấu Trí Trinh Thám (Detective)
    {
        "id": "detective_alibi",
        "matchup": "detective",
        "title_main": "サクッと笑える",
        "title_sub": "【推理】SNSの映え写真でアリバイ崩壊した男",
        "topic": "完全犯罪・SNS特定",
        "topic_vi": "Bóc trần ảnh sống ảo ngoại phạm trên Instagram",
        "moral_lesson": "完璧な嘘など存在しない。承認欲求の投稿が身を滅ぼす。",
        "moral_lesson_vi": "Không có lời nói dối nào hoàn hảo. Bệnh sống ảo câu like sớm muộn cũng tự vạch trần chính mình.",
        "dialogue": [
            {
                "speaker": "detective",
                "text": "犯人よ！犯行時刻「昨夜22時」、お前は被害者の部屋に侵入したな？",
                "text_vi": "Kẻ thủ phạm kia! Lúc gây án 「22 giờ đêm qua」, ngươi đã đột nhập vào phòng nạn nhân đúng không?",
                "emotion": "normal"
            },
            {
                "speaker": "culprit",
                "text": "フッ、名探偵とやら。俺はその時間「ハワイのビーチ」にいたぜ！インスタを見ろ！",
                "text_vi": "Hừ, thám tử lừng danh gì chứ. Giờ đó ta đang ở 「bãi biển Hawaii」 nghỉ dưỡng nhé! Xem ảnh Instagram đi!",
                "emotion": "normal"
            },
            {
                "speaker": "detective",
                "text": "その写真のサングラスの反射…「自宅のコタツとテレビ画面」がクッキリ映っとるぞ！",
                "text_vi": "Cái kính râm trong ảnh đó... phản chiếu rõ mồn một cảnh ngươi 「ngồi sưởi bàn kotatsu xem TV ở nhà」 kìa!",
                "emotion": "angry"
            },
            {
                "speaker": "culprit",
                "text": "しまっ…！4K高画質でアップロードしちまったあああ！！",
                "text_vi": "Chết dở...! Quên mất là mình lỡ tay tải ảnh lên chế độ 「độ phân giải 4K」 rồi trời ơiii!!",
                "emotion": "shocked"
            },
            {
                "speaker": "detective",
                "text": "ネットで拾ったハワイの壁紙の前でポーズ取るな！署まで同行願おうか！",
                "text_vi": "Đừng có tải hình nền Hawaii trên mạng về làm phông nền chụp hình nữa! Mời theo tôi về đồn!",
                "emotion": "normal"
            },
            {
                "speaker": "culprit",
                "text": "いいね！欲しさに人生終わったぁぁぁーー！！",
                "text_vi": "Chỉ vì thèm mấy cái like ảo mà cuộc đời ta tan nát thế này saoーー!!",
                "emotion": "shocked"
            }
        ]
    },

    # 10. Chung Cư & Hàng Xóm (Apartment)
    {
        "id": "apartment_karaoke",
        "matchup": "apartment",
        "title_main": "サクッと笑える",
        "title_sub": "【騒音】深夜2時に爆音カラオケを熱唱する住人",
        "topic": "近隣トラブル・深夜騒音",
        "topic_vi": "Hát karaoke lúc 2h sáng và cái kết đối mặt ban quản lý",
        "moral_lesson": "自分の部屋でも自由には限度がある。周囲への気配りを忘れた者に住処なし。",
        "moral_lesson_vi": "Dù ở trong phòng mình thì tự do cũng có giới hạn. Kẻ không biết tôn trọng sự yên tĩnh chung sẽ không xứng đáng ở lại.",
        "dialogue": [
            {
                "speaker": "manager",
                "text": "402号室の住人！「深夜2時半」にマイク持って熱唱するのはやめなさい！",
                "text_vi": "Cư dân phòng 402! 「2 giờ rưỡi đêm」 rồi mà còn cầm mic gào thét thì dừng ngay lại!",
                "emotion": "angry"
            },
            {
                "speaker": "troublemaker",
                "text": "すいません管理人さん！今「サビの超盛り上がり」なんですよ！止められません！",
                "text_vi": "Thông cảm giùm đi quản lý ơi! Đang tới đoạn 「điệp khúc cao trào cực đỉnh」 của bài hát mà! Không dừng được!",
                "emotion": "sweat"
            },
            {
                "speaker": "manager",
                "text": "お前のヘタクソな歌声で「マンション全住民120人」が不眠症になっとるんだ！",
                "text_vi": "Giọng hát thảm họa của cậu đang làm 「toàn bộ 120 cư dân chung cư」 mất ngủ trầm cảm kìa!",
                "emotion": "angry"
            },
            {
                "speaker": "troublemaker",
                "text": "えっ！？みんな僕の生ライブをベッドで聴いてくれてるんですか…！？感無量です！",
                "text_vi": "Hả!? Mọi người nằm trên giường lắng nghe live concert của em thật sao...!? Xúc động rớt nước mắt!",
                "emotion": "blush"
            },
            {
                "speaker": "manager",
                "text": "誰がライブと言った！今すぐ電源を抜いて、今月末で「強制退去」です！！",
                "text_vi": "Ai nói là live concert hả! Rút phích cắm điện ngay, và cuối tháng này 「bị đuổi khỏi nhà」 nhé!!",
                "emotion": "angry"
            },
            {
                "speaker": "troublemaker",
                "text": "アンコールはお断りってことですかーー！？",
                "text_vi": "Ý ban quản lý là không cho em hát bài encore tặng kèm sao trờiーー!?",
                "emotion": "shocked"
            }
        ]
    }
]

def get_presets():
    return PRESET_SCRIPTS

def generate_script_from_prompt(topic, matchup_id="courtroom", api_key=None):
    """
    Generate satirical parable drama script with Vietnamese translations.
    Uses Gemini with an API key, or a fixed matchup template when no key exists.
    """
    # 1. Exact preset matching check
    for p in PRESET_SCRIPTS:
        if topic.lower() in p["topic"].lower() or topic.lower() in p.get("topic_vi", "").lower() or topic.lower() in p["title_sub"].lower():
            return {**p, "generation_mode": "preset"}

    # 2. Check API Key for Gemini
    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY")

    matchup_conf = get_matchup(matchup_id)
    preset = next(p for p in PRESET_SCRIPTS if p["matchup"] == matchup_conf["id"])
    title_prefix = preset["title_sub"].split("】", 1)[0] + "】"
    spk_a = matchup_conf.get("speaker_a", "judge")
    spk_b = matchup_conf.get("speaker_b", "prisoner")
    char_a = get_character(spk_a)
    char_b = get_character(spk_b)

    # 3. If API Key is present, run Gemini AI
    if api_key:
        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            
            prompt = f"""
            あなたは日本のTikTokで大人気の「いらすとや風刺ショートコント」専門の脚本家です。
            テーマ: 「{topic}」
            形式: 2人の対話（{char_a.get('name_jp', spk_a)} vs {char_b.get('name_jp', spk_b)}）
            Matchup ID: {matchup_id}
            Speaker A: {spk_a} ({char_a.get('name_jp', spk_a)})
            Speaker B: {spk_b} ({char_b.get('name_jp', spk_b)})
            
            【重要なルール】
            1. テンポの良さとユーモア（約30〜40秒、合計5〜6行のセリフ）。
            2. speaker は厳密に "{spk_a}" と "{spk_b}" を交互に使ってください。
            3. 強調したい重要キーワード（金額、年数、罪名、オチの言葉など）は必ず「」で囲んでください。（例: 「3日」、「10万円」、「オナラ」）。
            4. 最後は必ず子供たちへの教訓・大人が考えさせられる【風刺と道徳的メッセージ (moral_lesson)】を1文で締めてください。
            5. 各セリフ（text）と教訓（moral_lesson）には、制作者が内容を確認できるように必ず自然なベトナム語訳（text_vi, moral_lesson_vi）を添えてください。
            6. emotion は [normal, sweat, shocked, blush, angry] から選んでください。
            7. 入力テーマがベトナム語でも、title_sub・moral_lesson・各textは自然な日本語のみにしてください。ベトナム語は *_vi フィールドだけに入れてください。
            
            返却フォーマット (JSONのみ):
            {{
                "matchup": "{matchup_id}",
                "title_main": "サクッと笑える",
                "title_sub": "{title_prefix}○○の末路",
                "moral_lesson": "安易な欲望に流されず、正しい道を選んで生きよう。",
                "moral_lesson_vi": "Đừng để dục vọng nhất thời cuốn đi, hãy sống ngay thẳng và chân chính.",
                "dialogue": [
                    {{
                        "speaker": "{spk_a}",
                        "text": "おい！今回「○○」で問題を起こしたな？",
                        "text_vi": "Này! Lần này đã gây ra rắc rối vì 「vấn đề...」 đúng không?",
                        "emotion": "normal"
                    }},
                    {{
                        "speaker": "{spk_b}",
                        "text": "すいません！あれには「深いワケ」があったんです！",
                        "text_vi": "Xin lỗi mà! Chuyện đó là có 「lý do khó nói」 mà!",
                        "emotion": "sweat"
                    }}
                ]
            }}
            """
            try:
                response = client.models.generate_content(model="gemini-3.6-flash", contents=prompt)
            except Exception as first_error:
                if getattr(first_error, "code", None) not in (404, 503):
                    raise
                response = client.models.generate_content(model="gemini-3.5-flash-lite", contents=prompt)
            text = response.text.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            return {**json.loads(text), "generation_mode": "gemini"}
        except Exception as e:
            raise GeminiGenerationError(gemini_error_message(e)) from None

    # 4. Use the complete Japanese preset for the selected pair when AI is unavailable.
    return {**preset, "generation_mode": "offline"}
