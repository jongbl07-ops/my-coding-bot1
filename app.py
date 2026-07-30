import streamlit as st
import google.generativeai as genai
from openai import OpenAI
from PIL import Image

# 페이지 설정
st.set_page_config(page_title="100% 무료 전문 코딩 AI 워크벤치", page_icon="💻", layout="wide")

# ==========================================
# 1. API 키 설정 (Google Gemini + Groq 무료 API)
# ==========================================
try:
    # 1) Google Gemini (Flash 3.5 / 1.5)
    gemini_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=gemini_key)
    model_flash = genai.GenerativeModel('gemini-3.5-flash')
    
    # 2) Groq API (100% 무료 Llama 3.3 70B / OpenAI 호환 SDK)
    groq_key = st.secrets["GROQ_API_KEY"]
    groq_client = OpenAI(
        api_key=groq_key,
        base_url="https://api.groq.com/openai/v1"
    )
except Exception as e:
    st.error(f"API 키 설정 오류: {e}. Streamlit Secrets에 'GEMINI_API_KEY'와 'GROQ_API_KEY'를 등록하세요.")
    st.stop()

# ==========================================
# 2. 세션 상태 초기화
# ==========================================
if "chat_sessions" not in st.session_state:
    st.session_state.chat_sessions = [{"title": "새로운 코딩 작업", "messages": []}]

if "current_session_idx" not in st.session_state:
    st.session_state.current_session_idx = 0

current_messages = st.session_state.chat_sessions[st.session_state.current_session_idx]["messages"]

# ==========================================
# 3. 사이드바 (무료 AI 선택)
# ==========================================
with st.sidebar:
    st.header("💻 코딩 작업실 설정")
    ai_mode = st.radio(
        "사용할 무료 AI 엔진:",
        [
            "Gemini Flash (초고속)", 
            "Groq Llama 3.3 70B (무료 고성능)",
            "🔥 두 모델 동시 비교"
        ],
        index=2
    )

    st.divider()
    
    st.subheader("🛠️ 개발자 퀵 숏컷")
    
    def get_effective_context():
        if not current_messages:
            return ""
        for msg in reversed(current_messages):
            content = msg["content"]
            if "분석할 대상 소스 코드" in content or "코딩 전용 AI 비서입니다" in content:
                continue
            return f"\n\n[참고할 이전 코드/내용]\n{content}"
        return ""

    if st.button("🐛 버그 및 에러 원인 분석"):
        context = get_effective_context()
        st.session_state.pre_prompt = f"아래 코드나 에러를 분석해서, 원인이 무엇이고 어떻게 수정해야 하는지 정확한 수정 코드와 함께 설명해 줘.{context}"

    if st.button("⚡ 코드 성능 최적화 (Refactoring)"):
        context = get_effective_context()
        st.session_state.pre_prompt = f"아래 코드의 성능을 높이고 가독성을 좋게 리팩토링해 줘.{context}"

    if st.button("🧪 단위 테스트 코드 생성"):
        context = get_effective_context()
        st.session_state.pre_prompt = f"아래 코드나 내용을 검증할 수 있는 단위 테스트(Unit Test) 코드와 실행 방법을 작성해 줘.{context}"

    st.divider()
    
    col_new, col_clear = st.columns(2)
    if col_new.button("➕ 새 작업"):
        new_session = {"title": f"작업 {len(st.session_state.chat_sessions) + 1}", "messages": []}
        st.session_state.chat_sessions.append(new_session)
        st.session_state.current_session_idx = len(st.session_state.chat_sessions) - 1
        st.rerun()

    if col_clear.button("🧹 화면 지우기"):
        st.session_state.chat_sessions[st.session_state.current_session_idx]["messages"] = []
        st.session_state.chat_sessions[st.session_state.current_session_idx]["title"] = "새로운 코딩 작업"
        st.rerun()

# ==========================================
# 4. 메인 화면 (개발 환경 인터페이스)
# ==========================================
current_title = st.session_state.chat_sessions[st.session_state.current_session_idx]["title"]
st.title(f"💻 100% 무료 AI 코딩 워크벤치 [{current_title}]")
st.markdown("과금 걱정 없는 **Gemini Flash**와 **Groq Llama 3.3 (70B)** 조합입니다.")

uploaded_file = st.file_uploader(
    "📂 소스 코드 또는 에러 캡처 업로드 (.py, .js, .txt, .png 등)", 
    type=['png', 'jpg', 'jpeg', 'txt', 'py', 'json', 'csv', 'js', 'html', 'css', 'sql'],
    key=f"file_uploader_{st.session_state.current_session_idx}"
)

for msg in current_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

default_input = st.session_state.pop("pre_prompt", "")

if prompt := st.chat_input("구현할 코드나 해결할 에러 내용을 입력하세요.", key=f"user_input_{st.session_state.current_session_idx}"):
    pass
elif default_input:
    prompt = default_input

if prompt:
    if len(current_messages) == 0:
        st.session_state.chat_sessions[st.session_state.current_session_idx]["title"] = prompt[:15] + "..."

    with st.chat_message("user"):
        st.markdown(prompt)
    current_messages.append({"role": "user", "content": prompt})

    file_text = ""
    image_data = None
    if uploaded_file is not None:
        if uploaded_file.name.lower().endswith(('png', 'jpg', 'jpeg')):
            image_data = Image.open(uploaded_file)
        else:
            string_data = uploaded_file.getvalue().decode("utf-8")
            file_text = f"\n\n[첨부된 소스코드/파일 '{uploaded_file.name}' 내용]\n```\n{string_data}\n```"

    coding_system_rule = (
        "너는 세계 최고 수준의 시니어 소프트웨어 엔지니어이자 프로그래밍 전문 AI야. "
        "사용자의 질문은 **오직 프로그래밍, 소스 코드 작성, 버그 디버깅, 단위 테스트 작성**과 관련된 내용뿐이야. "
        "인사말이나 불필요한 사설은 최대한 배제하고, 즉시 실행 가능한 깨끗한 코드와 핵심 기술적 설명 위주로 답변해. "
        "만약 참고할 코드가 없다면 '검증할 소스코드가 제공되지 않았습니다.'라고 안내해 줘.\n\n"
        f"[사용자 요청 및 컨텍스트]\n{prompt}{file_text}"
    )

    # ==========================================
    # 5. 무료 AI 처리 로직 (Gemini Flash + Groq)
    # ==========================================
    if ai_mode == "Gemini Flash (초고속)":
        with st.chat_message("assistant"):
            with st.spinner("Gemini Flash 분석 중... ⚡"):
                try:
                    input_data = [coding_system_rule]
                    if image_data: input_data.append(image_data)
                    response = model_flash.generate_content(input_data)
                    st.markdown("### ⚡ Gemini Flash 솔루션")
                    st.markdown(response.text)
                    current_messages.append({"role": "assistant", "content": f"**[Gemini Flash]**\n\n{response.text}"})
                except Exception as e:
                    st.error(f"Gemini 오류 발생: {e}")

    elif ai_mode == "Groq Llama 3.3 70B (무료 고성능)":
        with st.chat_message("assistant"):
            with st.spinner("Groq Llama 3.3 분석 중... 🚀"):
                try:
                    groq_response = groq_client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "user", "content": coding_system_rule}]
                    )
                    answer = groq_response.choices[0].message.content
                    st.markdown("### 🚀 Groq Llama 3.3 솔루션")
                    st.markdown(answer)
                    current_messages.append({"role": "assistant", "content": f"**[Groq Llama 3.3]**\n\n{answer}"})
                except Exception as e:
                    st.error(f"Groq 오류 발생: {e}")

    else:
        # 두 모델 동시 비교 모드
        col1, col2 = st.columns(2)
        
        res_flash = "Gemini 분석 실패"
        res_groq = "Groq 분석 실패"

        with col1:
            with st.chat_message("assistant"):
                with st.spinner("Gemini Flash 분석..."):
                    try:
                        input_data = [coding_system_rule]
                        if image_data: input_data.append(image_data)
                        res_flash = model_flash.generate_content(input_data).text
                        st.markdown("### ⚡ Gemini Flash")
                        st.markdown(res_flash)
                    except Exception as e:
                        res_flash = f"Gemini 오류: {e}"
                        st.error(res_flash)

        with col2:
            with st.chat_message("assistant"):
                with st.spinner("Groq Llama 3.3 분석..."):
                    try:
                        groq_response = groq_client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=[{"role": "user", "content": coding_system_rule}]
                        )
                        res_groq = groq_response.choices[0].message.content
                        st.markdown("### 🚀 Groq Llama 3.3")
                        st.markdown(res_groq)
                    except Exception as e:
                        res_groq = f"Groq 오류: {e}"
                        st.error(res_groq)

        combined_answer = f"**[Gemini Flash]**\n\n{res_flash}\n\n---\n\n**[Groq Llama 3.3]**\n\n{res_groq}"
        current_messages.append({"role": "assistant", "content": combined_answer})
