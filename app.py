import streamlit as st
from google import genai
from pptx import Presentation
from pptx.util import Inches, Pt
from PIL import Image
import io
import json
import time

st.set_page_config(page_title="이미지-PPT 변환기 (2.0 전용)", layout="wide")
st.title("🎯 Gemini 2.0 Flash 쿼터 최적화 변환기")

# 1. API 키 설정
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    api_key = st.sidebar.text_input("Gemini API Key", type="password")

if api_key:
    # 최신 SDK 클라이언트 설정
    client = genai.Client(api_key=api_key)

    uploaded_files = st.file_uploader("이미지를 선택하세요", accept_multiple_files=True, type=['jpg', 'png', 'jpeg'])

    if uploaded_files and st.button("🚀 PPT 생성 시작"):
        prs = Presentation()
        prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
        
        progress_bar = st.progress(0)
        
        for idx, uploaded_file in enumerate(uploaded_files):
            slide = prs.slides.add_slide(prs.slide_layouts[6])
            img_bytes = uploaded_file.read()
            
            # 배경 이미지는 즉시 삽입
            slide.shapes.add_picture(io.BytesIO(img_bytes), 0, 0, width=prs.slide_width, height=prs.slide_height)
            
            with st.spinner(f'{uploaded_file.name} 분석 중...'):
                max_retries = 5  
                retry_delay = 15 
                
                for attempt in range(max_retries):
                    try:
                        prompt = "Extract text and return as JSON array: [{'text': '...', 'x': 10, 'y': 20, 'w': 30, 'h': 5}]. Scale 0-100. Raw JSON only."
                        
                        response = client.models.generate_content(
                            model="gemini-2.0-flash", 
                            contents=[prompt, Image.open(io.BytesIO(img_bytes))]
                        )
                        
                        res_text = response.text
                        start = res_text.find("[")
                        end = res_text.rfind("]") + 1
                        
                        if start != -1 and end != 0:
                            text_blocks = json.loads(res_text[start:end])
                            for block in text_blocks:
                                l = prs.slide_width * (float(block.get('x', 0)) / 100)
                                t = prs.slide_height * (float(block.get('y', 0)) / 100)
                                w = prs.slide_width * (float(block.get('w', 10)) / 100)
                                h = prs.slide_height * (float(block.get('h', 5)) / 100)
                                
                                txBox = slide.shapes.add_textbox(l, t, w, h)
                                tf = txBox.text_frame
                                tf.word_wrap = True
                                p = tf.add_paragraph()
                                p.text = str(block.get('text', ''))
                                p.font.size = Pt(14)
                                p.font.bold = True
                            break 
                            
                    except Exception as e:
                        error_msg = str(e).upper()
                        # 429 에러 또는 할당량 부족 문구 확인
                        if "429" in error_msg or "QUOTA" in error_msg or "EXHAUSTED" in error_msg:
                            if attempt < max_retries - 1:
                                wait_time = retry_delay * (attempt + 1)
                                st.warning(f"⚠️ 사용량 제한! {wait_time}초 후 다시 시도합니다... ({attempt+1}/{max_retries})")
                                time.sleep(wait_time)
                            else:
                                st.error(f"❌ {uploaded_file.name}: 할당량 부족으로 분석 실패.")
                        else:
                            st.error(f"❌ 오류: {e}")
                            break
            
            progress_bar.progress((idx + 1) / len(uploaded_files))

        output = io.BytesIO()
        prs.save(output)
        st.success("✅ 처리가 완료되었습니다!")
        st.download_button("📥 PPT 다운로드", output.getvalue(), "result.pptx")
else:
    st.info("API 키를 등록해 주세요.")
