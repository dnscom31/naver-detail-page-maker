from __future__ import annotations

import json
from datetime import datetime
from io import BytesIO
from pathlib import Path
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
    "세이지 그린": {
        "description": "차분한 세이지 그린 계열로 편안하고 자연스러운 이미지를 강조하는 테마",
        "page_bg": "#f1f5f0",
        "section_bg": "#fbfdfb",
        "soft_bg": "#dfe8dd",
        "text": "#263127",
        "muted": "#667468",
        "point": "#6f8b72",
        "line": "#d5ddd4",
        "card_bg": "#fbfdfb",
        "hero_bg": "#e6eee4",
        "hero_text": "#263127",
        "heading_align": "center",
    },
    "딥 네이비": {
        "description": "네이비와 실버 포인트로 신뢰감 있고 정돈된 느낌을 주는 테마",
        "page_bg": "#eef1f7",
        "section_bg": "#ffffff",
        "soft_bg": "#1f2d44",
        "text": "#203048",
        "muted": "#5f6c82",
        "point": "#6f88b5",
        "line": "#d8dee9",
        "card_bg": "#ffffff",
        "hero_bg": "#273853",
        "hero_text": "#ffffff",
        "heading_align": "left",
    },
    "테라코타 브라운": {
        "description": "따뜻한 브라운과 테라코타 포인트로 깊이 있고 안정적인 인상을 주는 테마",
        "page_bg": "#f7f0eb",
        "section_bg": "#fffaf7",
        "soft_bg": "#ead9cf",
        "text": "#3b2b24",
        "muted": "#7a655b",
        "point": "#b06f52",
        "line": "#e3d3ca",
        "card_bg": "#fffaf7",
        "hero_bg": "#efe1d8",
        "hero_text": "#3b2b24",
        "heading_align": "center",
    },
    "라벤더 그레이": {
        "description": "라벤더와 그레이 톤으로 부드럽고 세련된 분위기를 만드는 테마",
        "page_bg": "#f3f1f7",
        "section_bg": "#fcfbff",
        "soft_bg": "#e4dfec",
        "text": "#342f3c",
        "muted": "#726b7b",
        "point": "#8a7aa6",
        "line": "#ddd7e7",
        "card_bg": "#fcfbff",
        "hero_bg": "#ece7f3",
        "hero_text": "#342f3c",
        "heading_align": "center",
    },
}


FONTS = ["맑은 고딕", "고딕 계열", "명조 계열", "바탕"]

DEFAULT_KOREA_IMAGE = Path(__file__).resolve().parent / "assets" / "domestic_production.jpg"

IMAGE_SLOTS = [
    ("hero", "01. 대표 모델 착용컷", "첫 화면을 대표하는 핵심 이미지"),
    ("front", "02. 정면 착용컷", "상품 전체 실루엣이 가장 잘 보이는 정면 사진"),
    ("angle", "03. 사선 착용컷", "자연스러운 각도와 분위기를 보여주는 사진"),
    ("back", "04. 후면 착용컷", "뒷모습과 전체 균형을 확인할 수 있는 사진"),
    ("fabric", "05. 원단·소재 접사", "조직감, 표면감, 결감이 보이는 사진"),
    ("button", "06. 대표 디테일 접사", "단추, 지퍼, 장식, 주머니 등 핵심 디테일 사진"),
    ("collar", "07. 상단 디테일", "카라, 넥라인, 어깨선 등 상단 디테일 사진"),
    ("sleeve", "08. 소매·밑단 디테일", "소매, 커프스, 밑단, 절개선 등의 디테일 사진"),
    ("styling", "10. 추가 착용·코디컷", "다양한 분위기와 연출을 보여주는 사진"),
    ("size", "11. 사이즈 측정 이미지", "측정 위치와 기준을 안내하는 사진"),
]

DEFAULTS = {
    "theme": "클래식 아이보리",
    "body_font": "고딕 계열",
    "heading_font": "명조 계열",
    "page_width": 860,
    "base_font_size": 17,
    "section_spacing": 72,
    "jpg_quality": 90,
    "detail_page_mode": "혼합형 상세페이지",
    "product_type_preset": "블라우스형",
    "brand_line": "KOREAN FABRIC · MADE IN KOREA",
    "main_title": "편안하게 입고\n단정하게 완성되는 옷",
    "main_subtitle": "부담 없이 손이 가고, 입었을 때 분위기까지 자연스럽게 정돈되는 한 벌을 소개합니다.",
    "badge1_title": "국내원단",
    "badge1_text": "촉감과 조직감, 완성도를 고려해 고른 소재",
    "badge2_title": "100% 국내제작",
    "badge2_text": "국내 재단·봉제·마감으로 완성",
    "badge3_title": "편안한 옷맵시",
    "badge3_text": "움직임은 편안하게, 인상은 단정하게",
    "problems": "\n".join([
        "오래 입어도 불편하지 않은 옷을 찾는 분",
        "몸의 선을 과하게 드러내지 않으면서 단정하게 입고 싶은 분",
        "유행을 크게 타지 않아 여러 자리에 활용할 옷이 필요한 분",
        "사진뿐 아니라 실제 소재와 마감까지 중요하게 보는 분",
        "평소 외출부터 모임까지 자연스럽게 격식을 갖추고 싶은 분",
    ]),
    "story_enabled": True,
    "story_intro_title": "좋은 원단과 정직한 완성도를 전하고 싶었습니다",
    "story_intro_text": "오랫동안 여러 브랜드의 제품을 소개해 왔지만, 이름값과 실제 완성도가 늘 같지는 않았습니다. 겉으로 보이는 가격보다 원단의 촉감과 봉제의 안정감, 오래 입었을 때의 만족감이 더 중요하다는 것을 현장에서 자주 느꼈습니다. 그래서 국내에서 고른 원단과 숙련된 제작 과정을 바탕으로, 보기 좋은 수준을 넘어 오래 입기 좋은 제품을 전하고 싶었습니다.",
    "story_making_title": "우리가 중요하게 생각하는 기준",
    "story_making_text": "우리는 잠깐 눈길을 끄는 디자인보다 편안함과 단정함의 균형을 먼저 생각합니다. 몸을 답답하게 조이지 않으면서도 인상은 깔끔하게 정리되고, 유행을 급하게 좇지 않아 오래 손이 가며, 가까이에서 볼수록 소재와 마감의 차분한 완성도가 느껴지는 제품을 만들고자 합니다.",
    "story_customer_title": "고객을 대하는 우리의 마음",
    "story_customer_text": "우리는 구매하시는 분을 단순한 주문번호로 생각하지 않습니다. 사진보다 실제가 더 만족스럽도록 색감과 디테일을 최대한 정확하게 보여드리고, 장점만 과장하기보다 궁금한 부분은 솔직하게 안내하려 합니다. 한 번의 판매보다 다음에도 기분 좋게 다시 찾을 수 있는 신뢰를 더 소중하게 생각합니다.",
    "look_description": "몸을 조이지 않는 편안함과 흐트러지지 않는 옷맵시를 함께 고려해, 정면과 옆모습 모두 단정한 인상을 전합니다.",
    "point1_title": "편안함을 생각한 핏",
    "point1_text": "움직일 때의 부담은 덜고, 입었을 때 실루엣은 자연스럽게 정돈되도록 균형을 잡았습니다.",
    "point2_title": "차분하게 돋보이는 디자인",
    "point2_text": "과한 장식보다 선과 디테일, 소재의 분위기로 오래 보아도 쉽게 질리지 않는 인상을 완성합니다.",
    "point3_title": "여러 자리에 어울리는 활용도",
    "point3_text": "가벼운 외출부터 식사 자리, 모임, 여행까지 상황에 맞게 자연스럽게 입기 좋습니다.",
    "point4_title": "가까이에서 느껴지는 완성도",
    "point4_text": "원단의 결감과 봉제선, 여밈과 마감처럼 작은 부분까지 차분하게 완성했습니다.",
    "fabric_title": "눈으로 보이고 손끝으로 느껴지는 소재",
    "fabric_text": "국내원단 특유의 안정적인 조직감과 자연스러운 색감을 살렸습니다. 가까이에서 볼수록 소재의 결감과 완성도가 더욱 잘 드러납니다.",
    "button_title": "작은 차이가 만드는 전체 분위기",
    "button_text": "여밈과 장식, 절개와 마감처럼 작은 요소가 전체 인상을 좌우합니다. 눈에 띄는 과장보다 자연스럽게 어우러지는 디테일을 중요하게 생각합니다.",
    "korea_title": "국내원단 · 국내 재단 · 국내 봉제 · 국내 마감",
    "korea_text": "본 제품은 국내원단을 사용해 국내에서 재단, 봉제, 마감한 국내제작 상품입니다.",
    "group_order_enabled": True,
    "group_order_title": "단체 주문 및 도소매 상담 가능합니다",
    "group_order_text": "매장 납품, 단체 행사, 모임 의상 등 수량 주문과 도소매 거래 상담이 가능합니다. 필요한 수량과 일정, 거래 조건에 맞춰 자세히 안내드립니다.",
    "group_order_contact": "네이버 톡톡 또는 상품 문의로 편하게 상담해 주세요.",
    "uses": "\n".join([
        "편안한 외출|차려입지 않아도 단정한 인상",
        "가족·지인 모임|부담 없이 품위 있는 스타일",
        "여행·나들이|오래 입어도 편안한 코디",
        "식사·행사 자리|과하지 않게 격식을 갖춘 옷차림",
    ]),
    "specs": "\n".join([
        "제품명|상품명 입력",
        "색상|색상 입력",
        "사이즈|사이즈 입력",
        "소재|혼용률 입력",
        "제조국|대한민국",
        "제조자|판매자 협력업체",
        "세탁방법|세탁방법 입력",
        "기타|필요 정보 입력",
    ]),
    "size_name": "FREE",
    "size_shoulder": "입력",
    "size_chest": "입력",
    "size_sleeve": "입력",
    "size_armhole": "입력",
    "size_length": "입력",
    "notices": "\n".join([
        "모니터 환경과 촬영 조명에 따라 실제 색상이 다르게 보일 수 있습니다.",
        "디자인과 소재 특성에 따라 디테일 표현이 상품마다 조금씩 달라질 수 있습니다.",
        "원단 특성상 나염의 위치와 배열은 상품마다 조금씩 다를 수 있으며, 모든 상품이 동일하지 않습니다.",
        "실측 사이즈는 측정 위치와 방법에 따라 1~3cm 오차가 발생할 수 있습니다.",
        "첫 세탁 전 반드시 상품의 케어라벨과 세탁 안내를 확인해 주세요.",
        "장시간 마찰이나 강한 열은 소재 손상의 원인이 될 수 있습니다.",
    ]),
    "footer_title": "잘 차려입은 하루는, 옷에서 시작됩니다",
    "footer_text": "편안하게 입고도 단정해 보이는 옷, 오래 두고 자연스럽게 손이 가는 국내제작 여성복을 제안합니다.",
}


PRODUCT_PRESETS = {
    "블라우스형": {
        "main_title": "편안하게 입고\n단정하게 완성되는 블라우스",
        "main_subtitle": "가볍게 손이 가면서도 차려입은 듯 정돈된 분위기를 전하는 블라우스를 소개합니다.",
        "look_description": "상체 라인을 답답하게 조이지 않으면서도 전체 인상이 깔끔하게 정리되도록 균형을 고려했습니다.",
        "point1_title": "부드럽게 흐르는 실루엣",
        "point1_text": "몸을 따라 자연스럽게 떨어져 편안하면서도 단정한 느낌을 전합니다.",
        "point2_title": "활용도 높은 상의",
        "point2_text": "팬츠, 스커트, 이너와 매치하기 좋아 데일리부터 모임까지 폭넓게 활용할 수 있습니다.",
        "point3_title": "가볍고 산뜻한 착용감",
        "point3_text": "오랜 시간 입어도 답답함이 덜하고 계절감에 맞춰 다양하게 연출하기 좋습니다.",
        "point4_title": "가까이서 더 느껴지는 완성도",
        "point4_text": "넥라인과 여밈, 소매와 밑단까지 전체 분위기를 해치지 않도록 차분하게 마감했습니다.",
        "fabric_title": "블라우스의 분위기를 살리는 소재",
        "fabric_text": "가벼워 보이면서도 지나치게 힘없지 않은 소재를 골라, 입었을 때 자연스러운 흐름과 단정한 인상을 함께 느낄 수 있습니다.",
        "button_title": "디자인을 정리해 주는 디테일",
        "button_text": "카라, 여밈, 장식, 절개처럼 작은 요소들이 전체 인상을 깔끔하게 정리해 주도록 구성했습니다.",
        "uses": "편안한 외출|과하지 않게 단정한 분위기\n가족·지인 모임|부드럽고 정돈된 스타일\n식사 자리|차려입은 듯 자연스러운 코디\n여행·나들이|가볍고 활용도 높은 상의",
        "specs": "제품명|블라우스 상품명 입력\n색상|색상 입력\n사이즈|사이즈 입력\n소재|혼용률 입력\n제조국|대한민국\n제조자|판매자 협력업체\n세탁방법|세탁방법 입력\n기타|필요 정보 입력",
    },
    "원피스형": {
        "main_title": "한 벌로 편안하고\n단정하게 완성되는 원피스",
        "main_subtitle": "과하게 꾸미지 않아도 한 벌만으로 분위기와 편안함을 함께 챙길 수 있는 원피스를 소개합니다.",
        "look_description": "몸의 선을 부담스럽게 드러내지 않으면서도 전체 비율이 단정하게 보이도록 실루엣을 정리했습니다.",
        "point1_title": "한 벌로 완성되는 스타일",
        "point1_text": "코디 고민을 덜어주면서도 자연스럽게 차려입은 인상을 전합니다.",
        "point2_title": "편안한 움직임",
        "point2_text": "장시간 착용해도 답답함이 덜하고 일상과 외출 모두에 잘 어울립니다.",
        "point3_title": "부담 없는 분위기",
        "point3_text": "화려함보다 차분한 멋을 살려 다양한 자리에서 편안하게 입기 좋습니다.",
        "point4_title": "실루엣을 살리는 마감",
        "point4_text": "넥라인과 허리선, 소매와 밑단까지 전체 흐름을 자연스럽게 완성했습니다.",
        "fabric_title": "원피스의 흐름을 살리는 소재",
        "fabric_text": "착용 시 실루엣이 무겁지 않게 떨어지면서도 비침, 두께, 조직감의 균형이 안정적으로 느껴지도록 구성했습니다.",
        "button_title": "한 벌의 분위기를 좌우하는 디테일",
        "button_text": "여밈, 절개, 장식, 포켓 같은 요소를 과하지 않게 배치해 전체적인 완성도를 높였습니다.",
        "uses": "일상 외출|한 벌만으로 자연스러운 코디\n가족 모임|부담 없이 단정한 스타일\n식사·행사 자리|과하지 않게 격식을 갖춘 분위기\n여행·나들이|편안하면서도 사진이 잘 받는 코디",
        "specs": "제품명|원피스 상품명 입력\n색상|색상 입력\n사이즈|사이즈 입력\n소재|혼용률 입력\n제조국|대한민국\n제조자|판매자 협력업체\n세탁방법|세탁방법 입력\n기타|필요 정보 입력",
    },
    "재킷형": {
        "main_title": "차분한 격식과 편안함을 담은 재킷",
        "main_subtitle": "가볍게 걸쳐도 인상이 정돈되고, 여러 자리에서 활용하기 좋은 재킷을 소개합니다.",
        "look_description": "어깨선과 앞여밈, 전체 비율이 깔끔하게 정리되어 걸쳤을 때 단정한 인상을 전합니다.",
        "point1_title": "정돈된 실루엣",
        "point1_text": "과하게 힘주지 않아도 전체 라인이 차분하게 정리되도록 설계했습니다.",
        "point2_title": "다양한 이너와 매치",
        "point2_text": "블라우스, 티셔츠, 원피스 위에 가볍게 걸치기 좋아 활용 범위가 넓습니다.",
        "point3_title": "격식과 실용성의 균형",
        "point3_text": "모임이나 외출은 물론 평소에도 부담 없이 입기 좋도록 완성했습니다.",
        "point4_title": "재킷다운 마감 완성도",
        "point4_text": "카라, 앞여밈, 절개, 소매 마감까지 전체 구조를 안정감 있게 정리했습니다.",
        "fabric_title": "형태감을 살리는 소재",
        "fabric_text": "너무 무겁지 않으면서도 재킷 특유의 단정한 형태감이 살아나도록 소재의 밀도와 조직감을 고려했습니다.",
        "button_title": "재킷의 분위기를 완성하는 요소",
        "button_text": "단추, 카라, 포켓, 절개선 등 재킷의 인상을 좌우하는 요소를 균형 있게 담았습니다.",
        "uses": "격식 있는 외출|과하지 않은 단정함\n가족·지인 모임|깔끔하고 안정적인 코디\n식사 자리|가볍게 걸쳐 완성하는 스타일\n간절기 활용|실용성과 분위기를 함께 챙기는 아이템",
        "specs": "제품명|재킷 상품명 입력\n색상|색상 입력\n사이즈|사이즈 입력\n소재|혼용률 입력\n제조국|대한민국\n제조자|판매자 협력업체\n세탁방법|세탁방법 입력\n기타|필요 정보 입력",
    },
    "티셔츠형": {
        "main_title": "편안함 속에 단정함을 담은 티셔츠",
        "main_subtitle": "매일 손이 가는 편안함에 깔끔한 인상까지 더한 티셔츠를 소개합니다.",
        "look_description": "몸에 지나치게 달라붙지 않으면서도 전체 인상이 흐트러져 보이지 않도록 균형을 잡았습니다.",
        "point1_title": "매일 입기 좋은 편안함",
        "point1_text": "부드러운 착용감과 부담 없는 핏으로 일상에서 자주 손이 갑니다.",
        "point2_title": "단정한 기본 디자인",
        "point2_text": "심플하지만 밋밋하지 않게, 다양한 하의와 자연스럽게 어울립니다.",
        "point3_title": "레이어드하기 좋은 활용도",
        "point3_text": "단독 착용은 물론 재킷이나 조끼 안에도 깔끔하게 매치됩니다.",
        "point4_title": "기본일수록 중요한 완성도",
        "point4_text": "넥라인, 어깨선, 소매와 밑단처럼 기본 티셔츠일수록 작은 마감 차이를 중요하게 보았습니다.",
        "fabric_title": "매일 입고 싶은 소재감",
        "fabric_text": "편안한 촉감과 안정적인 조직감을 살려 단독으로 입어도 부담 없고 다양한 계절에 활용하기 좋습니다.",
        "button_title": "기본을 살리는 디테일",
        "button_text": "넥라인, 봉제선, 절개, 작은 장식처럼 티셔츠의 인상을 좌우하는 부분을 깔끔하게 마무리했습니다.",
        "uses": "일상 외출|부담 없이 손이 가는 코디\n가족·지인 모임|편안하지만 깔끔한 인상\n재킷 이너|안정감 있는 레이어드\n여행·나들이|가볍고 실용적인 착용",
        "specs": "제품명|티셔츠 상품명 입력\n색상|색상 입력\n사이즈|사이즈 입력\n소재|혼용률 입력\n제조국|대한민국\n제조자|판매자 협력업체\n세탁방법|세탁방법 입력\n기타|필요 정보 입력",
    },
    "팬츠형": {
        "main_title": "편안한 움직임과 단정한 실루엣의 팬츠",
        "main_subtitle": "매일 입기 좋으면서도 전체 코디를 안정감 있게 정리해 주는 팬츠를 소개합니다.",
        "look_description": "허리부터 밑단까지 답답함은 덜고 라인은 깔끔하게 보이도록 균형을 고려했습니다.",
        "point1_title": "편안한 착용감",
        "point1_text": "오랜 시간 착용해도 부담이 덜하고 일상에서 자연스럽게 손이 갑니다.",
        "point2_title": "정돈된 하체 실루엣",
        "point2_text": "과하게 붙거나 부해 보이지 않도록 안정감 있는 라인을 완성했습니다.",
        "point3_title": "다양한 상의와 매치",
        "point3_text": "블라우스, 티셔츠, 재킷과 두루 어울려 데일리 활용도가 높습니다.",
        "point4_title": "팬츠에서 중요한 디테일",
        "point4_text": "허리선, 주머니, 절개, 밑단 마감까지 실제 착용감을 생각해 꼼꼼하게 살폈습니다.",
        "fabric_title": "움직임을 고려한 소재",
        "fabric_text": "팬츠는 자주 입는 만큼 편안함과 형태감을 함께 살릴 수 있는 소재 선택이 중요하다고 생각했습니다.",
        "button_title": "착용감을 좌우하는 요소",
        "button_text": "허리 구조, 지퍼와 여밈, 포켓과 봉제선 등 실제 입었을 때의 편안함과 완성도를 함께 고려했습니다.",
        "uses": "일상 외출|매일 입기 좋은 기본 팬츠\n모임 코디|상의를 단정하게 받쳐주는 스타일\n여행·나들이|오래 입어도 부담이 적은 착용감\n다양한 상의 매치|코디 활용도가 높은 아이템",
        "specs": "제품명|팬츠 상품명 입력\n색상|색상 입력\n사이즈|사이즈 입력\n소재|혼용률 입력\n제조국|대한민국\n제조자|판매자 협력업체\n세탁방법|세탁방법 입력\n기타|필요 정보 입력",
    },
    "조끼형": {
        "main_title": "가볍게 더해 완성하는 실용적인 조끼",
        "main_subtitle": "가벼운 레이어드만으로도 분위기를 정돈해 주는 조끼형 아이템을 소개합니다.",
        "look_description": "이너 위에 부담 없이 걸치기 좋으면서도 전체 코디가 정리되어 보이도록 실루엣을 구성했습니다.",
        "point1_title": "레이어드하기 좋은 활용성",
        "point1_text": "블라우스, 티셔츠, 원피스 위에 자연스럽게 더해 코디의 폭을 넓혀 줍니다.",
        "point2_title": "가볍고 실용적인 착용",
        "point2_text": "답답하지 않게 걸치기 좋고 계절 변화에 따라 다양하게 연출할 수 있습니다.",
        "point3_title": "코디를 정리하는 포인트",
        "point3_text": "단조로운 차림에도 은근한 포인트를 더해 전체 인상을 차분하게 정리해 줍니다.",
        "point4_title": "작은 구조까지 살핀 완성도",
        "point4_text": "암홀, 앞여밈, 포켓과 밑단처럼 조끼의 활용도를 결정하는 부분까지 꼼꼼하게 살폈습니다.",
        "fabric_title": "겹쳐 입기 좋은 소재감",
        "fabric_text": "이너와 함께 입었을 때 답답하지 않으면서도 조끼 특유의 존재감이 자연스럽게 살아나도록 소재를 구성했습니다.",
        "button_title": "레이어드 아이템의 분위기를 살리는 디테일",
        "button_text": "여밈, 포켓, 절개선 등 조끼의 실용성과 분위기를 좌우하는 디테일을 균형 있게 정리했습니다.",
        "uses": "가벼운 외출|간단히 더해 완성하는 코디\n레이어드 스타일|이너 위에 자연스럽게 매치\n간절기 활용|실용성과 분위기를 함께 챙기는 아이템\n모임 코디|은근한 포인트를 더하는 스타일",
        "specs": "제품명|조끼 상품명 입력\n색상|색상 입력\n사이즈|사이즈 입력\n소재|혼용률 입력\n제조국|대한민국\n제조자|판매자 협력업체\n세탁방법|세탁방법 입력\n기타|필요 정보 입력",
    },
    "아우터형": {
        "main_title": "가볍게 걸쳐 분위기를 완성하는 아우터",
        "main_subtitle": "한 겹 더하는 것만으로도 인상과 실용성을 함께 챙길 수 있는 아우터를 소개합니다.",
        "look_description": "이너 위에 자연스럽게 걸쳐졌을 때 전체 비율이 안정감 있게 보이도록 실루엣과 길이감을 고려했습니다.",
        "point1_title": "걸치기 좋은 실용성",
        "point1_text": "계절 변화나 실내외 온도차에 대응하기 좋고 자주 활용할 수 있습니다.",
        "point2_title": "코디를 완성하는 존재감",
        "point2_text": "가벼운 이너 위에 걸쳐도 전체 차림이 단정하게 정리됩니다.",
        "point3_title": "다양한 스타일링 가능",
        "point3_text": "데일리, 모임, 외출 등 여러 상황에 맞춰 폭넓게 활용할 수 있습니다.",
        "point4_title": "겉옷일수록 중요한 마감",
        "point4_text": "카라, 여밈, 포켓, 소매와 밑단 등 눈에 잘 띄는 부분까지 안정감 있게 완성했습니다.",
        "fabric_title": "아우터의 분위기를 살리는 소재",
        "fabric_text": "무게감과 촉감, 형태감을 함께 고려해 걸쳤을 때 자연스럽고 단정한 인상이 살아나도록 구성했습니다.",
        "button_title": "아우터의 인상을 결정하는 디테일",
        "button_text": "단추와 지퍼, 절개와 포켓, 카라와 마감처럼 전체 분위기를 좌우하는 요소를 세심하게 살폈습니다.",
        "uses": "일상 외출|가볍게 걸치기 좋은 아우터\n간절기 코디|온도차에 대응하는 실용성\n모임·식사 자리|단정함을 더하는 마무리\n여행·나들이|활용도 높은 겉옷 아이템",
        "specs": "제품명|아우터 상품명 입력\n색상|색상 입력\n사이즈|사이즈 입력\n소재|혼용률 입력\n제조국|대한민국\n제조자|판매자 협력업체\n세탁방법|세탁방법 입력\n기타|필요 정보 입력",
    },
}


def initialize_state() -> None:
    for key, value in DEFAULTS.items():
        st.session_state.setdefault(key, value)


def current_config() -> Dict:
    return {key: st.session_state.get(key, value) for key, value in DEFAULTS.items()}


def apply_detail_mode(mode: str) -> None:
    st.session_state["detail_page_mode"] = mode
    if mode == "스토리형 상세페이지":
        st.session_state["story_enabled"] = True
        st.session_state["group_order_enabled"] = True
        st.session_state["main_subtitle"] = "국내원단과 국내제작의 진정성을 바탕으로, 오래 입을수록 편안함과 단정한 분위기가 살아나는 한 벌을 소개합니다."
        st.session_state["footer_title"] = "좋은 옷에는 만드는 마음이 담겨 있습니다"
        st.session_state["footer_text"] = "좋은 소재와 정직한 제작, 그리고 고객을 생각하는 마음까지 담아 오래 곁에 둘 수 있는 옷을 제안합니다."
    elif mode == "판매집중형 상세페이지":
        st.session_state["story_enabled"] = False
        st.session_state["group_order_enabled"] = True
        st.session_state["main_subtitle"] = "편안하게 입기 좋고 단정한 인상까지 챙길 수 있도록 소재, 핏, 마감을 균형 있게 담았습니다."
        st.session_state["footer_title"] = "사진으로 보고, 실제로 입었을 때 더 만족스러운 옷"
        st.session_state["footer_text"] = "외출부터 모임까지 자연스럽게 활용하기 좋고, 원단과 마감의 완성도까지 꼼꼼하게 확인할 수 있습니다."
    else:
        st.session_state["story_enabled"] = True
        st.session_state["group_order_enabled"] = True
        st.session_state["main_subtitle"] = "국내원단과 국내제작의 진정성을 바탕으로, 입는 순간의 편안함과 단정한 분위기를 함께 전하는 한 벌을 소개합니다."
        st.session_state["footer_title"] = "잘 차려입은 하루는, 옷에서 시작됩니다"
        st.session_state["footer_text"] = "브랜드 스토리의 진정성과 판매 포인트를 함께 담아, 보고 공감하고 실제로 만족할 수 있는 상품으로 제안합니다."


def apply_product_preset(preset_name: str) -> None:
    preset = PRODUCT_PRESETS[preset_name]
    st.session_state["product_type_preset"] = preset_name
    for key, value in preset.items():
        st.session_state[key] = value


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

st.subheader("상세페이지 모드 빠른 선택")
st.caption("버튼 한 번으로 섹션 구성 방향을 바꿀 수 있습니다. 선택 후에도 모든 문구는 자유롭게 수정할 수 있습니다.")
mode_cols = st.columns(3)
mode_labels = ["스토리형 상세페이지", "판매집중형 상세페이지", "혼합형 상세페이지"]
mode_desc = {
    "스토리형 상세페이지": "브랜드 스토리와 제작 철학을 가장 앞쪽에 배치합니다.",
    "판매집중형 상세페이지": "핵심 장점과 구매 정보 중심으로 빠르게 설득하는 구성입니다.",
    "혼합형 상세페이지": "스토리를 위쪽에 두고 판매 포인트도 함께 살리는 균형형 구성입니다.",
}
for col, label in zip(mode_cols, mode_labels):
    with col:
        st.caption(mode_desc[label])
        if st.button(label, use_container_width=True):
            apply_detail_mode(label)
            st.rerun()
st.info(f"현재 적용 모드: {st.session_state.get('detail_page_mode', '혼합형 상세페이지')}")

st.subheader("상품 종류 빠른 선택")
st.caption("상품군에 맞는 기본 문구를 버튼 한 번으로 적용합니다. 적용 후 세부 문구는 자유롭게 수정할 수 있습니다.")
preset_labels = ["블라우스형", "원피스형", "재킷형", "티셔츠형", "팬츠형", "조끼형", "아우터형"]
for row_start in range(0, len(preset_labels), 4):
    cols = st.columns(4)
    for col, label in zip(cols, preset_labels[row_start:row_start+4]):
        with col:
            if st.button(label, use_container_width=True):
                apply_product_preset(label)
                st.rerun()
st.info(f"현재 적용 상품군: {st.session_state.get('product_type_preset', '블라우스형')}")

with st.sidebar:
    st.header("1. 디자인 설정")
    st.caption(f"현재 모드: {st.session_state.get('detail_page_mode', '혼합형 상세페이지')}")
    st.caption(f"현재 상품군: {st.session_state.get('product_type_preset', '블라우스형')}")
    st.selectbox("상세페이지 테마", list(THEMES.keys()), key="theme")
    st.info(THEMES[st.session_state.theme]["description"])
    st.caption("브랜드 스토리를 강조하려면 클래식 아이보리, 세이지 그린, 테라코타 브라운이 잘 어울립니다.")
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

    st.subheader("브랜드 스토리")
    st.checkbox("상세페이지에 브랜드 스토리 표시", key="story_enabled")
    st.text_input("스토리 1 제목", key="story_intro_title")
    st.text_area("스토리 1 내용", key="story_intro_text", height=150)
    st.text_input("스토리 2 제목", key="story_making_title")
    st.text_area("스토리 2 내용", key="story_making_text", height=150)
    st.text_input("스토리 3 제목", key="story_customer_title")
    st.text_area("스토리 3 내용", key="story_customer_text", height=150)

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

    st.subheader("국내제작 안내")
    st.info("국내제작 구역은 저장소의 고정 이미지가 자동으로 들어갑니다. 상품마다 다시 업로드할 필요가 없습니다.")

    st.subheader("단체 주문·도소매 안내")
    st.checkbox("상세페이지에 단체 주문·도소매 안내 표시", key="group_order_enabled")
    st.text_input("단체 주문·도소매 제목", key="group_order_title")
    st.text_area("단체 주문·도소매 설명", key="group_order_text", height=110)
    st.text_input("상담 유도 문구", key="group_order_contact")

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
    st.info("나염 패턴 제품은 같은 원단이라도 위치와 배열이 조금씩 다를 수 있다는 안내 문구를 기본으로 포함했습니다.")
    st.text_area("한 줄에 한 항목씩 입력", key="notices", height=220)

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

    st.subheader("09. 국내제작 이미지 · 고정 사용")
    st.caption("아래 이미지는 모든 상세페이지에 자동으로 들어가며 별도 업로드가 필요하지 않습니다.")
    if DEFAULT_KOREA_IMAGE.exists():
        st.image(str(DEFAULT_KOREA_IMAGE), use_container_width=True)
    else:
        st.error("assets/domestic_production.jpg 파일을 찾을 수 없습니다.")

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
    if DEFAULT_KOREA_IMAGE.exists():
        core_images["korea"] = BytesIO(DEFAULT_KOREA_IMAGE.read_bytes())
    else:
        core_images["korea"] = None
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
