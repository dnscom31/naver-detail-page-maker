
import base64
import html
import json
import mimetypes
from datetime import datetime
from io import BytesIO
from typing import Dict, List

import streamlit as st
import streamlit.components.v1 as components


st.set_page_config(
    page_title="네이버 상세페이지 자동 제작기",
    page_icon="🛍️",
    layout="wide",
)

THEMES = {
    "퓨어 화이트": {
        "description": "화이트 배경과 넓은 여백을 사용하는 가장 깔끔한 상품 중심 테마",
        "page_bg": "#ffffff",
        "section_bg": "#ffffff",
        "soft_bg": "#f7f7f7",
        "text": "#222222",
        "muted": "#6f6f6f",
        "point": "#9b835f",
        "line": "#e9e6e1",
        "card_bg": "#ffffff",
        "hero_bg": "#ffffff",
        "hero_text": "#222222",
        "heading_align": "center",
        "radius": "0px",
        "shadow": "none",
    },
    "클래식 아이보리": {
        "description": "아이보리와 골드 포인트로 국내제작·프리미엄 이미지를 강조하는 테마",
        "page_bg": "#f7f2e9",
        "section_bg": "#fffdf8",
        "soft_bg": "#eee5d8",
        "text": "#2e2923",
        "muted": "#746b60",
        "point": "#9b7644",
        "line": "#ddcfbd",
        "card_bg": "#fffdf8",
        "hero_bg": "#f1e8db",
        "hero_text": "#2e2923",
        "heading_align": "center",
        "radius": "2px",
        "shadow": "0 8px 28px rgba(87, 66, 38, .08)",
    },
    "모던 블랙": {
        "description": "블랙과 샴페인 골드를 사용해 시크하고 고급스러운 인상을 주는 테마",
        "page_bg": "#eeeeee",
        "section_bg": "#ffffff",
        "soft_bg": "#151515",
        "text": "#202020",
        "muted": "#707070",
        "point": "#b79a62",
        "line": "#dcdcdc",
        "card_bg": "#f8f8f8",
        "hero_bg": "#111111",
        "hero_text": "#ffffff",
        "heading_align": "left",
        "radius": "0px",
        "shadow": "0 12px 34px rgba(0, 0, 0, .10)",
    },
    "로즈 베이지": {
        "description": "부드러운 로즈·베이지 계열로 우아하고 여성스러운 분위기를 만드는 테마",
        "page_bg": "#f7eeee",
        "section_bg": "#fffafa",
        "soft_bg": "#eadcdc",
        "text": "#352b2d",
        "muted": "#796b6e",
        "point": "#a6767e",
        "line": "#e2cfd2",
        "card_bg": "#fffafa",
        "hero_bg": "#f2e3e4",
        "hero_text": "#352b2d",
        "heading_align": "center",
        "radius": "18px",
        "shadow": "0 10px 30px rgba(119, 76, 84, .10)",
    },
}

FONTS = {
    "맑은 고딕": '"Malgun Gothic","Apple SD Gothic Neo",sans-serif',
    "고딕 계열": '"Noto Sans KR","Pretendard","Malgun Gothic",sans-serif',
    "명조 계열": '"Noto Serif KR","Batang","Times New Roman",serif',
    "바탕": '"Batang","Noto Serif KR",serif',
}

IMAGE_SLOTS = [
    ("hero", "01. 대표 모델 착용컷", "첫 화면의 대표 이미지"),
    ("front", "02. 정면 착용컷", "상품 전체 실루엣이 잘 보이는 정면 사진"),
    ("angle", "03. 사선 착용컷", "45도 또는 자연스러운 포즈의 사진"),
    ("back", "04. 후면 착용컷", "뒤 기장과 패턴을 확인할 수 있는 사진"),
    ("fabric", "05. 원단 접사", "플라워 패턴과 반짝임이 보이는 사진"),
    ("button", "06. 시그니처 단추 접사", "단추의 색상·광택·2홀 구조가 보이는 사진"),
    ("collar", "07. 카라 접사", "카라와 앞여밈 마감 사진"),
    ("sleeve", "08. 소매 접사", "시스루와 소매 길이가 보이는 사진"),
    ("korea", "09. 국내제작 이미지", "제작 현장, 라벨 또는 신뢰를 주는 이미지"),
    ("styling", "10. 코디 착용컷", "모임·외출 상황을 보여주는 사진"),
    ("size", "11. 사이즈 측정 이미지", "측정 위치를 안내하는 사진"),
]

DEFAULTS = {
    "theme": "클래식 아이보리",
    "body_font": "고딕 계열",
    "heading_font": "명조 계열",
    "page_width": 860,
    "base_font_size": 17,
    "section_spacing": 72,
    "brand_line": "PREMIUM MATURE WOMENSWEAR",
    "main_title": "국내원단으로 완성한\n우아한 플라워 시스루 롱블라우스",
    "main_subtitle": "55세 이후의 여성을 위해, 편안함과 품격을 함께 담았습니다.",
    "badge1_title": "국내원단",
    "badge1_text": "품질을 고려해 선택한 국내 소재",
    "badge2_title": "100% 국내제작",
    "badge2_text": "국내 재단·봉제·마감",
    "badge3_title": "체형 커버",
    "badge3_text": "복부와 힙을 자연스럽게 정돈",
    "problems": "\n".join([
        "몸에 달라붙지 않으면서도 단정한 옷을 찾는 분",
        "팔뚝과 복부, 힙 라인을 자연스럽게 가리고 싶은 분",
        "너무 젊거나 지나치게 올드한 디자인이 부담스러운 분",
        "모임과 외출에 두루 입을 수 있는 옷이 필요한 분",
        "국내원단과 국내제작의 안정적인 품질을 선호하는 분",
    ]),
    "look_description": "세로로 이어지는 앞여밈과 여유 있는 롱기장이 몸의 선을 자연스럽게 정돈해 줍니다.",
    "point1_title": "부담 없는 체형 커버",
    "point1_text": "복부와 힙 라인을 자연스럽게 감싸는 여유 있는 실루엣입니다.",
    "point2_title": "은은한 시스루",
    "point2_text": "과하지 않은 비침과 플라워 패턴이 우아한 분위기를 만듭니다.",
    "point3_title": "2WAY 활용",
    "point3_text": "단추를 잠그면 블라우스로, 열면 가벼운 아우터로 연출할 수 있습니다.",
    "point4_title": "편안한 소매",
    "point4_text": "팔뚝을 안정적으로 감싸면서 손목은 가볍게 드러냅니다.",
    "fabric_title": "국내원단의 섬세한 플라워 패턴",
    "fabric_text": "고급스러운 플라워 패턴과 은은한 반짝임이 어우러져 과하지 않으면서도 특별한 인상을 줍니다.",
    "button_title": "이 옷만의 시그니처 단추",
    "button_text": "깊이감 있는 그레이 블랙 컬러와 은은한 광택이 살아 있는 2홀 단추로, 전면 디자인의 완성도를 높였습니다.",
    "korea_title": "국내원단 · 국내 재단 · 국내 봉제 · 국내 마감",
    "korea_text": "본 제품은 국내원단을 사용해 국내에서 재단, 봉제, 마감한 100% 국내제작 상품입니다.",
    "uses": "\n".join([
        "가족 모임|부담 없이 단정한 외출복",
        "동창회·친목 모임|은은하게 돋보이는 스타일",
        "결혼식·행사|격식을 갖춘 하객룩",
        "여행·공연 관람|가볍고 활용도 높은 코디",
    ]),
    "specs": "\n".join([
        "제품명|플라워 시스루 롱블라우스",
        "색상|블랙",
        "사이즈|FREE",
        "소재|혼용률 입력",
        "제조국|대한민국",
        "제조자|판매자 협력업체",
        "세탁방법|드라이클리닝 권장",
        "이너 포함 여부|확인 후 입력",
    ]),
    "size_name": "FREE",
    "size_shoulder": "입력",
    "size_chest": "입력",
    "size_sleeve": "입력",
    "size_armhole": "입력",
    "size_length": "입력",
    "notices": "\n".join([
        "시스루 소재 특성상 이너웨어와 함께 착용하는 상품입니다.",
        "모니터 환경과 촬영 조명에 따라 실제 색상이 다르게 보일 수 있습니다.",
        "패턴 위치는 재단 과정에 따라 상품마다 조금씩 다를 수 있습니다.",
        "실측 사이즈는 측정 위치와 방법에 따라 1~3cm 오차가 발생할 수 있습니다.",
        "세탁 전 반드시 상품의 케어라벨을 확인해 주세요.",
    ]),
    "footer_title": "나이에 맞춘 옷이 아니라, 품격에 맞춘 옷",
    "footer_text": "55세 이후의 여성이 더 편안하고 우아하게 입을 수 있는 국내제작 여성복을 제안합니다.",
}


def initialize_state() -> None:
    for key, value in DEFAULTS.items():
        st.session_state.setdefault(key, value)


def clean_lines(text: str) -> List[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def parse_pairs(text: str) -> List[List[str]]:
    items = []
    for line in clean_lines(text):
        if "|" in line:
            left, right = line.split("|", 1)
        else:
            left, right = line, ""
        items.append([left.strip(), right.strip()])
    return items


def safe_text(value: str) -> str:
    return html.escape(str(value)).replace("\n", "<br>")


def image_data_uri(uploaded_file) -> str:
    if uploaded_file is None:
        return ""
    data = uploaded_file.getvalue()
    mime = uploaded_file.type or mimetypes.guess_type(uploaded_file.name)[0] or "image/jpeg"
    encoded = base64.b64encode(data).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def image_html(images: Dict[str, str], key: str, label: str, css_class: str = "") -> str:
    src = images.get(key, "")
    if src:
        return f'<img class="product-image {css_class}" src="{src}" alt="{html.escape(label)}">'
    return (
        f'<div class="image-placeholder {css_class}">'
        f'<strong>{html.escape(label)}</strong><span>사진이 업로드되지 않았습니다.</span></div>'
    )


def current_config() -> Dict:
    keys = [key for key in DEFAULTS.keys()]
    return {key: st.session_state.get(key, DEFAULTS[key]) for key in keys}


def render_html(config: Dict, images: Dict[str, str]) -> str:
    theme = THEMES[config["theme"]]
    body_font = FONTS[config["body_font"]]
    heading_font = FONTS[config["heading_font"]]
    problems = clean_lines(config["problems"])
    uses = parse_pairs(config["uses"])
    specs = parse_pairs(config["specs"])
    notices = clean_lines(config["notices"])

    badges = [
        (config["badge1_title"], config["badge1_text"]),
        (config["badge2_title"], config["badge2_text"]),
        (config["badge3_title"], config["badge3_text"]),
    ]
    points = [
        (config["point1_title"], config["point1_text"]),
        (config["point2_title"], config["point2_text"]),
        (config["point3_title"], config["point3_text"]),
        (config["point4_title"], config["point4_text"]),
    ]

    badge_html = "".join(
        f'<div class="badge"><strong>{safe_text(title)}</strong><span>{safe_text(text)}</span></div>'
        for title, text in badges
    )
    problem_html = "".join(f"<li>{safe_text(item)}</li>" for item in problems)
    point_html = "".join(
        f'<article class="point-card"><div class="point-no">POINT {index:02d}</div>'
        f'<h3>{safe_text(title)}</h3><p>{safe_text(text)}</p></article>'
        for index, (title, text) in enumerate(points, 1)
    )
    use_html = "".join(
        f'<div class="use-card"><strong>{safe_text(title)}</strong><span>{safe_text(text)}</span></div>'
        for title, text in uses
    )
    spec_html = "".join(
        f"<tr><th>{safe_text(label)}</th><td>{safe_text(value)}</td></tr>"
        for label, value in specs
    )
    notice_html = "".join(f"<li>{safe_text(item)}</li>" for item in notices)

    modern_dark = config["theme"] == "모던 블랙"
    soft_text = "#f2f2f2" if modern_dark else theme["text"]
    soft_muted = "#c7c7c7" if modern_dark else theme["muted"]

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{safe_text(config["main_title"]).replace("<br>", " ")}</title>
<style>
:root {{
  --page-bg:{theme["page_bg"]};
  --section-bg:{theme["section_bg"]};
  --soft-bg:{theme["soft_bg"]};
  --text:{theme["text"]};
  --muted:{theme["muted"]};
  --point:{theme["point"]};
  --line:{theme["line"]};
  --card-bg:{theme["card_bg"]};
  --hero-bg:{theme["hero_bg"]};
  --hero-text:{theme["hero_text"]};
  --max-width:{int(config["page_width"])}px;
  --base-size:{int(config["base_font_size"])}px;
  --space:{int(config["section_spacing"])}px;
  --radius:{theme["radius"]};
  --shadow:{theme["shadow"]};
}}
*{{box-sizing:border-box}}
html,body{{margin:0;padding:0;background:var(--page-bg);color:var(--text)}}
body{{font-family:{body_font};font-size:var(--base-size);line-height:1.72;word-break:keep-all}}
.detail-page{{max-width:var(--max-width);margin:0 auto;background:var(--section-bg);overflow:hidden;box-shadow:var(--shadow)}}
img{{display:block;width:100%;height:auto}}
.hero-copy{{background:var(--hero-bg);color:var(--hero-text);padding:64px 34px 52px;text-align:center}}
.eyebrow,.section-label,.point-no{{color:var(--point);font-weight:800;letter-spacing:.13em;font-size:.82em}}
h1,h2,.footer-title{{font-family:{heading_font};font-weight:600}}
h1{{font-size:2.5em;line-height:1.3;margin:14px 0}}
h2{{font-size:2em;line-height:1.38;margin:10px 0}}
h3{{font-size:1.22em;line-height:1.45}}
.hero-subtitle,.section-description{{color:var(--muted);max-width:670px;margin:16px auto 0}}
.hero-copy .hero-subtitle{{color:{"#e2e2e2" if modern_dark else theme["muted"]}}}
.product-image{{object-fit:cover}}
.image-placeholder{{min-height:340px;background:#ededed;color:#8a8a8a;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:30px}}
.image-placeholder span{{font-size:.85em;margin-top:8px}}
.badges{{display:grid;grid-template-columns:repeat(3,1fr);gap:1px;background:var(--line);border-block:1px solid var(--line)}}
.badge{{background:var(--section-bg);padding:26px 12px;text-align:center}}
.badge strong,.badge span{{display:block}} .badge strong{{font-size:1.05em}} .badge span{{color:var(--muted);font-size:.82em;margin-top:3px}}
section{{padding:var(--space) 34px;background:var(--section-bg)}}
section.soft{{background:var(--soft-bg);color:{soft_text}}}
section.soft .section-description,section.soft p,section.soft .problem-list{{color:{soft_muted}}}
.section-head{{text-align:{theme["heading_align"]};margin-bottom:38px}}
.section-head.center{{text-align:center}}
.problem-list{{max-width:660px;margin:0 auto;padding:0;list-style:none;border-top:1px solid var(--line)}}
.problem-list li{{position:relative;padding:16px 8px 16px 38px;border-bottom:1px solid var(--line)}}
.problem-list li::before{{content:"✓";position:absolute;left:8px;color:var(--point);font-weight:900}}
.image-stack{{display:grid;gap:20px}}
.two-column{{display:grid;grid-template-columns:1fr 1fr;gap:18px}}
.points{{display:grid;grid-template-columns:1fr 1fr;gap:18px}}
.point-card{{background:var(--card-bg);color:var(--text);border:1px solid var(--line);padding:28px 24px;border-radius:var(--radius);box-shadow:var(--shadow)}}
.point-card h3{{margin:7px 0}} .point-card p{{margin:0;color:var(--muted)}}
.detail-block{{margin-bottom:44px}} .detail-block:last-child{{margin-bottom:0}}
.detail-copy{{padding:20px 5px 0}} .detail-copy h3{{margin:0 0 7px}} .detail-copy p{{margin:0;color:var(--muted)}}
.korea-box{{background:var(--card-bg);color:var(--text);border:1px solid var(--point);padding:34px 26px;text-align:center;border-radius:var(--radius)}}
.korea-box strong{{display:block;font-size:1.35em;margin-bottom:10px}}
.uses{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}
.use-card{{background:var(--card-bg);border:1px solid var(--line);padding:24px 20px;text-align:center;border-radius:var(--radius)}}
.use-card strong,.use-card span{{display:block}} .use-card span{{color:var(--muted);font-size:.84em;margin-top:5px}}
table{{width:100%;border-collapse:collapse}} th,td{{border:1px solid var(--line);padding:14px 12px}} th{{background:rgba(128,128,128,.07)}}
.spec-table th{{width:34%;text-align:left}} .size-wrap{{overflow-x:auto}} .size-table{{min-width:650px;text-align:center}}
.notice{{background:var(--card-bg);color:var(--text);padding:26px;border:1px solid var(--line);border-radius:var(--radius)}}
.notice li{{margin:6px 0}}
.footer{{padding:68px 34px 90px;text-align:center;background:var(--section-bg)}}
.footer-title{{font-size:1.7em}} .footer p{{color:var(--muted)}}
@media(max-width:640px){{
  body{{font-size:calc(var(--base-size) - 1px)}}
  h1{{font-size:1.95em}} h2{{font-size:1.65em}}
  .hero-copy,section,.footer{{padding-left:22px;padding-right:22px}}
  .badges,.two-column,.points,.uses{{grid-template-columns:1fr}}
}}
</style>
</head>
<body>
<main class="detail-page">
  <header>
    <div class="hero-copy">
      <div class="eyebrow">{safe_text(config["brand_line"])}</div>
      <h1>{safe_text(config["main_title"])}</h1>
      <p class="hero-subtitle">{safe_text(config["main_subtitle"])}</p>
    </div>
    {image_html(images, "hero", "대표 모델 착용컷")}
  </header>

  <div class="badges">{badge_html}</div>

  <section class="soft">
    <div class="section-head center">
      <div class="section-label">FOR YOU</div>
      <h2>이런 옷을 찾고 계셨나요?</h2>
    </div>
    <ul class="problem-list">{problem_html}</ul>
  </section>

  <section>
    <div class="section-head">
      <div class="section-label">SILHOUETTE</div>
      <h2>우아하게 정돈되는 실루엣</h2>
      <p class="section-description">{safe_text(config["look_description"])}</p>
    </div>
    <div class="image-stack">
      {image_html(images, "front", "정면 착용컷")}
      <div class="two-column">
        {image_html(images, "angle", "사선 착용컷")}
        {image_html(images, "back", "후면 착용컷")}
      </div>
    </div>
  </section>

  <section class="soft">
    <div class="section-head center">
      <div class="section-label">KEY POINT</div>
      <h2>입을수록 만족스러운 이유</h2>
    </div>
    <div class="points">{point_html}</div>
  </section>

  <section>
    <div class="section-head">
      <div class="section-label">DETAIL</div>
      <h2>눈으로 확인하는 섬세한 디테일</h2>
    </div>
    <div class="detail-block">
      {image_html(images, "fabric", "원단 접사")}
      <div class="detail-copy"><h3>{safe_text(config["fabric_title"])}</h3><p>{safe_text(config["fabric_text"])}</p></div>
    </div>
    <div class="detail-block">
      {image_html(images, "button", "시그니처 단추 접사")}
      <div class="detail-copy"><h3>{safe_text(config["button_title"])}</h3><p>{safe_text(config["button_text"])}</p></div>
    </div>
    <div class="two-column">
      {image_html(images, "collar", "카라 접사")}
      {image_html(images, "sleeve", "소매 접사")}
    </div>
  </section>

  <section class="soft">
    <div class="section-head center">
      <div class="section-label">MADE IN KOREA</div>
      <h2>원단부터 완성까지, 국내에서</h2>
    </div>
    <div class="korea-box"><strong>{safe_text(config["korea_title"])}</strong><p>{safe_text(config["korea_text"])}</p></div>
    <div style="margin-top:28px">{image_html(images, "korea", "국내제작 이미지")}</div>
  </section>

  <section>
    <div class="section-head">
      <div class="section-label">STYLING</div>
      <h2>격식 있는 순간부터 편안한 외출까지</h2>
    </div>
    <div class="uses">{use_html}</div>
    <div style="margin-top:28px">{image_html(images, "styling", "코디 착용컷")}</div>
  </section>

  <section class="soft">
    <div class="section-head center">
      <div class="section-label">PRODUCT INFO</div>
      <h2>상품 정보</h2>
    </div>
    <table class="spec-table">{spec_html}</table>
  </section>

  <section>
    <div class="section-head">
      <div class="section-label">SIZE GUIDE</div>
      <h2>실측 사이즈</h2>
      <p class="section-description">측정 위치와 방법에 따라 1~3cm 정도 오차가 발생할 수 있습니다.</p>
    </div>
    <div class="size-wrap">
      <table class="size-table">
        <thead><tr><th>사이즈</th><th>어깨</th><th>가슴단면</th><th>소매길이</th><th>암홀</th><th>총장</th></tr></thead>
        <tbody><tr>
          <td>{safe_text(config["size_name"])}</td>
          <td>{safe_text(config["size_shoulder"])}</td>
          <td>{safe_text(config["size_chest"])}</td>
          <td>{safe_text(config["size_sleeve"])}</td>
          <td>{safe_text(config["size_armhole"])}</td>
          <td>{safe_text(config["size_length"])}</td>
        </tr></tbody>
      </table>
    </div>
    <div style="margin-top:28px">{image_html(images, "size", "사이즈 측정 이미지")}</div>
  </section>

  <section class="soft">
    <div class="section-head center">
      <div class="section-label">NOTICE</div>
      <h2>구매 전 확인해 주세요</h2>
    </div>
    <div class="notice"><ul>{notice_html}</ul></div>
  </section>

  <footer class="footer">
    <div class="footer-title">{safe_text(config["footer_title"])}</div>
    <p>{safe_text(config["footer_text"])}</p>
  </footer>
</main>
</body>
</html>"""


initialize_state()

st.title("네이버 상세페이지 자동 제작기")
st.caption("테마를 고르고 문구와 사진을 넣은 뒤, 하단의 생성 버튼을 누르면 단일 HTML 상세페이지가 만들어집니다.")

with st.sidebar:
    st.header("1. 디자인 설정")
    st.selectbox("상세페이지 테마", list(THEMES.keys()), key="theme")
    st.info(THEMES[st.session_state.theme]["description"])
    st.selectbox("본문 폰트", list(FONTS.keys()), key="body_font")
    st.selectbox("제목 폰트", list(FONTS.keys()), key="heading_font")
    st.slider("페이지 가로폭", 720, 1000, key="page_width", step=10)
    st.slider("기본 글자 크기", 14, 22, key="base_font_size")
    st.slider("구역 간격", 45, 100, key="section_spacing", step=5)

    st.divider()
    st.header("설정 저장·불러오기")
    config_upload = st.file_uploader("이전에 저장한 설정 JSON 불러오기", type=["json"], key="config_upload")
    if st.button("설정 불러오기", use_container_width=True):
        if config_upload is None:
            st.warning("JSON 파일을 먼저 선택해 주세요.")
        else:
            try:
                loaded = json.loads(config_upload.getvalue().decode("utf-8"))
                for key, default in DEFAULTS.items():
                    if key in loaded:
                        st.session_state[key] = loaded[key]
                st.success("설정을 불러왔습니다.")
                st.rerun()
            except Exception as exc:
                st.error(f"설정 파일을 읽지 못했습니다: {exc}")

    config_bytes = json.dumps(current_config(), ensure_ascii=False, indent=2).encode("utf-8")
    st.download_button(
        "현재 설정 JSON 저장",
        data=config_bytes,
        file_name="상세페이지_설정.json",
        mime="application/json",
        use_container_width=True,
    )

tab1, tab2, tab3, tab4 = st.tabs(["기본 문구", "세일 포인트", "상품 정보", "사진 업로드"])

with tab1:
    st.subheader("첫 화면")
    st.text_input("브랜드 문구", key="brand_line")
    st.text_area("메인 제목", key="main_title", height=100, help="줄을 바꾸면 상세페이지에서도 줄바꿈됩니다.")
    st.text_area("메인 설명", key="main_subtitle", height=90)

    st.subheader("상단 핵심 배지 3개")
    cols = st.columns(3)
    for index, col in enumerate(cols, 1):
        with col:
            st.text_input(f"배지 {index} 제목", key=f"badge{index}_title")
            st.text_area(f"배지 {index} 설명", key=f"badge{index}_text", height=80)

    st.subheader("고객 고민")
    st.text_area("한 줄에 한 항목씩 입력", key="problems", height=180)

    st.subheader("마지막 브랜드 문구")
    st.text_input("하단 제목", key="footer_title")
    st.text_area("하단 설명", key="footer_text", height=90)

with tab2:
    st.subheader("실루엣 설명")
    st.text_area("착용핏·체형 커버 설명", key="look_description", height=90)

    st.subheader("핵심 세일 포인트 4개")
    for row in range(2):
        cols = st.columns(2)
        for col_index, col in enumerate(cols):
            index = row * 2 + col_index + 1
            with col:
                st.text_input(f"포인트 {index} 제목", key=f"point{index}_title")
                st.text_area(f"포인트 {index} 설명", key=f"point{index}_text", height=95)

    st.subheader("디테일 설명")
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("원단 제목", key="fabric_title")
        st.text_area("원단 설명", key="fabric_text", height=120)
    with col2:
        st.text_input("단추 제목", key="button_title")
        st.text_area("단추 설명", key="button_text", height=120)

    st.subheader("국내제작 설명")
    st.text_input("국내제작 제목", key="korea_title")
    st.text_area("국내제작 설명", key="korea_text", height=100)

    st.subheader("추천 착용 상황")
    st.text_area(
        "한 줄에 `제목|설명` 형식으로 입력",
        key="uses",
        height=150,
        help="예: 가족 모임|부담 없이 단정한 외출복",
    )

with tab3:
    st.subheader("상품 정보")
    st.text_area(
        "한 줄에 `항목|내용` 형식으로 입력",
        key="specs",
        height=250,
        help="예: 제조국|대한민국",
    )

    st.subheader("실측 사이즈")
    size_cols = st.columns(6)
    labels = [
        ("사이즈", "size_name"),
        ("어깨", "size_shoulder"),
        ("가슴단면", "size_chest"),
        ("소매길이", "size_sleeve"),
        ("암홀", "size_armhole"),
        ("총장", "size_length"),
    ]
    for col, (label, key) in zip(size_cols, labels):
        with col:
            st.text_input(label, key=key)

    st.subheader("구매 전 안내")
    st.text_area("한 줄에 한 항목씩 입력", key="notices", height=200)

with tab4:
    st.subheader("사진을 넣어주세요")
    st.caption("JPG, JPEG, PNG, WEBP 파일을 업로드할 수 있습니다. 업로드하지 않은 자리는 안내 박스로 표시됩니다.")
    uploaded_files = {}
    for row in range(0, len(IMAGE_SLOTS), 2):
        cols = st.columns(2)
        for offset, col in enumerate(cols):
            index = row + offset
            if index >= len(IMAGE_SLOTS):
                break
            key, label, help_text = IMAGE_SLOTS[index]
            with col:
                st.markdown(f"**{label}**")
                st.caption(help_text)
                uploaded_files[key] = st.file_uploader(
                    "사진을 넣어주세요",
                    type=["jpg", "jpeg", "png", "webp"],
                    key=f"upload_{key}",
                    label_visibility="collapsed",
                )
                if uploaded_files[key] is not None:
                    st.image(uploaded_files[key], use_container_width=True)

st.divider()
st.subheader("상세페이지 생성")

if st.button("상세페이지 생성하기", type="primary", use_container_width=True):
    config = current_config()
    images = {}
    for key, _, _ in IMAGE_SLOTS:
        uploaded = st.session_state.get(f"upload_{key}")
        images[key] = image_data_uri(uploaded) if uploaded else ""

    result_html = render_html(config, images)
    st.session_state["result_html"] = result_html
    st.session_state["generated_at"] = datetime.now().strftime("%Y%m%d_%H%M%S")
    st.success("상세페이지가 생성되었습니다. 아래에서 미리보기와 다운로드를 확인하세요.")

if "result_html" in st.session_state:
    st.subheader("미리보기")
    components.html(st.session_state["result_html"], height=1100, scrolling=True)

    html_bytes = st.session_state["result_html"].encode("utf-8")
    file_name = f"네이버_상세페이지_{st.session_state.get('generated_at','완성')}.html"
    st.download_button(
        "완성된 HTML 다운로드",
        data=html_bytes,
        file_name=file_name,
        mime="text/html",
        type="primary",
        use_container_width=True,
    )

    st.info(
        "다운로드한 HTML은 사진이 파일 내부에 포함된 단일 파일입니다. "
        "Chrome에서 열어 전체 페이지 캡처 후 긴 이미지로 저장하면 스마트스토어 상세설명에 등록하기 쉽습니다."
    )
