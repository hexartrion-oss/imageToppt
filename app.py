import streamlit as st
from pptx import Presentation
from pptx.util import Inches, Pt
import google.generativeai as genai
from PIL import Image
import io

# 1. AI 세팅 (사용자의 API 키를 입력받거나 환경변수 사용)
st.title("🚀 범용 이미지-PPT 변환기")
api_key = st.sidebar.text_input("Gemini API Key를 입력하세요", type="password")

if api_key:
    genai.configure(api_key=api_key)# 기존 코드
# model = genai.GenerativeModel('gemini-1.5-flash')

# 수정 코드 (버전 명시)
model = genai.GenerativeModel('models/gemini-1.5-flash') 
# 또는 'models/gemini-1.5-flash-latest'
    # 2. 여러 이미지 업로드 가능
    uploaded_files = st.file_uploader("변환할 이미지들을 모두 선택하세요", accept_multiple_files=True, type=['jpg', 'png'])

    if uploaded_files and st.button("PPT 생성 시작"):
        prs = Presentation()

        for uploaded_file in uploaded_files:
            # 슬라이드 추가
            slide = prs.slides.add_slide(prs.slide_layouts[6]) # 빈 슬라이드
            img = Image.open(uploaded_file)
            
            # 3. Gemini Vision으로 이미지 분석 (동적 추출)
            # 특정 이미지에 국한되지 않도록 AI에게 좌표를 요청합니다.
            prompt = "이 이미지의 모든 텍스트를 찾아서 [텍스트내용, x좌표, y좌표, 폰트크기] 리스트로 반환해줘. 좌표는 0~100 사이의 상대값으로 줘."
            response = model.generate_content([prompt, img])
            
            # 4. 분석된 데이터를 PPT 텍스트 박스로 변환
            # (여기서는 AI가 준 텍스트 데이터를 파싱하여 slide.shapes.add_textbox로 배치하는 로직이 작동합니다)
            # 예시용 고정 코드:
            left = Inches(1)
            top = Inches(2)
            txBox = slide.shapes.add_textbox(left, top, Inches(8), Inches(1))
            txBox.text_frame.text = response.text # AI가 추출한 전체 텍스트 삽입

        # 5. 파일 다운로드 준비
        ppt_out = io.BytesIO()
        prs.save(ppt_out)
        ppt_out.seek(0)

        st.success("✅ 모든 이미지 분석 완료!")
        st.download_button("완성된 PPT 다운로드", data=ppt_out, file_name="converted_presentation.pptx")
else:
    st.info("왼쪽 사이드바에 Gemini API Key를 입력하면 시작할 수 있습니다.")
