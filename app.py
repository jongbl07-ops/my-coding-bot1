import streamlit as st
import google.generativeai as genai
from openai import OpenAI
from PIL import Image

# 페이지 설정
st.set_page_config(page_title="100% 무료 전문 코딩 AI 워크벤치", page_icon="💻", layout="wide")

# ==========================================
# 1. API 키 설정 및 실시간 모델 목록 동적 검색
# ==========================================
try:
    # 1) Google Gemini 설정
    gemini_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=gemini_key)
    
    if "gemini_model_list" not in st.session_state:
        raw_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        priority_models = ['models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-1.5-flash-8b']
        sorted_models = [p for p in priority_models if p in raw_models]
        
        for m in raw_models:
            m_lower = m.lower()
            if m not in sorted_models and "vision" not in m_lower and "tts" not in m_lower:
                sorted_models.append(m)
        st.session_state.gemini_model_list = sorted_models

    # 2) Groq API 설정 및 실시간 모델 매칭
    groq_key = st.secrets["GROQ_API_KEY"]
    groq_client = OpenAI(
        api_key=groq_key,
        base_url="https://api.groq.com/openai/v1"
    )
    
    if "groq_models_dict" not in st.session_state:
        available_groq_models = [m.id for m in groq_client.models.list().data]
        fallback_model = available_groq_models[0] if available_groq_models else ""
        
        llama_model = next((m for m in available_groq_models if 'llama-3.3-70b' in m.lower()), 
                           next((m for m in available_groq_models if 'llama3-70b' in m.lower()), fallback_model))
        deepseek_model = next((m for m in available_groq_models if 'deepseek' in m.lower()), llama_model)
        mixtral_model = next((m for m in available_groq_models if 'mixtral' in m.lower()), fallback_model)
        
        st.session_state.groq_models_dict = {
            "llama": llama_model,
            "deepseek": deepseek_model,
            "mixtral": mixtral_model
        }

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
# 3. 사이드바 (설정 및 숏컷)
# ==========================================
with st.sidebar:
    st.header("💻 코딩 작업실 설정")
    
    st.caption(f"**Groq 실시간 연결 모델**\n- 🚀 {st.session_state.groq_models_dict['llama']}\n- 🧠 {st.session_state.groq_models_dict['deepseek']}\n- 🌪️ {st.session_state.groq_models_dict['mixtral']}")
    
    ai_mode = st.radio(
        "사용할 무료 AI 엔진 선택:",
        [
            "⚡ Gemini (무한 자동 교체)", 
            "🚀 Groq: Llama (범용 고성능)",
            "🧠 Groq: DeepSeek (코딩/추론 특화)",
            "🔥 [비교] Gemini vs Groq Llama",
            "🤝 [비교+합의] Groq DeepSeek vs Llama" # 신규 추가된 모드
        ],
        index=4
    )

    st.divider()
    st.subheader("🛠️ 개발자 퀵 숏컷")
    
    def get_effective_context():
        if not current_messages:
            return ""
        for msg in reversed(current_messages):
            if "분석할 대상 소스 코드" in msg["content"] or "코딩 전용 AI 비서입니다" in msg["content"]:
                continue
            return f"\n\n[참고할 이전 코드/내용]\n{msg['content']}"
        return ""

    if st.button("🐛 버그 및 에러 원인 분석"):
        st.session_state.pre_prompt = f"아래 코드나 에러를 분석해서, 원인이 무엇이고 어떻게 수정해야 하는지 정확한 수정 코드와 함께 설명해 줘.{get_effective_context()}"

    if st.button("⚡ 코드 성능 최적화 (Refactoring)"):
        st.session_state.pre_prompt = f"아래 코드의 성능을 높이고 가독성을 좋게 리팩토링해 줘.{get_effective_context()}"

    st.divider()
    col_new, col_clear = st.columns(2)
    if col_new.button("➕ 새 작업"):
        st.session_state.chat_sessions.append({"title": f"작업 {len(st.session_state.chat_sessions) + 1}", "messages": []})
        st.session_state.current_session_idx = len(st.session_state.chat_sessions) - 1
        st.rerun()

    if col_clear.button("🧹 화면 지우기"):
        st.session_state.chat_sessions[st.session_state.current_session_idx]["messages"] = []
        st.session_state.chat_sessions[st.session_state.current_session_idx]["title"] = "새로운 코딩 작업"
        st.rerun()

# ==========================================
# 4. 메인 화면 UI
# ==========================================
current_title = st.session_state.chat_sessions[st.session_state.current_session_idx]["title"]
st.title(f"💻 통합 AI 코딩 워크벤치 [{current_title}]")
st.markdown("과금 걱정 없이 실시간으로 작동하는 최상위 모델을 알아서 찾아 연결합니다.")

uploaded_file = st.file_uploader(
    "📂 소스 코드 캡처 또는 파일 업로드", 
    type=['png', 'jpg', 'jpeg', 'txt', 'py', 'json', 'csv', 'js', 'html', 'css', 'sql'],
    key=f"file_uploader_{st.session_state.current_session_idx}"
)

for msg in current_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

default_input = st.session_state.pop("pre_prompt", "")
prompt = st.chat_input("구현할 코드나 해결할 에러 내용을 입력하세요.", key=f"user_input_{st.session_state.current_session_idx}") or default_input

if prompt:
    if not current_messages:
        st.session_state.chat_sessions[st.session_state.current_session_idx]["title"] = prompt[:15] + "..."

    with st.chat_message("user"):
        st.markdown(prompt)
    current_messages.append({"role": "user", "content": prompt})

    file_text, image_data = "", None
    if uploaded_file:
        if uploaded_file.name.lower().endswith(('png', 'jpg', 'jpeg')):
            image_data = Image.open(uploaded_file)
        else:
            file_text = f"\n\n[첨부 파일 '{uploaded_file.name}']\n```\n{uploaded_file.getvalue().decode('utf-8')}\n```"

    coding_system_rule = (
        "너는 세계 최고 수준의 시니어 소프트웨어 엔지니어이자 프로그래밍 전문 AI야. "
        "사용자의 질문은 **오직 프로그래밍, 소스 코드 작성, 버그 디버깅, 단위 테스트 작성**과 관련된 내용뿐이야. "
        "인사말이나 불필요한 사설은 최대한 배제하고, 즉시 실행 가능한 깨끗한 코드와 핵심 기술적 설명 위주로 답변해.\n\n"
        f"[사용자 요청]\n{prompt}{file_text}"
    )

    # ==========================================
    # 5. 모델 호출 엔진
    # ==========================================
    def run_gemini(inputs):
        for model_name in st.session_state.gemini_model_list:
            try:
                res = genai.GenerativeModel(model_name).generate_content(inputs)
                return res.text, f"Gemini ({model_name.split('/')[-1]})"
            except Exception as e:
                err = str(e).lower()
                if any(k in err for k in ["429", "quota", "exceeded", "404", "not found", "400", "modalities"]):
                    continue
                raise e
        raise Exception("모든 Gemini 모델이 응답에 실패했습니다.")

    def run_groq(sys_rule, target_key):
        model_id = st.session_state.groq_models_dict[target_key]
        response = groq_client.chat.completions.create(
            model=model_id,
            messages=[{"role": "user", "content": sys_rule}]
        )
        return response.choices[0].message.content, model_id

    input_data = [coding_system_rule] + ([image_data] if image_data else [])

    # ---------------------------------------------------------
    # 모드별 분기 실행
    # ---------------------------------------------------------
    if ai_mode.startswith("⚡ Gemini"):
        with st.chat_message("assistant"):
            with st.spinner("Gemini 분석 중..."):
                try:
                    text, m_name = run_gemini(input_data)
                    st.markdown(f"### ⚡ {m_name}\n{text}")
                    current_messages.append({"role": "assistant", "content": f"**[{m_name}]**\n\n{text}"})
                except Exception as e: st.error(str(e))

    elif ai_mode.startswith("🚀 Groq: Llama"):
        with st.chat_message("assistant"):
            with st.spinner("Llama 분석 중..."):
                try:
                    text, m_id = run_groq(coding_system_rule, "llama")
                    st.markdown(f"### 🚀 {m_id}\n{text}")
                    current_messages.append({"role": "assistant", "content": f"**[Groq: {m_id}]**\n\n{text}"})
                except Exception as e: st.error(str(e))

    elif ai_mode.startswith("🧠 Groq: DeepSeek"):
        with st.chat_message("assistant"):
            with st.spinner("DeepSeek 추론 중..."):
                try:
                    text, m_id = run_groq(coding_system_rule, "deepseek")
                    st.markdown(f"### 🧠 {m_id}\n{text}")
                    current_messages.append({"role": "assistant", "content": f"**[Groq: {m_id}]**\n\n{text}"})
                except Exception as e: st.error(str(e))

    elif ai_mode.startswith("🔥 [비교] Gemini vs Groq"):
        col1, col2 = st.columns(2)
        with col1:
            with st.chat_message("assistant"):
                with st.spinner("Gemini 분석 중..."):
                    try:
                        res_gem, gem_name = run_gemini(input_data)
                        st.markdown(f"### ⚡ {gem_name}\n{res_gem}")
                    except Exception as e: 
                        res_gem, gem_name = str(e), "Gemini 실패"
                        st.error(res_gem)
        with col2:
            with st.chat_message("assistant"):
                with st.spinner("Llama 분석 중..."):
                    try:
                        res_groq, groq_name = run_groq(coding_system_rule, "llama")
                        st.markdown(f"### 🚀 {groq_name}\n{res_groq}")
                    except Exception as e: 
                        res_groq, groq_name = f"Groq 오류: {e}", "Groq 실패"
                        st.error(res_groq)
        current_messages.append({"role": "assistant", "content": f"**[{gem_name}]**\n\n{res_gem}\n\n---\n\n**[{groq_name}]**\n\n{res_groq}"})

    elif ai_mode.startswith("🤝 [비교+합의]"):
        col1, col2 = st.columns(2)
        
        # 1단계: DeepSeek와 Llama가 각각 코드를 짭니다.
        with col1:
            with st.chat_message("assistant"):
                with st.spinner("🧠 DeepSeek 코딩 중..."):
                    try:
                        res_ds, ds_name = run_groq(coding_system_rule, "deepseek")
                        st.markdown(f"### 🧠 {ds_name} 초안\n{res_ds}")
                    except Exception as e:
                        res_ds, ds_name = str(e), "DeepSeek 실패"
                        st.error(res_ds)
        with col2:
            with st.chat_message("assistant"):
                with st.spinner("🚀 Llama 코딩 중..."):
                    try:
                        res_llama, llama_name = run_groq(coding_system_rule, "llama")
                        st.markdown(f"### 🚀 {llama_name} 초안\n{res_llama}")
                    except Exception as e:
                        res_llama, llama_name = str(e), "Llama 실패"
                        st.error(res_llama)
                        
        st.divider()

        # 2단계: 수석 엔지니어(Llama 3.3)가 두 코드를 바탕으로 최종 합의안을 만듭니다.
        with st.chat_message("assistant"):
            with st.spinner("🧑‍💻 수석 엔지니어(AI)가 두 코드를 분석하여 최종 합의안을 작성 중입니다..."):
                try:
                    consensus_prompt = (
                        f"사용자의 코딩 요청: {prompt}{file_text}\n\n"
                        f"--- AI 1 (DeepSeek)의 초안 ---\n{res_ds}\n\n"
                        f"--- AI 2 (Llama)의 초안 ---\n{res_llama}\n\n"
                        "너는 이 프로젝트의 수석 소프트웨어 아키텍트(Staff Engineer)야. "
                        "위 두 AI가 작성한 코드를 꼼꼼히 비교하고 분석해서 장점만 취합한 가장 완벽하고 실행 가능한 '최종 코드' 하나를 작성해줘. "
                        "그리고 왜 이런 형태로 두 코드를 합의하고 최적화했는지 핵심적인 이유를 짧게 덧붙여줘."
                    )
                    # 수석 엔지니어 역할은 가장 성능이 밸런스 좋은 Llama 모델에게 맡깁니다.
                    res_final, final_name = run_groq(consensus_prompt, "llama")
                    st.markdown("### 🏆 수석 엔지니어 최종 합의안 (Best Code)")
                    st.markdown(res_final)
                    
                    # 대화 기록에는 모든 과정을 보기 좋게 저장합니다.
                    combined_log = (
                        f"**[🧠 DeepSeek 초안]**\n\n{res_ds}\n\n---\n\n"
                        f"**[🚀 Llama 초안]**\n\n{res_llama}\n\n---\n\n"
                        f"**[🏆 최종 합의안]**\n\n{res_final}"
                    )
                    current_messages.append({"role": "assistant", "content": combined_log})
                except Exception as e:
                    st.error(f"최종 합의 도중 오류 발생: {e}")
