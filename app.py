import streamlit as st
import google.generativeai as genai
from PIL import Image

# 페이지 설정 (사이드바 확장 기능 포함)
st.set_page_config(page_title="나만의 AI 코딩 비서", page_icon="💻", layout="wide")

# ==========================================
# 1. API 키 설정 (스트림릿 Secrets에서 안전하게 가져옴)
# ==========================================
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')
except Exception as e:
    st.error(f"API 키 설정 오류: {e}. Streamlit Secrets에 'GEMINI_API_KEY'가 올바르게 등록되었는지 확인하세요.")
    st.stop()

# ==========================================
# 2. 사이드바 구성 (개발 숏컷 + 실무 편의 기능)
# ==========================================
with st.sidebar:
    st.header("🛠️ 코딩 도우미 숏컷")
    
    # [신규 기능 1] 대화 초기화 버튼
    if st.button("🧹 새로운 대화 시작하기 (초기화)"):
        st.session_state.messages = []
        st.rerun()

    st.divider()
    
    # [신규 기능 2] 답변 스타일 선택 옵션
    st.subheader("⚙️ 답변 스타일 설정")
    response_style = st.radio(
        "원하는 답변 형태를 선택하세요:",
        ["상세한 설명 + 코드", "핵심 코드 위주로 간결하게"],
        index=0
    )

    st.divider()
    st.subheader("💡 자주 쓰는 요청")
    if st.button("🔍 코드 리뷰 및 최적화"):
        st.session_state.pre_prompt = "첨부하거나 입력한 코드를 검토하고, 성능을 최적화하거나 개선할 부분이 있다면 수정된 코드와 함께 설명해 줘."
        
    if st.button("🐛 에러 로그/버그 분석"):
        st.session_state.pre_prompt = "아래 에러 메시지나 코드를 분석해서, 어떤 이유 때문에 에러가 났고 어떻게 고치면 되는지 정확한 해결책을 알려줘."

    if st.button("📝 상세한 주석 달기"):
        st.session_state.pre_prompt = "제공된 코드에 다른 사람이 봐도 한눈에 이해할 수 있도록 친절하고 상세한 주석을 추가해서 완성된 코드를 짜줘."

    if st.button("🔄 다른 언어로 변환"):
        st.session_state.pre_prompt = "이 코드를 다른 주요 프로그래밍 언어로 변환해 줘. (어떤 언어로 바꿀지 물어봐 줘)"

# ==========================================
# 3. 메인 웹 화면 디자인
# ==========================================
st.title("💻 나만의 AI 코딩 비서")
st.write("코드를 입력하거나, 에러 캡처 화면 및 코드 파일을 첨부해 보세요!")

# 파일 첨부 창 (이미지, 코드 파일 등)
uploaded_file = st.file_uploader(
    "파일 첨부 (에러 캡처 이미지, 파이썬 코드, 텍스트 등)", 
    type=['png', 'jpg', 'jpeg', 'txt', 'py', 'json', 'csv', 'js', 'html', 'css']
)

# 대화 기록 세션 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []

# 이전 대화 출력
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 사이드바 버튼을 눌렀을 때 전달할 텍스트 처리
default_input = st.session_state.pop("pre_prompt", "")

# 채팅 입력 및 처리
if prompt := st.chat_input("어떤 코드를 짜드릴까요?", key="user_input"):
    pass
elif default_input:
    prompt = default_input

if prompt:
    # 답변 스타일에 따른 시스템 지시사항을 프롬프트에 살짝 녹여냄
    if response_style == "핵심 코드 위주로 간결하게":
        final_prompt = f"{prompt}\n\n[요청 조건: 장황한 설명은 생략하고, 핵심 코드와 짧은 주석 위주로 아주 간결하게 답변해 줘.]"
    else:
        final_prompt = f"{prompt}\n\n[요청 조건: 초보자도 이해하기 쉽게 친절하고 상세한 설명과 함께 완성된 코드를 제공해 줘.]"

    with st.chat_message("user"):
        st.markdown(prompt) # 화면에는 사용자가 입력한 원래 텍스트만 예쁘게 보여줌
    st.session_state.messages.append({"role": "user", "content": prompt})

    # AI에게 전달할 데이터 구성
    input_data = [final_prompt]
    
    if uploaded_file is not None:
        if uploaded_file.name.lower().endswith(('png', 'jpg', 'jpeg')):
            image = Image.open(uploaded_file)
            input_data.append(image)
        else:
            string_data = uploaded_file.getvalue().decode("utf-8")
            file_text = f"\n\n[첨부파일 '{uploaded_file.name}' 내용]\n{string_data}"
            input_data.append(file_text)

    with st.chat_message("assistant"):
        with st.spinner("코드를 분석하고 작성하고 있습니다... ⏳"):
            try:
                response = model.generate_content(input_data)
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"응답 생성 중 오류가 발생했습니다: {e}")
