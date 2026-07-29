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
    model = genai.GenerativeModel('gemini-3.5-flash')
except Exception as e:
    st.error(f"API 키 설정 오류: {e}. Streamlit Secrets에 'GEMINI_API_KEY'가 올바르게 등록되었는지 확인하세요.")
    st.stop()

# ==========================================
# 2. 세션 상태 초기화 (대화 기록 관리)
# ==========================================
if "chat_sessions" not in st.session_state:
    # 여러 개의 대화방을 저장할 수 있는 리스트 (기본 방 1개 생성)
    st.session_state.chat_sessions = [{"title": "새로운 코딩 작업", "messages": []}]

if "current_session_idx" not in st.session_state:
    st.session_state.current_session_idx = 0

# 현재 선택된 대화방의 메시지 가져오기
current_messages = st.session_state.chat_sessions[st.session_state.current_session_idx]["messages"]

# ==========================================
# 3. 사이드바 구성 (이전 작업 목록 및 도우미 숏컷)
# ==========================================
with st.sidebar:
    st.header("📂 작업 히스토리")
    
    # [신규 기능] 새로운 작업(대화방) 만들기 버튼
    if st.button("➕ 새로운 작업 시작하기"):
        new_session = {"title": f"작업 {len(st.session_state.chat_sessions) + 1}", "messages": []}
        st.session_state.chat_sessions.append(new_session)
        st.session_state.current_session_idx = len(st.session_state.chat_sessions) - 1
        st.rerun()

    st.divider()
    
    # 이전 작업 목록 선택 버튼들
    st.subheader("📜 이전 작업 불러오기")
    for idx, session in enumerate(st.session_state.chat_sessions):
        # 현재 선택된 방은 다르게 표시
        btn_label = f"💬 {session['title']}"
        if idx == st.session_state.current_session_idx:
            btn_label = f"▶️ {session['title']}"
            
        if st.button(btn_label, key=f"session_btn_{idx}"):
            st.session_state.current_session_idx = idx
            st.rerun()

    st.divider()
    
    # 답변 스타일 설정
    st.subheader("⚙️ 답변 스타일 설정")
    response_style = st.radio(
        "원하는 답변 형태:",
        ["상세한 설명 + 코드", "핵심 코드 위주로 간결하게"],
        index=0
    )

    st.divider()
    st.subheader("🛠️ 코딩 도우미 숏컷")
    if st.button("🔍 코드 리뷰 및 최적화"):
        st.session_state.pre_prompt = "첨부하거나 입력한 코드를 검토하고, 성능을 최적화하거나 개선할 부분이 있다면 수정된 코드와 함께 설명해 줘."
        
    if st.button("🐛 에러 로그/버그 분석"):
        st.session_state.pre_prompt = "아래 에러 메시지나 코드를 분석해서, 어떤 이유 때문에 에러가 났고 어떻게 고치면 되는지 정확한 해결책을 알려줘."

    if st.button("📝 상세한 주석 달기"):
        st.session_state.pre_prompt = "제공된 코드에 다른 사람이 봐도 한눈에 이해할 수 있도록 친절하고 상세한 주석을 추가해서 완성된 코드를 짜줘."

# ==========================================
# 4. 메인 웹 화면 디자인
# ==========================================
current_title = st.session_state.chat_sessions[st.session_state.current_session_idx]["title"]
st.title(f"💻 AI 코딩 비서 [{current_title}]")
st.write("이전에 작업하던 내용을 불러오거나, 새로운 코딩 작업을 시작해보세요!")

# 파일 첨부 창 (이미지, 코드 파일 등)
uploaded_file = st.file_uploader(
    "파일 첨부 (에러 캡처 이미지, 파이썬 코드, 텍스트 등)", 
    type=['png', 'jpg', 'jpeg', 'txt', 'py', 'json', 'csv', 'js', 'html', 'css'],
    key=f"file_uploader_{st.session_state.current_session_idx}"
)

# 현재 선택된 대화방의 이전 대화 출력
for msg in current_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 사이드바 버튼을 눌렀을 때 전달할 텍스트 처리
default_input = st.session_state.pop("pre_prompt", "")

# 채팅 입력 및 처리
if prompt := st.chat_input("어떤 코드를 짜드릴까요?", key=f"user_input_{st.session_state.current_session_idx}"):
    pass
elif default_input:
    prompt = default_input

if prompt:
    # 답변 스타일에 따른 지시사항 반영
    if response_style == "핵심 코드 위주로 간결하게":
        final_prompt = f"{prompt}\n\n[요청 조건: 장황한 설명은 생략하고, 핵심 코드와 짧은 주석 위주로 아주 간결하게 답변해 줘.]"
    else:
        final_prompt = f"{prompt}\n\n[요청 조건: 초보자도 이해하기 쉽게 친절하고 상세한 설명과 함께 완성된 코드를 제공해 줘.]"

    # 첫 번째 질문일 경우, 대화방 이름을 질문 내용으로 자동 변경
    if len(current_messages) == 0:
        st.session_state.chat_sessions[st.session_state.current_session_idx]["title"] = prompt[:15] + "..."

    with st.chat_message("user"):
        st.markdown(prompt)
    current_messages.append({"role": "user", "content": prompt})

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
                current_messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"응답 생성 중 오류가 발생했습니다: {e}")
