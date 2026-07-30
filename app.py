import streamlit as st
import google.generativeai as genai
from openai import OpenAI
from PIL import Image

# 페이지 설정
st.set_page_config(page_title="100% 무료 전문 코딩 AI 워크벤치", page_icon="💻", layout="wide")

# ==========================================
# 1. API 키 설정 및 예비 모델 준비
# ==========================================
try:
    # 1) Google Gemini 
    gemini_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=gemini_key)
    
    # 메인 모델과 한도 초과 시 대신할 예비 모델을 준비합니다.
    # (안정성을 위해 공식 지원되는 1.5-flash와 1.5-flash-8b를 사용합니다)
    model_primary = genai.GenerativeModel('gemini-1.5-flash')
    model_fallback = genai.GenerativeModel('gemini-1.5-flash-8b') 
    
    # 2) Groq API (100% 무료 Llama 3.3 70B)
    groq_key = st.secrets["GROQ_API_KEY"]
    groq_client = OpenAI(
        api_key=groq_key,
        base_url="https://api.groq.com/openai/v1"
    )
except Exception as e:
    st.error(f"API 키 설정 오류: {e}. Streamlit Secrets 설정을 확인하세요.")
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
            "Gemini Flash (자동 전환 탑재)", 
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
st.title(f"💻 자동 전환 탑재 AI 워크벤치 [{current_title}]")
st.markdown("Gemini 한도 초과 시 **자동으로 예비 모델로 전환**되는 무중단 시스템입니다.")

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
        "인사말이나 불필요한 사설은 최대한 배제하고, 즉시 실행 가능한 깨끗한 코드와 핵심 기술적 설명 위주로 답변해.\n\n"
        f"[사용자 요청 및 컨텍스트]\n{prompt}{file_text}"
    )

    # ---------------------------------------------------------
    # 공통 Gemini 실행 함수 (한도 초과 시 예비 모델 자동 전환 로직)
    # ---------------------------------------------------------
    def run_gemini_with_fallback(inputs):
        try:
            # 1차 시도: 메인 모델 (분당 5~15회)
            res = model_primary.generate_content(inputs)
            return res.text, "Gemini Flash (Main)"
        except Exception as e:
            error_str = str(e).lower()
            if "429" in error_str or "quota" in error_str or "exceeded" in error_str:
                # 메인 모델 뻗음 -> 사용자에게 살짝 알리고 예비 모델로 2차 시도
                st.warning("⚠️ 메인 Gemini 한도(분당 5회) 도달! 자동으로 예비 Gemini(8B)로 전환하여 답변을 가져옵니다 🔄")
                try:
                    res_fallback = model_fallback.generate_content(inputs)
                    return res_fallback.text, "Gemini Flash (Fallback-8B)"
                except Exception as fallback_e:
                    raise Exception(f"예비 모델도 한도를 초과했습니다. 물 한잔 드시고 20초 뒤에 다시 시도해주세요! 😅 ({fallback_e})")
            else:
                # Quota 에러가 아닌 진짜 에러인 경우
                raise e

    # ==========================================
    # 5. 무료 AI 처리 로직
    # ==========================================
    input_data = [coding_system_rule]
    if image_data: input_data.append(image_data)

    if ai_mode == "Gemini Flash (자동 전환 탑재)":
        with st.chat_message("assistant"):
            with st.spinner("Gemini Flash 분석 중... ⚡"):
                try:
                    res_text, used_model = run_gemini_with_fallback(input_data)
                    st.markdown(f"### ⚡ {used_model} 솔루션")
                    st.markdown(res_text)
                    current_messages.append({"role": "assistant", "content": f"**[{used_model}]**\n\n{res_text}"})
                except Exception as e:
                    st.error(str(e))

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
        col1, col2 = st.columns(2)
        
        res_gemini_text = "Gemini 분석 실패"
        used_model_name = "Gemini"
        res_groq = "Groq 분석 실패"

        with col1:
            with st.chat_message("assistant"):
                with st.spinner("Gemini 분석..."):
                    try:
                        res_gemini_text, used_model_name = run_gemini_with_fallback(input_data)
                        st.markdown(f"### ⚡ {used_model_name}")
                        st.markdown(res_gemini_text)
                    except Exception as e:
                        res_gemini_text = str(e)
                        st.error(res_gemini_text)

        with col2:
            with st.chat_message("assistant"):
                with st.spinner("Groq 분석..."):
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

        combined_answer = f"**[{used_model_name}]**\n\n{res_gemini_text}\n\n---\n\n**[Groq Llama 3.3]**\n\n{res_groq}"
        current_messages.append({"role": "assistant", "content": combined_answer})
