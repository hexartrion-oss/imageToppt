import streamlit as st
import google.generativeai as genai
from pptx import Presentation
from pptx.util import Inches, Pt
from PIL import Image
import io

# 페이지 설정
st.set_page_config(page_title="범용 이미지-PPT 변환기", layout="centered")
st.title("🖼️ 범용 이미지-PPT 변환기")
st.write("이미지를 업로드하면 AI가 텍스트를 추출하여 PPT로 만들어 드립니다.")

# 1. API 키 설정 (Secrets 우선)
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    api_key = st.sidebar.text_input("Gemini API Key를 입력하세요", type="password")

if api_key:
    try:
        genai.configure(api_key=api_key)
        
        # [핵심] 404 에러 방지용 모델 로드 로직
        # 사용 가능한 모델 리스트를 확인하여 가장 적합한 것을 선택합니다.
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # 우선순위에 따른 모델 선택
        target_model = 'models/gemini-1.5-flash'
        if target_model not in available_models:
            # 경로 접두사 없는 버전 확인
            if 'gemini-1.5-flash' in str(available_models):
                target_model = 'gemini-1.5-flash'
            else:
                # 최후의 수단으로 첫 번째 사용 가능한 모델 선택
                target_model = available_models[0]
        
        model = genai.GenerativeModel(target_model)
        st.sidebar.success(f"사용 중인 모델: {target_model}")

        # 2. 파일 업로드
        uploaded_files = st.file_uploader("이미지 파일들을 선택하세요 (JPG, PNG)", accept_multiple_files=True, type=['jpg', 'png', 'jpeg'])

        if uploaded_files and st.button("🚀 PPT 생성 시작"):
            prs = Presentation()
            
            # 슬라이드 크기를 일반적인 16:9 비율로 설정 (선택 사항)
            prs.slide_width = Inches(13.333)
            prs.slide_height = Inches(7.5)

            with st.spinner('AI가 이미지를 분석 중입니다...'):
                for uploaded_file in uploaded_files:
                    # 슬라이드 추가 (빈 레이아웃)
                    slide = prs.slides.add_slide(prs.slide_layouts[6])
                    img = Image.open(uploaded_file)
                    
                    try:
                        # AI에게 텍스트 추출 요청
                        response = model.generate_content([
                            "Extract all text from this image accurately. Keep the structure if possible.", 
                            img
                        ])
                        
                        # 텍스트 박스 추가 (슬라이드 중앙 부근 배치)
                        left = Inches(1)
                        top = Inches(1)
                        width = Inches(11)
                        height = Inches(5.5)
                        
                        txBox = slide.shapes.add_textbox(left, top, width, height)
                        tf = txBox.text_frame
                        tf.word_wrap = True
                        
                        # 결과 텍스트 삽입
                        p = tf.add_paragraph()
                        p.text = response.text if response.text else "텍스트를 추출하지 못했습니다."
                        p.font.size = Pt(18)
                        
                    except Exception as e:
                        st.error(f"이미지 분석 실패 ({uploaded_file.name}): {e}")
                
                # 3. PPT 파일 생성 및 다운로드
                ppt_out = io.BytesIO()
                prs.save(ppt_out)
                st.success("✅ 모든 슬라이드 변환이 완료되었습니다!")
                st.download_button(
                    label="📥 완성된 PPT 다운로드",
                    data=ppt_out.getvalue(),
                    file_name="AI_Generated_Presentation.pptx",
                    mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
                )
                
    except Exception as e:
        st.error(f"초기화 오류: {e}")
        st.info("API 키가 올바른지, 혹은 프로젝트에서 Generative Language API가 활성화되었는지 확인하세요.")
else:
    st.warning("👈 왼쪽 사이드바에 API 키를 입력하거나 Streamlit Secrets에 등록해주세요.")
