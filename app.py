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
st.write("이미지를 배경으로 깔고, 그 위에 편집 가능한 텍스트를 정확한 위치에 얹어 드립니다.")

if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    api_key = st.sidebar.text_input("Gemini API Key", type="password")

if api_key:
    genai.configure(api_key=api_key)
    
    # 모델 설정
    model = genai.GenerativeModel('gemini-1.5-flash')

    uploaded_files = st.file_uploader("슬라이드 이미지들을 업로드하세요", accept_multiple_files=True, type=['jpg', 'png', 'jpeg'])

    if uploaded_files and st.button("🚀 원본 재현 PPT 생성 시작"):
        prs = Presentation()
        # 슬라이드 크기 설정 (표준 16:9)
        prs.slide_width = Inches(13.333)
        prs.slide_height = Inches(7.5)

        with st.spinner('이미지 분석 및 레이어 작업 중...'):
            for uploaded_file in uploaded_files:
                slide = prs.slides.add_slide(prs.slide_layouts[6]) # 빈 슬라이드
                
                # 1. 원본 이미지 삽입 (슬라이드 전체 크기에 맞춤)
                img_data = uploaded_file.read()
                img_stream = io.BytesIO(img_data)
                slide.shapes.add_picture(img_stream, 0, 0, width=prs.slide_width, height=prs.slide_height)
                
                # 2. AI에게 좌표가 포함된 JSON 데이터 요청
                img = Image.open(io.BytesIO(img_data))
                prompt = """
                분석된 모든 텍스트를 다음 JSON 형식으로만 응답해줘:
                [{"text": "내용", "x": 좌측상단_비율(0-100), "y": 좌측상단_비율(0-100), "w": 너비_비율(0-100), "h": 높이_비율(0-100)}]
                이미지의 해상도에 맞춰 텍스트가 위치한 곳의 정확한 좌표를 계산해줘.
                """
                
                try:
                    response = model.generate_content([prompt, img])
                    # JSON 데이터만 추출 (마크다운 제거)
                    json_str = re.search(r'\[.*\]', response.text, re.DOTALL).group()
                    text_blocks = json.loads(json_str)
                    
                    # 3. 텍스트 박스 레이어 얹기
                    for block in text_blocks:
                        left = prs.slide_width * (block['x'] / 100)
                        top = prs.slide_height * (block['y'] / 100)
                        width = prs.slide_width * (block['w'] / 100)
                        height = prs.slide_height * (block['h'] / 100)
                        
                        txBox = slide.shapes.add_textbox(left, top, width, height)
                        tf = txBox.text_frame
                        tf.word_wrap = True
                        p = tf.add_paragraph()
                        p.text = block['text']
                        # 텍스트가 이미지 위에서 잘 보이도록 기본 설정
                        p.font.size = Pt(14)
                        
                except Exception as e:
                    st.error(f"{uploaded_file.name} 분석 중 오류 발생. 텍스트 레이어를 생성하지 못했습니다.")

            # 다운로드
            ppt_out = io.BytesIO()
            prs.save(ppt_out)
            st.success("✅ 원본 재현 PPT 완성!")
            st.download_button("📥 완성된 PPT 다운로드", data=ppt_out.getvalue(), file_name="reproduced_presentation.pptx")
else:
    st.info("API 키를 등록해 주세요.")
