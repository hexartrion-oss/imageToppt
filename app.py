import streamlit as st
from google import genai
from pptx import Presentation
from pptx.util import Inches, Pt
from PIL import Image
import io
import json

st.set_page_config(page_title="이미지-PPT 변환기", layout="wide")
st.title("🎨 원본 재현형 이미지-PPT 변환기")

# 1. API 키 설정
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    api_key = st.sidebar.text_input("Gemini API Key", type="password")

if api_key:
    # 최신 google-genai 클라이언트 설정
    client = genai.Client(api_key=api_key)

    uploaded_files = st.file_uploader("이미지를 업로드하세요", accept_multiple_files=True, type=['jpg', 'png', 'jpeg'])

    if uploaded_files and st.button("🚀 PPT 생성 시작"):
        prs = Presentation()
        prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)

        with st.spinner('이미지 분석 중...'):
            for uploaded_file in uploaded_files:
                slide = prs.slides.add_slide(prs.slide_layouts[6])
                
                # 배경 이미지 삽입
                img_bytes = uploaded_file.read()
                slide.shapes.add_picture(io.BytesIO(img_bytes), 0, 0, width=prs.slide_width, height=prs.slide_height)
                
                try:
                    # 최신 모델 호출 방식
                    response = client.models.generate_content(
                        model="gemini-2.0-flash", # 최신 모델 사용 가능
                        contents=["Extract text with JSON format: [{'text': '...', 'x': 10, 'y': 20, 'w': 30, 'h': 5}]", Image.open(io.BytesIO(img_bytes))]
                    )
                    
                    res_text = response.text
                    start, end = res_text.find("["), res_text.rfind("]") + 1
                    text_blocks = json.loads(res_text[start:end])
                    
                    for block in text_blocks:
                        left = prs.slide_width * (float(block['x']) / 100)
                        top = prs.slide_height * (float(block['y']) / 100)
                        width = prs.slide_width * (float(block['w']) / 100)
                        height = prs.slide_height * (float(block['h']) / 100)
                        
                        txBox = slide.shapes.add_textbox(left, top, width, height)
                        tf = txBox.text_frame
                        tf.word_wrap = True
                        p = tf.add_paragraph()
                        p.text = str(block['text'])
                        p.font.size = Pt(14)
                except:
                    continue

            ppt_out = io.BytesIO()
            prs.save(ppt_out)
            st.success("✅ 완료!")
            st.download_button("📥 PPT 다운로드", ppt_out.getvalue(), "result.pptx")
