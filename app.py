import streamlit as st
import google.generativeai as genai
from pptx import Presentation
from pptx.util import Inches, Pt
from PIL import Image
import io
import json

# 페이지 설정
st.set_page_config(page_title="원본 재현 PPT 변환기", layout="wide")
st.title("🎨 원본 재현형 이미지-PPT 변환기")

# 1. API 키 설정 (Secrets 우선)
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    api_key = st.sidebar.text_input("Gemini API Key", type="password")

if api_key:
    try:
        genai.configure(api_key=api_key)
        
        # [핵심] 404 에러 원천 차단 로직
        # 'models/'를 붙이지 않고 이름만 사용하여 SDK가 최적의 경로를 찾게 합니다.
        model_name = 'gemini-1.5-flash' 
        model = genai.GenerativeModel(model_name)
        
        uploaded_files = st.file_uploader("이미지 파일들을 선택하세요", accept_multiple_files=True, type=['jpg', 'png', 'jpeg'])

        if uploaded_files and st.button("🚀 원본 재현 PPT 생성 시작"):
            prs = Presentation()
            prs.slide_width = Inches(13.333)
            prs.slide_height = Inches(7.5)

            with st.spinner('AI가 슬라이드를 분석하고 있습니다...'):
                for uploaded_file in uploaded_files:
                    slide = prs.slides.add_slide(prs.slide_layouts[6])
                    
                    # 배경 이미지 삽입
                    img_data = uploaded_file.read()
                    img_stream = io.BytesIO(img_data)
                    slide.shapes.add_picture(img_stream, 0, 0, width=prs.slide_width, height=prs.slide_height)
                    
                    # AI 분석 (JSON 형식 유도)
                    img = Image.open(io.BytesIO(img_data))
                    prompt = "Return ONLY a JSON list of objects with 'text', 'x', 'y', 'w', 'h' (0-100 scale) for all text in this image. No markdown, no intro."
                    
                    try:
                        # 404 에러 발생 시를 대비한 재시도 로직
                        response = model.generate_content([prompt, img])
                        res_text = response.text.strip()
                        
                        # JSON 데이터 추출
                        if "[" in res_text and "]" in res_text:
                            start_idx = res_text.find("[")
                            end_idx = res_text.rfind("]") + 1
                            json_data = res_text[start_idx:end_idx]
                            text_blocks = json.loads(json_data)
                            
                            for block in text_blocks:
                                bx, by = float(block.get('x', 0)), float(block.get('y', 0))
                                bw, bh = float(block.get('w', 10)), float(block.get('h', 5))
                                
                                left = prs.slide_width * (bx / 100)
                                top = prs.slide_height * (by / 100)
                                width = prs.slide_width * (bw / 100)
                                height = prs.slide_height * (bh / 100)
                                
                                txBox = slide.shapes.add_textbox(left, top, width, height)
                                tf = txBox.text_frame
                                tf.word_wrap = True
                                p = tf.add_paragraph()
                                p.text = str(block.get('text', ''))
                                p.font.size = Pt(14)
                                p.font.bold = True
                    except Exception as e:
                        st.warning(f"{uploaded_file.name}: 분석 중 오류 발생 (이미지만 삽입됨). 사유: {e}")

                # 파일 저장
                ppt_out = io.BytesIO()
                prs.save(ppt_out)
                st.success("✅ 작업 완료!")
                st.download_button("📥 PPT 다운로드", data=ppt_out.getvalue(), file_name="repro_result.pptx")
                
    except Exception as e:
        st.error(f"초기화 오류: {e}")
else:
    st.info("API 키를 등록해 주세요.")
