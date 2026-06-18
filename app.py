from __future__ import annotations

import json
from datetime import datetime
from typing import Dict, List

import streamlit as st

from jpg_renderer import MAX_EXTRA_IMAGES, build_detail_jpg


st.set_page_config(
    page_title="네이버 상세페이지 JPG 자동 제작기",
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
    },
}

FONTS = ["맑은 고딕", "고딕 계열", "명조 계열", "바탕"]

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
    "jpg_quality": 90,
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


def current_config() -> Dict:
    return {key: st.session_state.get(key, value) for key, value in DEFAULTS.items()}


def show_uploaded_preview(files: List, columns: int = 4) -> None:
    if not files:
        return
    cols = st.columns(columns)
    for index, uploaded in enumerate(files):
        with cols[index % columns]:
            st.image(uploaded, use_container_width=True)
            st.caption(uploaded.name)


initialize_state()

st.title("네이버 상세페이지 JPG 자동 제작기")
st.caption("테마·문구·사진을 설정한 뒤 생성 버튼을 누르면 네이버 업로드용 긴 JPG가 바로 만들어집니다.")

with st.sidebar:
    st.header("1. 디자인 설정")
    st.selectbox("상세페이지 테마", list(THEMES.keys()), key="theme")
    st.info(THEMES[st.session_state.theme]["description"])
    st.selectbox("본문 폰트", FONTS, key="body_font")
    st.selectbox("제목 폰트", FONTS, key="heading_font")
    st.slider("완성 JPG 가로폭", 720, 1000, key="page_width", step=10)
    st.slider("기본 글자 크기", 14, 22, key="base_font_size")
    st.slider("구역 간격", 45, 100, key="section_spacing", step=5)
    st.slider("JPG 품질", 80, 95, key="jpg_quality")

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
    st.text_area("메인 제목", key="main_title", height=100, help="줄을 바꾸면 완성 JPG에도 줄바꿈됩니다.")
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
    st.subheader("기본 배치 사진")
    st.caption("기본 사진은 각 위치에 1장씩 들어갑니다. JPG, JPEG, PNG, WEBP를 사용할 수 있습니다.")
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
                uploaded = st.file_uploader(
                    "사진을 넣어주세요",
                    type=["jpg", "jpeg", "png", "webp"],
                    key=f"upload_{key}",
                    label_visibility="collapsed",
                )
                if uploaded is not None:
                    st.image(uploaded, use_container_width=True)

    st.divider()
    st.subheader("추가 사진 여러 장 업로드")
    st.caption(
        f"추가 사진은 세 구역을 합쳐 최대 {MAX_EXTRA_IMAGES}장까지 완성 JPG에 반영됩니다. "
        "선택한 순서대로 배치됩니다."
    )
    extra_model = st.file_uploader(
        "추가 모델 착용컷",
        type=["jpg", "jpeg", "png", "webp"],
        accept_multiple_files=True,
        key="extra_model_images",
        help="정면·측면·다른 포즈 등 모델 착용사진을 여러 장 선택하세요.",
    )
    show_uploaded_preview(extra_model)

    extra_detail = st.file_uploader(
        "추가 원단·봉제·단추 디테일컷",
        type=["jpg", "jpeg", "png", "webp"],
        accept_multiple_files=True,
        key="extra_detail_images",
        help="원단, 봉제선, 밑단, 단추, 라벨 등의 접사 사진을 여러 장 선택하세요.",
    )
    show_uploaded_preview(extra_detail)

    extra_gallery = st.file_uploader(
        "추가 코디·기타 상세 이미지",
        type=["jpg", "jpeg", "png", "webp"],
        accept_multiple_files=True,
        key="extra_gallery_images",
        help="코디컷, 색상컷, 무드컷, 추가 설명 이미지 등을 여러 장 선택하세요.",
    )
    show_uploaded_preview(extra_gallery)

st.divider()
st.subheader("상세페이지 JPG 생성")

if st.button("완성된 상세페이지 JPG 만들기", type="primary", use_container_width=True):
    config = current_config()
    core_images = {key: st.session_state.get(f"upload_{key}") for key, _, _ in IMAGE_SLOTS}
    extra_model_images = st.session_state.get("extra_model_images") or []
    extra_detail_images = st.session_state.get("extra_detail_images") or []
    extra_gallery_images = st.session_state.get("extra_gallery_images") or []
    extra_total = len(extra_model_images) + len(extra_detail_images) + len(extra_gallery_images)

    if core_images.get("hero") is None and core_images.get("front") is None:
        st.warning("대표 모델컷이나 정면 착용컷 중 최소 1장은 넣는 것이 좋습니다.")

    try:
        with st.spinner("긴 상세페이지 JPG를 제작하고 있습니다..."):
            jpg_bytes, out_w, out_h, used_extras = build_detail_jpg(
                config=config,
                theme=THEMES[config["theme"]],
                core_images=core_images,
                extra_model_images=extra_model_images,
                extra_detail_images=extra_detail_images,
                extra_gallery_images=extra_gallery_images,
                quality=config["jpg_quality"],
            )
        st.session_state["result_jpg"] = jpg_bytes
        st.session_state["result_size"] = (out_w, out_h)
        st.session_state["used_extras"] = used_extras
        st.session_state["generated_at"] = datetime.now().strftime("%Y%m%d_%H%M%S")
        if extra_total > MAX_EXTRA_IMAGES:
            st.warning(f"추가 사진은 최대 {MAX_EXTRA_IMAGES}장까지만 반영했습니다.")
        st.success("완성된 상세페이지 JPG가 제작되었습니다.")
    except Exception as exc:
        st.error(f"JPG 제작 중 오류가 발생했습니다: {exc}")

if "result_jpg" in st.session_state:
    width, height = st.session_state.get("result_size", (0, 0))
    st.subheader("완성 이미지 미리보기")
    st.caption(f"완성 크기: {width:,} × {height:,}px · 추가 사진 {st.session_state.get('used_extras', 0)}장 반영")
    st.image(st.session_state["result_jpg"], use_container_width=True)

    file_name = f"네이버_상세페이지_{st.session_state.get('generated_at', '완성')}.jpg"
    st.download_button(
        "완성된 JPG 다운로드",
        data=st.session_state["result_jpg"],
        file_name=file_name,
        mime="image/jpeg",
        type="primary",
        use_container_width=True,
    )
    st.info("다운로드한 JPG를 네이버 스마트스토어 상세설명 이미지로 바로 등록하면 됩니다.")
