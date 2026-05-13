import streamlit as st
import google.generativeai as genai
from pptx import Presentation
from pptx.util import Inches
from PIL import Image
import io

st.set_page_config(page_title="이미지 PPT 변환기")
st.title("🖼️ 범용 이미지-PPT 변환기")

# [수정됨] 사이드바 입력 대신 Secrets에서 자동으로 키를 가져옵니다.
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    # 혹시 Secrets 설정을 안 했을 경우를 대비해 사이드바 노출
    api_key = st.sidebar.text_input("Gemini API Key를 입력하세요", type="password")

if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('models/gemini-1.5-flash')

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
        st.download_button("📥 PPT 다운로드", data=ppt_out.getvalue(), file_name="converted.pptx")
else:
    st.warning("API 키가 설정되지 않았습니다. Streamlit Settings > Secrets에 키를 등록하거나 사이드바에 입력해주세요.")
