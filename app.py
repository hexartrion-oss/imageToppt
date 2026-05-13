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

# 1. API 키 설정
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

        with st.spinner('이미지 분석 및 PPT 레이어 작업 중...'):
            for uploaded_file in uploaded_files:
                slide = prs.slides.add_slide(prs.slide_layouts[6])
                
                # 2. 배경 이미지 삽입
                img_data = uploaded_file.read()
                img_stream = io.BytesIO(img_data)
                slide.shapes.add_picture(img_stream, 0, 0, width=prs.slide_width, height=prs.slide_height)
                
                # 3. AI에게 데이터 요청 (매우 단순한 형식으로 유도)
                img = Image.open(io.BytesIO(img_data))
                prompt = "Analyze this slide image. Extract all text with coordinates (x, y, w, h as 0-100 percentages). Return ONLY a JSON list like this: [{'text': 'content', 'x': 10, 'y': 20, 'w': 30, 'h': 5}]. No explanation, no markdown tags."
                
                try:
                    response = model.generate_content([prompt, img])
                    # [핵심 수정] 정규표현식 대신 안전한 문자열 처리 사용
                    res_text = response.text.strip()
                    
                    # 마크다운 태그(```json 등)가 있으면 앞뒤를 잘라냄
                    if "[" in res_text and "]" in res_text:
                        start_idx = res_text.find("[")
                        end_idx = res_text.rfind("]") + 1
                        json_data = res_text[start_idx:end_idx]
                        
                        text_blocks = json.loads(json_data)
                        
                        # 4. 텍스트 박스 배치
                        for block in text_blocks:
                            bx = float(block.get('x', 0))
                            by = float(block.get('y', 0))
                            bw = float(block.get('w', 10))
                            bh = float(block.get('h', 5))
                            
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
                    st.warning(f"{uploaded_file.name}: 텍스트 레이어 생성 실패 (이미지만 삽입). 사유: {e}")

            # 5. 결과물 저장
            ppt_out = io.BytesIO()
            prs.save(ppt_out)
            st.success("✅ PPT 생성 성공!")
            st.download_button("📥 완성된 PPT 다운로드", data=ppt_out.getvalue(), file_name="ai_result.pptx")
else:
    st.info("API 키를 등록해 주세요.")
