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
# 2. 사이드바 구성 (개발 필수 기능 및 빠른 프롬프트)
# ==========================================
with st.sidebar:
    st.header("🛠️ 코딩 도우미 숏컷")
    st.write("개발할 때 자주 쓰는 요청을 클릭해 보세요!")
    
    # 1. 코드 리뷰 및 최적화
    if st.button("🔍 코드 리뷰 및 최적화 요청"):
        st.session_state.pre_prompt = "첨부하거나 입력한 코드를 검토하고, 성능을 최적화하거나 개선할 부분이 있다면 수정된 코드와 함께 설명해 줘."
        
    # 2. 에러 로그 분석
    if st.button("🐛 에러 로그/버그 분석"):
        st.session_state.pre_prompt = "아래 에러 메시지나 코드를 분석해서, 어떤 이유 때문에 에러가 났고 어떻게 고치면 되는지 정확한 해결책을 알려줘."

    # 3. 주석 및 문서화 생성
    if st.button("📝 상세한 주석 달기"):
        st.session_state.pre_prompt = "제공된 코드에 다른 사람이 봐도 한눈에 이해할 수 있도록 친절하고 상세한 주석을 추가해서 완성된 코드를 짜줘."

    # 4. 다른 언어로 변환 (예: 파이썬 <-> 자바스크립트 등)
    if st.button("🔄 다른 언어로 코드 변환"):
        st.session_state.pre_prompt = "이 코드를 다른 주요 프로그래밍 언어로 변환해 줘. (어떤 언어로 바꿀지 물어봐 줘)"

    st.divider()
    st.markdown("💡 **Tip:** 에러 화면을 캡처해서 올리거나, 코드 파일을 업로드한 상태에서 위 버튼을 누르면 훨씬 정확한 답변을 얻을 수 있습니다!")

# ==========================================
# 3. 메인 웹 화면 디자인
# ==========================================
st.title("💻 나만의 AI 코딩 비서")
st.write("코드를 입력하거나, 에러 캡처 화면 및 코드 파일을 첨부해 보세요!")

# 파일 첨부 창 (코드 파일, 이미지 등)
uploaded_file = st.file_uploader("파일 첨부 (이미지, 파이썬 코드, 텍스트 등)", type=['png', 'jpg', 'txt', 'py', 'json', 'csv', 'js', 'html', 'css'])

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
        with st.spinner("코드를 분석하고 작성하고 있습니다... ⏳"):
            try:
                response = model.generate_content(input_data)
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"응답 생성 중 오류가 발생했습니다: {e}")
