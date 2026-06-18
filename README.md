# 네이버 상세페이지 JPG 자동 제작기

Streamlit에서 상품 문구와 사진을 입력하면 네이버 스마트스토어에 바로 올릴 수 있는 긴 JPG 상세페이지를 만듭니다.

## 주요 변경사항

- HTML 다운로드 제거
- 완성된 긴 JPG를 앱에서 직접 생성하고 다운로드
- 기본 사진 11개 배치
- 추가 모델 착용컷 여러 장 업로드
- 추가 원단·봉제·단추 디테일컷 여러 장 업로드
- 추가 코디·기타 상세 이미지 여러 장 업로드
- 추가 사진은 세 구역 합계 최대 30장 반영
- 한글 JPG 렌더링을 위해 Noto CJK 폰트 자동 설치

## GitHub 저장소 파일

```text
app.py
jpg_renderer.py
requirements.txt
packages.txt
README.md
.streamlit/config.toml
```

Streamlit Community Cloud에서 Main file path는 `app.py`로 설정합니다.
