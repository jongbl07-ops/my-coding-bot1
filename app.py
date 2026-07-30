import streamlit as st
import google.generativeai as genai
from openai import OpenAI
from PIL import Image

# 페이지 설정
st.set_page_config(page_title="100% 무료 전문 코딩 AI 워크벤치", page_icon="💻", layout="wide")

# ==========================================
# 1. API 키 설정 및 사용 가능한 모든 모델 검색
# ==========================================
try:
    # 1) Google Gemini 
    gemini_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=gemini_key)
    
    # 세션에 사용 가능한 제미나이 모델 목록을 저장 (최초 1회만 검색)
    if "gemini_model_list" not in st.session_state:
        # generateContent를 지원하는 모든 모델의 이름을 가져옴
        raw_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # 선호하는 순서대로 정렬 (Flash -> 8B -> 기타 모델들)
        sorted_models = []
        priorities = ['gemini-1.5-flash', 'gemini-1.5-flash-8b', 'gemini-1.5-pro']
        
        for p in priorities:
            for m in raw_models:
                if p in m and m not in sorted_models:
                    sorted_models.append(m)
        
        # 선호 모델 외에 남은 나머지 모든 모델 추가 (최후의 보루)
        for m in raw_models:
            if m not in sorted_models and "vision" not in m:
                sorted_models.append(m)
                
        st.session_state.gemini_model_list = sorted_models

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
            "Gemini (무한 자동 교체)", 
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
st.title(f"💻 AI 코딩 워크벤치 [{current_title}]")
st.markdown("Gemini 한도 초과 시 **사용 가능한 다른 모델로 계속 자동 교체**하며 답변을 찾아옵니다.")

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
    # 무한 릴레이 교체 엔진 (모든 모델을 순서대로 테스트)
    # ---------------------------------------------------------
    def run_gemini_with_infinite_fallback(inputs):
        models_to_try = st.session_state.gemini_model_list
        
        for model_name in models_to_try:
            try:
                # 현재 순서의 모델로 객체 생성 및 질문
                model = genai.GenerativeModel(model_name)
                res = model.generate_content(inputs)
                
                # 성공하면 모델 이름 보기 좋게 다듬어서 리턴
                clean_name = model_name.split('/')[-1]
                return res.text, f"Gemini ({clean_name})"
                
            except Exception as e:
                error_str = str(e).lower()
                # Quota(한도 초과) 에러가 감지되면 다음 모델로 패스
                if "429" in error_str or "quota" in error_str or "exceeded" in error_str:
                    clean_name = model_name.split('/')[-1]
                    st.toast(f"⚠️ {clean_name} 한도 초과! 다음 예비 모델로 교체합니다...", icon="🔄")
                    continue
                else:
                    # 한도 초과가 아닌 코딩 질문 자체의 에러(Safety 등)면 즉시 중단
                    raise e
                    
        # 리스트에 있는 수많은 제미나이 모델이 전부 다 한도 초과일 때
        raise Exception("사용 가능한 모든 Gemini 모델의 한도가 초과되었습니다. 1분만 기다렸다가 화면을 지우고 다시 시도해 주세요! 😅")

    # ==========================================
    # 5. 메인 처리 로직
    # ==========================================
    input_data = [coding_system_rule]
    if image_data: input_data.append(image_data)

    if ai_mode == "Gemini (무한 자동 교체)":
        with st.chat_message("assistant"):
            with st.spinner("최적의 Gemini 모델을 찾아 분석 중입니다... ⚡"):
                try:
                    res_text, used_model = run_gemini_with_infinite_fallback(input_data)
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
        # 동시 비교 모드
        col1, col2 = st.columns(2)
        
        res_gemini_text = "Gemini 분석 실패"
        used_model_name = "Gemini"
        res_groq = "Groq 분석 실패"

        with col1:
            with st.chat_message("assistant"):
                with st.spinner("Gemini 분석..."):
                    try:
                        res_gemini_text, used_model_name = run_gemini_with_infinite_fallback(input_data)
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
