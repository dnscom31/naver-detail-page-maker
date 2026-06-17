THEMES = {
    "퓨어 화이트": dict(bg="#ffffff", section="#ffffff", soft="#f5f5f5", text="#222222", muted="#707070", point="#9b835f", line="#e5e5e5"),
    "클래식 아이보리": dict(bg="#f7f2e9", section="#fffdf8", soft="#eee5d8", text="#2e2923", muted="#746b60", point="#9b7644", line="#ddcfbd"),
    "모던 블랙": dict(bg="#eeeeee", section="#ffffff", soft="#151515", text="#202020", muted="#707070", point="#b79a62", line="#d8d8d8"),
    "로즈 베이지": dict(bg="#f7eeee", section="#fffafa", soft="#eadcdc", text="#352b2d", muted="#796b6e", point="#a6767e", line="#e2cfd2"),
}
FONTS = ["고딕 계열", "명조 계열"]
NAMED_IMAGES = [
    ("hero", "01. 대표 모델 착용컷"), ("front", "02. 정면 착용컷"),
    ("angle", "03. 사선 착용컷"), ("back", "04. 후면 착용컷"),
    ("fabric", "05. 원단 접사"), ("button", "06. 시그니처 단추 접사"),
    ("collar", "07. 카라 접사"), ("sleeve", "08. 소매 접사"),
    ("korea", "09. 국내제작 이미지"), ("styling", "10. 코디 착용컷"),
    ("size", "11. 사이즈 측정 이미지"),
]
DEFAULTS = {
    "theme": "클래식 아이보리", "body_font": "고딕 계열", "heading_font": "명조 계열",
    "page_width": 860, "base_font_size": 18, "section_spacing": 64, "jpg_quality": 90,
    "brand_line": "PREMIUM MATURE WOMENSWEAR",
    "main_title": "국내원단으로 완성한\n우아한 플라워 시스루 롱블라우스",
    "main_subtitle": "55세 이후의 여성을 위해, 편안함과 품격을 함께 담았습니다.",
    "badges": "국내원단|품질을 고려해 선택한 국내 소재\n100% 국내제작|국내 재단·봉제·마감\n체형 커버|복부와 힙을 자연스럽게 정돈",
    "problems": "몸에 달라붙지 않으면서도 단정한 옷을 찾는 분\n팔뚝과 복부, 힙 라인을 자연스럽게 가리고 싶은 분\n너무 젊거나 지나치게 올드한 디자인이 부담스러운 분\n모임과 외출에 두루 입을 수 있는 옷이 필요한 분\n국내원단과 국내제작의 안정적인 품질을 선호하는 분",
    "look_description": "세로로 이어지는 앞여밈과 여유 있는 롱기장이 몸의 선을 자연스럽게 정돈해 줍니다.",
    "points": "부담 없는 체형 커버|복부와 힙 라인을 자연스럽게 감싸는 여유 있는 실루엣입니다.\n은은한 시스루|과하지 않은 비침과 플라워 패턴이 우아한 분위기를 만듭니다.\n2WAY 활용|단추를 잠그면 블라우스로, 열면 가벼운 아우터로 연출할 수 있습니다.\n편안한 소매|팔뚝을 안정적으로 감싸면서 손목은 가볍게 드러냅니다.",
    "fabric_title": "국내원단의 섬세한 플라워 패턴",
    "fabric_text": "고급스러운 플라워 패턴과 은은한 반짝임이 어우러져 과하지 않으면서도 특별한 인상을 줍니다.",
    "button_title": "이 옷만의 시그니처 단추",
    "button_text": "깊이감 있는 그레이 블랙 컬러와 은은한 광택이 살아 있는 2홀 단추로 전면 디자인의 완성도를 높였습니다.",
    "korea_title": "국내원단 · 국내 재단 · 국내 봉제 · 국내 마감",
    "korea_text": "본 제품은 국내원단을 사용해 국내에서 재단, 봉제, 마감한 100% 국내제작 상품입니다.",
    "uses": "가족 모임|부담 없이 단정한 외출복\n동창회·친목 모임|은은하게 돋보이는 스타일\n결혼식·행사|격식을 갖춘 하객룩\n여행·공연 관람|가볍고 활용도 높은 코디",
    "specs": "제품명|플라워 시스루 롱블라우스\n색상|블랙\n사이즈|FREE\n소재|혼용률 입력\n제조국|대한민국\n제조자|판매자 협력업체\n세탁방법|드라이클리닝 권장\n이너 포함 여부|확인 후 입력",
    "size_row": "FREE|입력|입력|입력|입력|입력",
    "notices": "시스루 소재 특성상 이너웨어와 함께 착용하는 상품입니다.\n모니터 환경과 촬영 조명에 따라 실제 색상이 다르게 보일 수 있습니다.\n패턴 위치는 재단 과정에 따라 상품마다 조금씩 다를 수 있습니다.\n실측 사이즈는 측정 위치와 방법에 따라 1~3cm 오차가 발생할 수 있습니다.\n세탁 전 반드시 상품의 케어라벨을 확인해 주세요.",
    "footer_title": "나이에 맞춘 옷이 아니라, 품격에 맞춘 옷",
    "footer_text": "55세 이후의 여성이 더 편안하고 우아하게 입을 수 있는 국내제작 여성복을 제안합니다.",
}
FONT_FILES = {
    "고딕 계열": ["/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", "/usr/share/fonts/truetype/nanum/NanumGothic.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"],
    "고딕 계열_bold": ["/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc", "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
    "명조 계열": ["/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc", "/usr/share/fonts/truetype/nanum/NanumMyeongjo.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"],
    "명조 계열_bold": ["/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc", "/usr/share/fonts/truetype/nanum/NanumMyeongjoBold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"],
}
