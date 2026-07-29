import streamlit as st
import google.generativeai as genai
from PIL import Image

# 페이지 설정 (사이드바 확장 기능 포함)
st.set_page_config(page_title="나만의 멀티 AI 코딩 비서", page_icon="💻", layout="wide")

# ==========================================
# 1. API 키 설정 (스트림릿 Secrets에서 안전하게 가져옴)
# ==========================================
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=GEMINI_API_KEY)
except Exception as e:
    st.error(f"API 키 설정 오류: {e}. Streamlit Secrets에 'GEMINI_API_KEY'가 올바르게 등록되었는지 확인하세요.")
    st.stop()

# ==========================================
# 2. 세션 상태 초기화 (대화 기록 관리)
# ==========================================
if "chat_sessions" not in st.session_state:
    st.session_state.chat_sessions = [{"title": "새로운 코딩 작업", "messages": []}]

if "current_session_idx" not in st.session_state:
    st.session_state.current_session_idx = 0

current_messages = st.session_state.chat_sessions[st.session_state.current_session_idx]["messages"]

# ==========================================
# 3. 사이드바 구성 (모델 선택 및 작업 히스토리)
# ==========================================
with st.sidebar:
    st.header("🤖 AI 모델 선택")
    # [신규 기능] 사용할 Gemini 모델을 2개 중에서 선택
    selected_model_name = st.radio(
        "사용할 AI 모델을 고르세요:",
        ["Gemini 2.5 Flash (빠르고 가벼움)", "Gemini 2.5 Pro / 최신 (더 깊고 똑똑함)"],
        index=0
    )
    
    # 선택에 따른 실제 구글 모델 이름 매핑
    if "Flash" in selected_model_name:
        active_model_id = "gemini-2.5-flash"
    else:
        active_model_id = "gemini-2.5-pro" # 필요시 최신 프로 모델명으로 적용

    st.divider()
    
    st.header("📂 작업 히스토리")
    if st.button("➕ 새로운 작업 시작하기"):
        new_session = {"title": f"작업 {len(st.session_state.chat_sessions) + 1}", "messages": []}
        st.session_state.chat_sessions.append(new_session)
        st.session_state.current_session_idx = len(st.session_state.chat_sessions) - 1
        st.rerun()

    st.divider()
    
    st.subheader("📜 이전 작업 불러오기")
    for idx, session in enumerate(st.session_state.chat_sessions):
        btn_label = f"💬 {session['title']}"
        if idx == st.session_state.current_session_idx:
            btn_label = f"▶️ {session['title']}"
            
        if st.button(btn_label, key=f"session_btn_{idx}"):
            st.session_state.current_session_idx = idx
            st.rerun()

    st.divider()
    
    st.subheader("⚙️ 답변 스타일")
    response_style = st.radio(
        "답변 형태:",
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
st.write(f"현재 연결된 모델: **{active_model_id}** | 원하시는 모델을 사이드바에서 변경할 수 있습니다.")

# 파일 첨부 창
uploaded_file = st.file_uploader(
    "파일 첨부 (에러 캡처 이미지, 파이썬 코드, 텍스트 등)", 
    type=['png', 'jpg', 'jpeg', 'txt', 'py', 'json', 'csv', 'js', 'html', 'css'],
    key=f"file_uploader_{st.session_state.current_session_idx}"
)

# 이전 대화 출력
for msg in current_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

default_input = st.session_state.pop("pre_prompt", "")

# 채팅 입력 및 처리
if prompt := st.chat_input("어떤 코드를 짜드릴까요?", key=f"user_input_{st.session_state.current_session_idx}"):
    pass
elif default_input:
    prompt = default_input

if prompt:
    if response_style == "핵심 코드 위주로 간결하게":
        final_prompt = f"{prompt}\n\n[요청 조건: 장황한 설명은 생략하고, 핵심 코드와 짧은 주석 위주로 아주 간결하게 답변해 줘.]"
    else:
        final_prompt = f"{prompt}\n\n[요청 조건: 초보자도 이해하기 쉽게 친절하고 상세한 설명과 함께 완성된 코드를 제공해 줘.]"

    if len(current_messages) == 0:
        st.session_state.chat_sessions[st.session_state.current_session_idx]["title"] = prompt[:15] + "..."

    with st.chat_message("user"):
        st.markdown(prompt)
    current_messages.append({"role": "user", "content": prompt})

    input_data = [final_prompt]
    
    if uploaded_file is not None:
        if uploaded_file.name.lower().endswith(('png', 'jpg', 'jpeg')):
            image = Image.open(uploaded_file)
            input_data.append(image)
        else:
            string_data = uploaded_file.getvalue().decode("utf-8")
            file_text = f"\n\n[첨부파일 '{uploaded_file.name}' 내용]\n{string_data}"
            input_data.append(file_text)

    # 선택된 모델 인스턴스 생성 및 답변 요청
    with st.chat_message("assistant"):
        with st.spinner(f"[{active_model_id}] 모델이 코드를 분석하고 있습니다... ⏳"):
            try:
                # 사이드바에서 선택한 모델 ID로 동적 생성
                selected_model = genai.GenerativeModel(active_model_id)
                response = selected_model.generate_content(input_data)
                st.markdown(response.text)
                current_messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"응답 생성 중 오류가 발생했습니다: {e}")
