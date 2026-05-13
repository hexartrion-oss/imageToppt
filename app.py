import streamlit as st
import google.generativeai as genai
from pptx import Presentation
from pptx.util import Inches
from PIL import Image
import io

st.set_page_config(page_title="이미지 PPT 변환기")
st.title("🖼️ 범용 이미지-PPT 변환기")

# 사이드바 설정
api_key = st.sidebar.text_input("Gemini API Key를 입력하세요", type="password")

if api_key:
    genai.configure(api_key=api_key)
    # 모델 경로에 'models/'를 추가하여 NotFound 에러 예방
    model = genai.GenerativeModel('models/gemini-1.5-flash')

    # 들여쓰기 주의 (스페이스 4칸)
    uploaded_files = st.file_uploader("이미지 파일들을 선택하세요", accept_multiple_files=True, type=['jpg', 'png', 'jpeg'])

    if uploaded_files and st.button("PPT 생성 시작"):
        prs = Presentation()
        for uploaded_file in uploaded_files:
            slide = prs.slides.add_slide(prs.slide_layouts[6])
            img = Image.open(uploaded_file)
            
            # AI 분석 및 텍스트 추출
            response = model.generate_content(["이 이미지의 모든 텍스트를 추출해줘", img])
            
            txBox = slide.shapes.add_textbox(Inches(1), Inches(1), Inches(8), Inches(5))
            txBox.text_frame.text = response.text
            
        ppt_out = io.BytesIO()
        prs.save(ppt_out)
        st.success("변환 완료!")
        st.download_button("📥 PPT 다운로드", data=ppt_out.getvalue(), file_name="result.pptx")
