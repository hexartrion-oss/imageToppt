import streamlit as st
import google.generativeai as genai
from pptx import Presentation
from pptx.util import Inches
from PIL import Image
import io

st.set_page_config(page_title="이미지 PPT 변환기")
st.title("🖼️ 범용 이미지-PPT 변환기")

# 1. Secrets에서 API 키 가져오기
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    api_key = st.sidebar.text_input("Gemini API Key를 입력하세요", type="password")

if api_key:
    try:
        genai.configure(api_key=api_key)
        
        # [수정] 가장 안정적인 모델 명칭 사용
        # 만약 gemini-1.5-flash가 안되면 gemini-1.5-pro로 자동 시도하도록 설정 가능
        model = genai.GenerativeModel('gemini-1.5-flash')

        uploaded_files = st.file_uploader("이미지 파일들을 선택하세요", accept_multiple_files=True, type=['jpg', 'png', 'jpeg'])

        if uploaded_files and st.button("PPT 생성 시작"):
            prs = Presentation()
            with st.spinner('AI가 이미지를 분석하여 PPT를 만들고 있습니다...'):
                for uploaded_file in uploaded_files:
                    slide = prs.slides.add_slide(prs.slide_layouts[6])
                    img = Image.open(uploaded_file)
                    
                    # AI 분석 요청 (프롬프트를 영어로 보내면 인식률이 더 올라갑/니다)
                    try:
                        response = model.generate_content([
                            "Extract all text from this image and provide it as plain text.", 
                            img
                        ])
                        
                        # 슬라이드에 텍스트 박스 추가
                        txBox = slide.shapes.add_textbox(Inches(0.5), Inches(0.5), Inches(9), Inches(6))
                        tf = txBox.text_frame
                        tf.word_wrap = True
                        tf.text = response.text if response.text else "추출된 텍스트가 없습니다."
                    
                    except Exception as e:
                        st.error(f"이미지 분석 중 오류 발생 ({uploaded_file.name}): {e}")
                        continue
                
                # 결과물 다운로드 버튼
                ppt_out = io.BytesIO()
                prs.save(ppt_out)
                st.success("✅ 모든 파일 변환 완료!")
                st.download_button("📥 완성된 PPT 다운로드", data=ppt_out.getvalue(), file_name="converted_result.pptx")
                
    except Exception as e:
        st.error(f"모델 초기화 오류: {e}")
else:
    st.warning("API 키가 설정되지 않았습니다. Streamlit Settings > Secrets에 GEMINI_API_KEY를 등록해주세요.")
