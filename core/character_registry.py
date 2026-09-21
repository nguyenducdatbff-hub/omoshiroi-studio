# OMOSHIROI Character Registry & Matchup Configurations
# 10 Viral Satirical Duo Matchups for TikTok Shorts

CHARACTERS = {
    'judge': {
        'id': 'judge',
        'name_jp': '裁判官',
        'name_vi': 'Chủ Tọa / Thẩm Phán',
        'role': 'authority',
        'voice': 'ja-JP-KeitaNeural',
        'pitch': '-18Hz',
        'rate': '-4%',
        'height_scale': 1.0,
        'sub_stroke': (180, 120, 20),    # Imperial Gold / Dark Amber
        'sub_glow': (255, 230, 100, 180),
        'tag_color': 'amber'
    },
    'prisoner': {
        'id': 'prisoner',
        'name_jp': '被告人',
        'name_vi': 'Bị Cáo / Kẻ Phạm Tội',
        'role': 'suspect',
        'voice': 'ja-JP-KeitaNeural',
        'pitch': '+6Hz',
        'rate': '+8%',
        'height_scale': 0.92,
        'sub_stroke': (120, 30, 140),    # Dark Purple / Guilty
        'sub_glow': (200, 80, 220, 160),
        'tag_color': 'purple'
    },
    'police': {
        'id': 'police',
        'name_jp': '警察官',
        'name_vi': 'Cảnh Sát Đồn (Koban)',
        'role': 'authority',
        'voice': 'ja-JP-KeitaNeural',
        'pitch': '-8Hz',
        'rate': '+2%',
        'height_scale': 1.0,
        'sub_stroke': (20, 70, 170),     # Police Royal Blue
        'sub_glow': (100, 160, 255, 180),
        'tag_color': 'blue'
    },
    'citizen': {
        'id': 'citizen',
        'name_jp': '男性容疑者',
        'name_vi': 'Nam Nghi Phạm (Run sợ)',
        'role': 'suspect',
        'voice': 'ja-JP-KeitaNeural',
        'pitch': '+4Hz',
        'rate': '+4%',
        'height_scale': 0.88,
        'sub_stroke': (30, 130, 80),     # Citizen Green
        'sub_glow': (80, 210, 140, 160),
        'tag_color': 'emerald'
    },
    'citizen_female': {
        'id': 'citizen_female',
        'name_jp': '女性容疑者',
        'name_vi': 'Nữ Nghi Phạm (Toát mồ hôi)',
        'role': 'suspect',
        'voice': 'ja-JP-NanamiNeural',
        'pitch': '+2Hz',
        'rate': '+4%',
        'height_scale': 0.85,
        'sub_stroke': (160, 40, 110),    # Magenta / Rose
        'sub_glow': (230, 90, 170, 160),
        'tag_color': 'rose'
    },
    'doctor': {
        'id': 'doctor',
        'name_jp': '医師',
        'name_vi': 'Bác Sĩ (Áo Blouse Trắng)',
        'role': 'authority',
        'voice': 'ja-JP-KeitaNeural',
        'pitch': '-10Hz',
        'rate': '-2%',
        'height_scale': 1.0,
        'sub_stroke': (20, 120, 160),    # Medical Teal / Cyan
        'sub_glow': (80, 210, 240, 180),
        'tag_color': 'cyan'
    },
    'patient': {
        'id': 'patient',
        'name_jp': '患者',
        'name_vi': 'Bệnh Nhân (Hoang tưởng)',
        'role': 'suspect',
        'voice': 'ja-JP-KeitaNeural',
        'pitch': '+6Hz',
        'rate': '+8%',
        'height_scale': 0.88,
        'sub_stroke': (180, 50, 80),     # Emergency Red-Pink
        'sub_glow': (240, 100, 130, 160),
        'tag_color': 'rose'
    },
    'boss': {
        'id': 'boss',
        'name_jp': '鬼上司',
        'name_vi': 'Sếp Khó Tính (Trưởng Phòng)',
        'role': 'authority',
        'voice': 'ja-JP-KeitaNeural',
        'pitch': '-8Hz',
        'rate': '+0%',
        'height_scale': 1.0,
        'sub_stroke': (160, 80, 20),     # Corporate Dark Amber
        'sub_glow': (240, 160, 60, 180),
        'tag_color': 'amber'
    },
    'worker': {
        'id': 'worker',
        'name_jp': 'Z世代社員',
        'name_vi': 'Nhân Viên Gen Z (Lươn lẹo)',
        'role': 'suspect',
        'voice': 'ja-JP-NanamiNeural',
        'pitch': '+4Hz',
        'rate': '+6%',
        'height_scale': 0.90,
        'sub_stroke': (30, 140, 100),    # Fresh Green
        'sub_glow': (80, 220, 160, 160),
        'tag_color': 'emerald'
    },
    'teacher': {
        'id': 'teacher',
        'name_jp': '熱血教師',
        'name_vi': 'Thầy Giáo (Kỷ Luật)',
        'role': 'authority',
        'voice': 'ja-JP-KeitaNeural',
        'pitch': '-4Hz',
        'rate': '+2%',
        'height_scale': 1.0,
        'sub_stroke': (120, 50, 160),    # Academic Purple
        'sub_glow': (190, 110, 240, 180),
        'tag_color': 'purple'
    },
    'boy': {
        'id': 'boy',
        'name_jp': '男子生徒',
        'name_vi': 'Học Sinh Nam (Cá Biệt)',
        'role': 'suspect',
        'voice': 'ja-JP-KeitaNeural',
        'pitch': '+4Hz',
        'rate': '+6%',
        'height_scale': 0.90,
        'sub_stroke': (20, 60, 160),     # Vivid Navy Blue
        'sub_glow': (80, 130, 230, 160),
        'tag_color': 'sky'
    },
    'girl': {
        'id': 'girl',
        'name_jp': '女子生徒',
        'name_vi': 'Nữ Sinh (Nanami)',
        'role': 'youth',
        'voice': 'ja-JP-NanamiNeural',
        'pitch': '+2Hz',
        'rate': '+6%',
        'height_scale': 0.88,
        'sub_stroke': (210, 30, 90),     # Vivid Pink
        'sub_glow': (250, 120, 170, 160),
        'tag_color': 'pink'
    },
    'clerk': {
        'id': 'clerk',
        'name_jp': 'コンビニ店員',
        'name_vi': 'Nhân Viên Conbini (Tạp dề)',
        'role': 'authority',
        'voice': 'ja-JP-KeitaNeural',
        'pitch': '+2Hz',
        'rate': '+4%',
        'height_scale': 0.92,
        'sub_stroke': (30, 100, 180),    # Service Blue
        'sub_glow': (100, 180, 250, 180),
        'tag_color': 'sky'
    },
    'customer': {
        'id': 'customer',
        'name_jp': '迷惑クレーマー',
        'name_vi': 'Khách Quái Đản (Ăn vạ)',
        'role': 'suspect',
        'voice': 'ja-JP-NanamiNeural',
        'pitch': '+2Hz',
        'rate': '+6%',
        'height_scale': 0.88,
        'sub_stroke': (190, 40, 40),     # Warning Red
        'sub_glow': (240, 100, 100, 160),
        'tag_color': 'rose'
    },
    'interviewer': {
        'id': 'interviewer',
        'name_jp': '面接官',
        'name_vi': 'Nhà Tuyển Dụng (Gắt gao)',
        'role': 'authority',
        'voice': 'ja-JP-KeitaNeural',
        'pitch': '-8Hz',
        'rate': '-2%',
        'height_scale': 1.0,
        'sub_stroke': (40, 70, 160),     # Navy Authority
        'sub_glow': (100, 150, 240, 180),
        'tag_color': 'indigo'
    },
    'candidate': {
        'id': 'candidate',
        'name_jp': '就活生',
        'name_vi': 'Ứng Viên (Nổ CV)',
        'role': 'suspect',
        'voice': 'ja-JP-KeitaNeural',
        'pitch': '+6Hz',
        'rate': '+8%',
        'height_scale': 0.88,
        'sub_stroke': (190, 100, 20),    # Nervous Orange
        'sub_glow': (240, 170, 70, 160),
        'tag_color': 'amber'
    },
    'girlfriend': {
        'id': 'girlfriend',
        'name_jp': '彼女',
        'name_vi': 'Bạn Gái (Bắt Bài)',
        'role': 'authority',
        'voice': 'ja-JP-NanamiNeural',
        'pitch': '+2Hz',
        'rate': '+4%',
        'height_scale': 0.86,
        'sub_stroke': (210, 30, 90),     # Intense Rose
        'sub_glow': (250, 110, 160, 180),
        'tag_color': 'pink'
    },
    'boyfriend': {
        'id': 'boyfriend',
        'name_jp': '彼氏',
        'name_vi': 'Bạn Trai (Lươn lẹo)',
        'role': 'suspect',
        'voice': 'ja-JP-KeitaNeural',
        'pitch': '+4Hz',
        'rate': '+6%',
        'height_scale': 0.90,
        'sub_stroke': (40, 110, 180),    # Panicked Blue
        'sub_glow': (100, 170, 240, 160),
        'tag_color': 'blue'
    },
    'detective': {
        'id': 'detective',
        'name_jp': '名探偵',
        'name_vi': 'Thám Tử Lừng Danh',
        'role': 'authority',
        'voice': 'ja-JP-KeitaNeural',
        'pitch': '-2Hz',
        'rate': '+4%',
        'height_scale': 1.0,
        'sub_stroke': (25, 110, 160),    # Detective Teal
        'sub_glow': (70, 190, 230, 180),
        'tag_color': 'cyan'
    },
    'culprit': {
        'id': 'culprit',
        'name_jp': '影の犯人',
        'name_vi': 'Kẻ Bí Ẩn / Bóng Đen',
        'role': 'suspect',
        'voice': 'ja-JP-KeitaNeural',
        'pitch': '-14Hz',
        'rate': '+2%',
        'height_scale': 0.95,
        'sub_stroke': (40, 40, 50),      # Noir Shadow Gray
        'sub_glow': (100, 100, 110, 180),
        'tag_color': 'slate'
    },
    'manager': {
        'id': 'manager',
        'name_jp': '管理人',
        'name_vi': 'Ban Quản Lý Chung Cư',
        'role': 'authority',
        'voice': 'ja-JP-KeitaNeural',
        'pitch': '-6Hz',
        'rate': '+0%',
        'height_scale': 1.0,
        'sub_stroke': (60, 90, 130),     # Serious Slate
        'sub_glow': (130, 170, 210, 180),
        'tag_color': 'slate'
    },
    'troublemaker': {
        'id': 'troublemaker',
        'name_jp': '騒音住人',
        'name_vi': 'Kẻ Gây Ồn (Karaoke đêm)',
        'role': 'suspect',
        'voice': 'ja-JP-KeitaNeural',
        'pitch': '+6Hz',
        'rate': '+6%',
        'height_scale': 0.90,
        'sub_stroke': (180, 40, 40),     # Warning Red
        'sub_glow': (230, 100, 100, 160),
        'tag_color': 'red'
    }
}

DUO_MATCHUPS = [
    {
        'id': 'courtroom',
        'icon': '⚖️',
        'title_vi': 'Tòa Án Kỳ Án',
        'title': '⚖️ 裁判所・法廷 (Tòa Án Kỳ Án)',
        'desc_vi': 'Thẩm phán xét xử bị cáo, bóc trần tội lỗi & tuyên án răn đe',
        'desc': 'Chủ tọa xét xử tội phạm, drama kỳ án & tuyên án răn đe',
        'speaker_a': 'judge',
        'speaker_b': 'prisoner',
        'default_bg': 'courtroom',
        'intro_sfx': 'sfx_gavel.wav',
        'has_mascot': True,
        'has_stamp': True
    },
    {
        'id': 'koban',
        'icon': '👮‍♂️',
        'title_vi': 'Đồn Cảnh Sát (Nam/Nữ)',
        'title': '👮‍♂️ 交番・警察署 (Đồn Cảnh Sát)',
        'desc_vi': 'Cảnh sát thẩm vấn nghi phạm run sợ lo bị bắt giam',
        'desc': 'Cảnh sát thẩm vấn nam/nữ nghi phạm run sợ lo bị bắt',
        'speaker_a': 'police',
        'speaker_b': 'citizen_female',
        'default_bg': 'koban',
        'intro_sfx': 'sfx_gavel.wav',
        'has_mascot': True,
        'has_stamp': True
    },
    {
        'id': 'hospital',
        'icon': '🏥',
        'title_vi': 'Bệnh Viện & Bác Sĩ Google',
        'title': '🏥 病院・診察室 (Bệnh Viện & Phòng Khám)',
        'desc_vi': 'Bác sĩ bóc phốt bệnh nhân tra Google tự tưởng tượng bệnh nan y',
        'desc': 'Bác sĩ khám bệnh, đối phó bệnh nhân ảo tưởng tra mạng',
        'speaker_a': 'doctor',
        'speaker_b': 'patient',
        'default_bg': 'hospital',
        'intro_sfx': 'sfx_gavel.wav',
        'has_mascot': True,
        'has_stamp': True
    },
    {
        'id': 'office',
        'icon': '💼',
        'title_vi': 'Công Sở & Gen Z',
        'title': '💼 職場・オフィス (Sếp vs Nhân Viên Gen Z)',
        'desc_vi': 'Sếp khó tính đối đầu nhân viên Gen Z từ chối OT, lười biếng',
        'desc': 'Tranh luận hài hước chốn công sở Nhật Bản',
        'speaker_a': 'boss',
        'speaker_b': 'worker',
        'default_bg': 'office',
        'intro_sfx': 'sfx_gavel.wav',
        'has_mascot': True,
        'has_stamp': True
    },
    {
        'id': 'school',
        'icon': '🏫',
        'title_vi': 'Học Đường & Lớp Học',
        'title': '🏫 学園・教室 (Giáo Viên vs Học Sinh)',
        'desc_vi': 'Thầy giáo bóc mẽ học sinh quay cóp AI, trốn học, nghịch ngợm',
        'desc': 'Thầy giáo kỷ luật học sinh cá biệt trong lớp',
        'speaker_a': 'teacher',
        'speaker_b': 'boy',
        'default_bg': 'classroom',
        'intro_sfx': 'sfx_gavel.wav',
        'has_mascot': True,
        'has_stamp': True
    },
    {
        'id': 'conbini',
        'icon': '🏪',
        'title_vi': 'Cửa Hàng Tiện Lợi (Conbini)',
        'title': '🏪 コンビニ (Thu Ngân vs Khách Ăn Vạ)',
        'desc_vi': 'Nhân viên thu ngân đối đầu khách hàng quái đản đòi đổi trả vô lý',
        'desc': 'Drama thường nhật tại cửa hàng tiện lợi Nhật',
        'speaker_a': 'clerk',
        'speaker_b': 'customer',
        'default_bg': 'convenience_store',
        'intro_sfx': 'sfx_gavel.wav',
        'has_mascot': True,
        'has_stamp': True
    },
    {
        'id': 'interview',
        'icon': '📑',
        'title_vi': 'Phỏng Vấn Xin Việc',
        'title': '📑 採用面接 (Nhà Tuyển Dụng vs Ứng Viên Nổ CV)',
        'desc_vi': 'Nhà tuyển dụng bóc mẽ ứng viên chém gió CV đòi lương trên trời',
        'desc': 'Màn phỏng vấn hài hước bóc mẽ ứng viên nổ',
        'speaker_a': 'interviewer',
        'speaker_b': 'candidate',
        'default_bg': 'interview_room',
        'intro_sfx': 'sfx_gavel.wav',
        'has_mascot': True,
        'has_stamp': True
    },
    {
        'id': 'dating',
        'icon': '💔',
        'title_vi': 'Hẹn Hò Drama',
        'title': '💔 デート・修羅場 (Bạn Gái Bắt Bài Bạn Trai)',
        'desc_vi': 'Bạn gái ghen tuông bắt quả tang bạn trai lươn lẹo, chia tiền sòng phẳng',
        'desc': 'Màn đối chất dở khóc dở cười của cặp đôi hẹn hò',
        'speaker_a': 'girlfriend',
        'speaker_b': 'boyfriend',
        'default_bg': 'cafe',
        'intro_sfx': 'sfx_gavel.wav',
        'has_mascot': True,
        'has_stamp': True
    },
    {
        'id': 'detective',
        'icon': '🔍',
        'title_vi': 'Đấu Trí Trinh Thám',
        'title': '🔍 名探偵 vs 影の犯人 (Đấu Trí Trinh Thám)',
        'desc_vi': 'Thám tử bóc trần thủ đoạn tinh vi và bằng chứng ngoại phạm sống ảo',
        'desc': 'Thám tử bóc trần thủ đoạn tinh vi của kẻ bí ẩn',
        'speaker_a': 'detective',
        'speaker_b': 'culprit',
        'default_bg': 'courtroom',
        'intro_sfx': 'sfx_gavel.wav',
        'has_mascot': True,
        'has_stamp': True
    },
    {
        'id': 'apartment',
        'icon': '🏢',
        'title_vi': 'Chung Cư & Hàng Xóm',
        'title': '🏢 マンション (Ban Quản Lý vs Kẻ Gây Ồn)',
        'desc_vi': 'Ban quản lý đối chất kẻ hát karaoke lúc 2h sáng, xả rác bừa bãi',
        'desc': 'Tranh chấp tiếng ồn và ý thức cộng đồng chung cư',
        'speaker_a': 'manager',
        'speaker_b': 'troublemaker',
        'default_bg': 'apartment',
        'intro_sfx': 'sfx_gavel.wav',
        'has_mascot': True,
        'has_stamp': True
    }
]

def get_character(char_id):
    return CHARACTERS.get(char_id, CHARACTERS['boy'])

def get_matchup(matchup_id):
    for m in DUO_MATCHUPS:
        if m['id'] == matchup_id:
            return m
    return DUO_MATCHUPS[0]
