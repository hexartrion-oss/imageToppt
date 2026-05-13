import streamlit as st
from google import genai
from pptx import Presentation
from pptx.util import Inches, Pt
from PIL import Image
import io
import json

st.set_page_config(page_title="완벽 재현 PPT 변환기", layout="wide")
st.title("🎯 원본 완벽 재현 이미지-PPT 변환기")

# 1. API 키 설정
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    api_key = st.sidebar.text_input("Gemini API Key", type="password")

if api_key:
    # 최신 SDK 클라이언트 (Gemini 2.0 지원)
    client = genai.Client(api_key=api_key)

    uploaded_files = st.file_uploader("변환할 슬라이드 이미지를 선택하세요", accept_multiple_files=True, type=['jpg', 'png', 'jpeg'])

    if uploaded_files and st.button("🚀 분석 및 PPT 생성 시작"):
        prs = Presentation()
        prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5) # 16:9 표준

        for uploaded_file in uploaded_files:
            slide = prs.slides.add_slide(prs.slide_layouts[6])
            img_bytes = uploaded_file.read()
            
            # 배경 이미지 깔기
            slide.shapes.add_picture(io.BytesIO(img_bytes), 0, 0, width=prs.slide_width, height=prs.slide_height)
            
            with st.spinner(f'{uploaded_file.name} 분석 중...'):
                try:
                    # 텍스트 추출 및 좌표 확보를 위한 정교한 프롬프트
                    prompt = """
                    Task: OCR and Layout Analysis.
                    Analyze the image and find ALL text elements.
                    For each text element, provide the content and its exact bounding box coordinates (x, y, width, height) as percentages (0-100) of the image.
                    Return ONLY a JSON array like this:
                    [{"text": "Headline", "x": 10.5, "y": 20.0, "w": 40.0, "h": 5.0}, ...]
                    Ensure the 'text' is exactly what is written in the image.
                    """
                    
                    # Gemini 2.0 Flash 모델로 정밀 분석
                    response = client.models.generate_content(
                        model="gemini-2.0-flash",
                        contents=[prompt, Image.open(io.BytesIO(img_bytes))]
                    )
                    
                    # JSON 파싱 루틴
                    res_text = response.text
                    start = res_text.find("[")
                    end = res_text.rfind("]") + 1
                    
                    if start != -1 and end != 0:
                        text_blocks = json.loads(res_text[start:end])
                        
                        for block in text_blocks:
                            # 좌표 계산 및 텍스트 박스 생성
                            l = prs.slide_width * (float(block['x']) / 100)
                            t = prs.slide_height * (float(block['y']) / 100)
                            w = prs.slide_width * (float(block['w']) / 100)
                            h = prs.slide_height * (float(block['h']) / 100)
                            
                            txBox = slide.shapes.add_textbox(l, t, w, h)
                            tf = txBox.text_frame
                            tf.word_wrap = True
                            p = tf.add_paragraph()
                            p.text = str(block['text'])
                            p.font.size = Pt(16)
                            p.font.bold = True
                    else:
                        st.warning(f"{uploaded_file.name}: 텍스트를 감지하지 못했습니다.")
                
                except Exception as e:
                    st.error(f"오류 발생 ({uploaded_file.name}): {e}")

        # 다운로드 제공
        output = io.BytesIO()
        prs.save(output)
        st.success("✅ 변환 완료!")
        st.download_button("📥 PPT 파일 다운로드", output.getvalue(), "reproduced_slides.pptx")
else:
    st.info("API 키를 등록해 주세요.")
