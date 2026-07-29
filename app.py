import streamlit as st
import google.generativeai as genai
from PIL import Image

# 페이지 설정
st.set_page_config(page_title="코딩 비서 봇", page_icon="💻")
st.title("💻 나만의 AI 코딩 비서")
st.write("질문을 입력하거나 에러가 난 코드 파일을 첨부해 보세요!")

# 1. API 키 설정 (스트림릿 Secrets에서 안전하게 가져옴)
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=GEMINI_API_KEY)
    # 모델명 설정 (사용하시는 모델명으로 지정)
    model = genai.GenerativeModel('gemini-2.5-flash') # 필요시 모델명 수정 가능
except Exception as e:
    st.error(f"API 키 설정 오류: {e}. Streamlit Secrets에 'GEMINI_API_KEY'가 올바르게 등록되었는지 확인하세요.")
    st.stop()

# 파일 첨부 창
uploaded_file = st.file_uploader("파일 첨부 (이미지, 파이썬 코드, 텍스트 등)", type=['png', 'jpg', 'txt', 'py', 'json', 'csv'])

# 대화 기록 세션 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []

# 이전 대화 출력
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 채팅 입력 및 처리
if prompt := st.chat_input("어떤 코드를 짜드릴까요?"):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    input_data = [prompt]
    
    if uploaded_file is not None:
        if uploaded_file.name.lower().endswith(('png', 'jpg', 'jpeg')):
            image = Image.open(uploaded_file)
            input_data.append(image)
        else:
            string_data = uploaded_file.getvalue().decode("utf-8")
            file_text = f"\n\n[첨부파일 '{uploaded_file.name}' 내용]\n{string_data}"
            input_data.append(file_text)

    with st.chat_message("assistant"):
        with st.spinner("코드를 작성하고 있습니다... ⏳"):
            try:
                response = model.generate_content(input_data)
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"응답 생성 중 오류가 발생했습니다: {e}")
