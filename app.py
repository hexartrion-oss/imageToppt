import streamlit as st
import google.generativeai as genai
from pptx import Presentation
from PIL import Image
import io

st.title("🖼️ 범용 이미지-PPT 변환기")

if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)

    # 모델 설정 (가장 호환성 높은 이름으로 시도)
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
    except:
        model = genai.GenerativeModel('gemini-1.5-pro')

    uploaded_files = st.file_uploader("이미지 파일 선택", accept_multiple_files=True)

    if uploaded_files and st.button("PPT 생성"):
        prs = Presentation()
        for uploaded_file in uploaded_files:
            slide = prs.slides.add_slide(prs.slide_layouts[6])
            img = Image.open(uploaded_file)
            
            # 분석 시도
            try:
                # v1beta 에러를 피하기 위해 가장 단순한 호출 방식 사용
                response = model.generate_content(["Extract text from this image", img])
                
                from pptx.util import Inches
                txBox = slide.shapes.add_textbox(Inches(1), Inches(1), Inches(8), Inches(5))
                txBox.text_frame.text = response.text
            except Exception as e:
                st.error(f"분석 오류: {e}")
        
        ppt_out = io.BytesIO()
        prs.save(ppt_out)
        st.download_button("PPT 다운로드", data=ppt_out.getvalue(), file_name="result.pptx")
else:
    st.error("Secrets에 GEMINI_API_KEY를 등록해주세요.")
