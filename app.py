import streamlit as st
import google.generativeai as genai
from pptx import Presentation
from pptx.util import Inches, Pt
from PIL import Image
import io
import json
import re

st.set_page_config(page_title="원본 재현 PPT 변환기", layout="wide")
st.title("🎨 원본 재현형 이미지-PPT 변환기")

if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    api_key = st.sidebar.text_input("Gemini API Key", type="password")

if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    uploaded_files = st.file_uploader("슬라이드 이미지들을 업로드하세요", accept_multiple_files=True, type=['jpg', 'png', 'jpeg'])

    if uploaded_files and st.button("🚀 원본 재현 PPT 생성 시작"):
        prs = Presentation()
        prs.slide_width = Inches(13.333)
        prs.slide_height = Inches(7.5)

        with st.spinner('이미지 분석 및 레이어 작업 중...'):
            for uploaded_file in uploaded_files:
                slide = prs.slides.add_slide(prs.slide_layouts[6])
                
                # 1. 이미지 읽기 및 배경 삽입
                img_data = uploaded_file.read()
                img_stream = io.BytesIO(img_data)
                slide.shapes.add_picture(img_stream, 0, 0, width=prs.slide_width, height=prs.slide_height)
                
                # 2. AI 분석 프롬프트 (JSON 형식을 매우 구체적으로 요청)
                img = Image.open(io.BytesIO(img_data))
                prompt = """
                Extract all text with coordinates. Return ONLY a JSON list like this:
                [{"text": "Sample text", "x": 10, "y": 20, "w": 30, "h": 5}]
                The values x, y, w, h are percentages (0-100) of the image size.
                Do not include any Markdown like ```json or explanation. Just the raw list.
                """
                
                try:
                    response = model.generate_content([prompt, img])
                    raw_text = response.text.strip()
                    
                    # 마크다운 기호가 포함된 경우 제거하는 보정 로직
                    clean_json = re.sub(r'```(?:json)?|
```', '', raw_text).strip()
                    text_blocks = json.loads(clean_json)
                    
                    # 3. 텍스트 레이어 생성
                    for block in text_blocks:
                        # 좌표값이 문자열로 들어올 경우를 대비해 float 변환
                        bx, by = float(block['x']), float(block['y'])
                        bw, bh = float(block['w']), float(block['h'])
                        
                        left = prs.slide_width * (bx / 100)
                        top = prs.slide_height * (by / 100)
                        width = prs.slide_width * (bw / 100)
                        height = prs.slide_height * (bh / 100)
                        
                        txBox = slide.shapes.add_textbox(left, top, width, height)
                        tf = txBox.text_frame
                        tf.word_wrap = True
                        p = tf.add_paragraph()
                        p.text = block['text']
                        p.font.size = Pt(16)
                        p.font.bold = True # 시인성을 위해 볼드체 적용
                        
                except Exception as e:
                    # 텍스트 추출에 실패해도 슬라이드(이미지)는 남겨둡니다.
                    st.warning(f"{uploaded_file.name}: 텍스트 레이어 생성 실패 (이미지만 삽입됨). 사유: {e}")

            # 파일 생성
            ppt_out = io.BytesIO()
            prs.save(ppt_out)
            st.success("✅ 작업 완료! 아래 버튼을 눌러 다운로드하세요.")
            st.download_button("📥 PPT 다운로드", data=ppt_out.getvalue(), file_name="ai_repro_slide.pptx")
else:
    st.info("API 키를 등록해 주세요.")
