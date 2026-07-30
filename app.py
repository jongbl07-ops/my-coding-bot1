import streamlit as st
import google.generativeai as genai
from openai import OpenAI
from PIL import Image
import json
import os

# 페이지 설정
st.set_page_config(page_title="100% 무료 전문 코딩 AI 워크벤치", page_icon="💻", layout="wide")

# ==========================================
# 0. 자동 저장 및 복구(JSON) 로직 (평상시 화면 유지용)
# ==========================================
HISTORY_FILE = "auto_save_history.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return [{"title": "새로운 코딩 작업", "messages": []}]

def save_history(sessions):
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(sessions, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

# ==========================================
# 1. API 키 설정 및 실시간 모델 동적 검색
# ==========================================
try:
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
# 2. 세션 상태 초기화 (자동 저장된 내역 불러오기)
# ==========================================
if "chat_sessions" not in st.session_state:
    st.session_state.chat_sessions = load_history()

if "current_session_idx" not in st.session_state:
    st.session_state.current_session_idx = 0

if st.session_state.current_session_idx >= len(st.session_state.chat_sessions):
    st.session_state.current_session_idx = max(0, len(st.session_state.chat_sessions) - 1)

current_messages = st.session_state.chat_sessions[st.session_state.current_session_idx]["messages"]

# ==========================================
# 3. 사이드바 (설정, 숏컷, 백업/복구)
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
            "🌪️ Groq: Mixtral (빠른 속도)",
            "🔥 [비교] Gemini vs Groq Llama",
            "🤝 [비교+합의] Groq DeepSeek vs Llama"
        ],
        index=5
    )

    st.divider()
    st.subheader("🎯 주력 기술 스택 설정")
    target_stack = st.selectbox("타겟 언어/프레임워크:", ["General (자동 감지)", "Python / Django", "JavaScript / React", "Java / Spring Boot", "C++ / Rust", "SQL"])
    
    st.subheader("⚙️ 고급 동작 설정")
    no_yap_mode = st.toggle("🤫 설명 생략 (No Yapping) 모드", value=False)
    use_memory = st.toggle("🧠 이전 대화 문맥 유지", value=True)

    st.divider()
    st.subheader("🛠️ 개발자 퀵 숏컷")
    
    def get_effective_context():
        if not current_messages: return ""
        for msg in reversed(current_messages):
            if "분석할 대상 소스 코드" in msg["content"] or "코딩 전용 AI 비서입니다" in msg["content"]: continue
            return f"\n\n[참고할 이전 코드/내용]\n{msg['content']}"
        return ""

    if st.button("🐛 버그 및 에러 분석"):
        st.session_state.pre_prompt = f"아래 코드나 에러를 분석해서, 원인이 무엇이고 어떻게 수정해야 하는지 설명해 줘.{get_effective_context()}"
    if st.button("⚡ 코드 성능 최적화 (리팩토링)"):
        st.session_state.pre_prompt = f"아래 코드의 성능을 높이고 가독성을 좋게 리팩토링해 줘.{get_effective_context()}"
    if st.button("📖 주석 및 README 생성"):
        st.session_state.pre_prompt = f"아래 코드에 상세한 주석(Docstring)을 달아주고, 사용법을 README 형식으로 정돈해 줘.{get_effective_context()}"
    if st.button("🛡️ 보안 취약점 점검 (Security)"):
        st.session_state.pre_prompt = f"아래 코드의 보안 취약점(메모리 누수, SQL 인젝션 등)을 점검하고 안전하게 수정해 줘.{get_effective_context()}"

    st.divider()
    col_new, col_clear = st.columns(2)
    if col_new.button("➕ 새 작업"):
        st.session_state.chat_sessions.append({"title": f"작업 {len(st.session_state.chat_sessions) + 1}", "messages": []})
        st.session_state.current_session_idx = len(st.session_state.chat_sessions) - 1
        save_history(st.session_state.chat_sessions) # 자동 저장
        st.rerun()

    if col_clear.button("🧹 화면 지우기"):
        st.session_state.chat_sessions[st.session_state.current_session_idx]["messages"] = []
        st.session_state.chat_sessions[st.session_state.current_session_idx]["title"] = "새로운 코딩 작업"
        save_history(st.session_state.chat_sessions) # 자동 저장
        st.rerun()

    st.divider()
    st.subheader("💾 현재 작업 다운로드 (개별 보관용)")
    if current_messages:
        curr_title = st.session_state.chat_sessions[st.session_state.current_session_idx]["title"]
        md_text = f"# 💻 AI 코딩 워크벤치 - [{curr_title}]\n\n"
        for m in current_messages:
            role_icon = "🧑‍💻 User" if m["role"] == "user" else "🤖 AI Assistant"
            md_text += f"### {role_icon}\n{m['content']}\n\n---\n\n"
        st.download_button("📝 현재 대화 내역 마크다운 저장 (.md)", data=md_text, file_name=f"{curr_title}_backup.md", mime="text/markdown")

    st.divider()
    st.subheader("☁️ 전체 작업 동기화 (클라우드 복구용)")
    st.caption("며칠 뒤 앱이 절전 모드에 들어가서 히스토리가 날아갔을 때만 사용하세요.")
    history_json = json.dumps(st.session_state.chat_sessions, ensure_ascii=False, indent=2)
    st.download_button("📥 전체 내역 백업 (.json)", data=history_json, file_name="workbench_all_backup.json", mime="application/json")
    
    uploaded_history = st.file_uploader("📤 백업 파일 복구 (.json)", type=["json"])
    if uploaded_history is not None:
        try:
            loaded_data = json.load(uploaded_history)
            if isinstance(loaded_data, list) and len(loaded_data) > 0 and "messages" in loaded_data[0]:
                if st.button("🚨 이 파일로 덮어쓰기"):
                    st.session_state.chat_sessions = loaded_data
                    st.session_state.current_session_idx = 0
                    save_history(st.session_state.chat_sessions) # 덮어쓴 후 자동 저장
                    st.rerun()
        except Exception:
            st.error("파일을 읽는 중 오류가 발생했습니다.")

    # 사이드바 히스토리를 즉시 그리기 위한 예약 공간
    history_placeholder = st.empty()

# ==========================================
# 4. 사이드바 히스토리 즉시 렌더링 함수
# ==========================================
def draw_sidebar_history():
    with history_placeholder.container():
        st.divider()
        st.subheader("📜 이전 코딩 히스토리")
        
        sessions_to_delete = []
        for idx, session in enumerate(st.session_state.chat_sessions):
            col_btn, col_del = st.columns([4, 1])
            with col_btn:
                btn_label = f"📁 {session['title']}"
                if idx == st.session_state.current_session_idx:
                    btn_label = f"▶️ {session['title']}"
                if st.button(btn_label, key=f"session_btn_{idx}"):
                    st.session_state.current_session_idx = idx
                    st.rerun()
            with col_del:
                if st.button("🗑️", key=f"del_btn_{idx}", help="이 작업 삭제하기"):
                    sessions_to_delete.append(idx)

        if sessions_to_delete:
            for idx in sorted(sessions_to_delete, reverse=True):
                if len(st.session_state.chat_sessions) > 1:
                    st.session_state.chat_sessions.pop(idx)
                    if st.session_state.current_session_idx >= len(st.session_state.chat_sessions):
                        st.session_state.current_session_idx = len(st.session_state.chat_sessions) - 1
                else:
                    st.session_state.chat_sessions[0] = {"title": "새로운 코딩 작업", "messages": []}
                    st.session_state.current_session_idx = 0
            save_history(st.session_state.chat_sessions) # 삭제 후 자동 저장
            st.rerun()

# ==========================================
# 5. 메인 화면 UI
# ==========================================
current_title = st.session_state.chat_sessions[st.session_state.current_session_idx]["title"]
st.title(f"💻 통합 AI 코딩 워크벤치 [{current_title}]")

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
    # 1. 새 질문이 들어오면 즉시 제목 업데이트 및 자동 저장
    if not current_messages:
        st.session_state.chat_sessions[st.session_state.current_session_idx]["title"] = prompt[:15] + "..."
        save_history(st.session_state.chat_sessions)

    # 2. 바뀐 제목으로 사이드바 즉시 다시 그리기
    draw_sidebar_history()

    with st.chat_message("user"):
        st.markdown(prompt)
    
    chat_history_context = ""
    if use_memory and len(current_messages) > 0:
        recent_msgs = current_messages[-6:]
        chat_history_context = "\n\n[이전 대화 맥락]\n"
        for m in recent_msgs:
            role_name = "User" if m["role"] == "user" else "AI"
            chat_history_context += f"{role_name}: {m['content']}\n"
            
    current_messages.append({"role": "user", "content": prompt})
    save_history(st.session_state.chat_sessions) # 질문 추가 시 자동 저장

    file_text, image_data = "", None
    if uploaded_file:
        if uploaded_file.name.lower().endswith(('png', 'jpg', 'jpeg')):
            image_data = Image.open(uploaded_file)
        else:
            file_text = f"\n\n[첨부 파일 '{uploaded_file.name}']\n```\n{uploaded_file.getvalue().decode('utf-8')}\n```"

    stack_instruction = f" target 기술 스택: [{target_stack}]." if target_stack != "General (자동 감지)" else ""
    yapping_instruction = " **[절대 규칙] 인사말이나 부연 설명을 최소화하고 오직 실행 가능한 코드 위주로 출력하라.**" if no_yap_mode else ""
    
    coding_system_rule = (
        f"너는 세계 최고 수준의 시니어 소프트웨어 엔지니어이자 프로그래밍 전문 AI야.{stack_instruction}{yapping_instruction}\n"
        "해당 기술 스택의 최신 베스트 프랙티스에 부합하는 깨끗한 코드를 작성해.\n"
        f"{chat_history_context}\n"
        f"[현재 사용자 요청]\n{prompt}{file_text}"
    )

    # ==========================================
    # 6. 모델 호출 및 메타데이터 추적 엔진
    # ==========================================
    def run_gemini(inputs):
        for model_name in st.session_state.gemini_model_list:
            try:
                res = genai.GenerativeModel(model_name).generate_content(inputs)
                return res.text, f"Google Gemini API ({model_name.split('/')[-1]})"
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
        return response.choices[0].message.content, f"Groq Cloud ({model_id})"

    def render_metadata_expander(provider_info, stack_info):
        with st.expander("🔍 호출 API 출처 및 세부 메타데이터"):
            st.markdown(f"- **실행 엔진:** `{provider_info}`")
            st.markdown(f"- **적용 기술 스택:** `{stack_info}`")
            st.markdown(f"- **대화 문맥 유지:** `{'활성화' if use_memory else '비활성화'}`")
            st.markdown(f"- **설명 생략(No Yapping):** `{'활성화' if no_yap_mode else '비활성화'}`")

    input_data = [coding_system_rule] + ([image_data] if image_data else [])

    try:
        if ai_mode.startswith("⚡ Gemini"):
            with st.chat_message("assistant"):
                with st.spinner("Gemini 분석 중..."):
                    text, m_name = run_gemini(input_data)
                    st.markdown(f"### ⚡ {m_name}\n{text}")
                    render_metadata_expander(m_name, target_stack)
                    current_messages.append({"role": "assistant", "content": f"**[{m_name}]**\n\n{text}"})

        elif ai_mode.startswith("🚀 Groq: Llama"):
            with st.chat_message("assistant"):
                with st.spinner("Llama 분석 중..."):
                    text, m_id = run_groq(coding_system_rule, "llama")
                    st.markdown(f"### 🚀 {m_id}\n{text}")
                    render_metadata_expander(m_id, target_stack)
                    current_messages.append({"role": "assistant", "content": f"**[{m_id}]**\n\n{text}"})

        elif ai_mode.startswith("🧠 Groq: DeepSeek"):
            with st.chat_message("assistant"):
                with st.spinner("DeepSeek 추론 중..."):
                    text, m_id = run_groq(coding_system_rule, "deepseek")
                    st.markdown(f"### 🧠 {m_id}\n{text}")
                    render_metadata_expander(m_id, target_stack)
                    current_messages.append({"role": "assistant", "content": f"**[{m_id}]**\n\n{text}"})

        elif ai_mode.startswith("🌪️ Groq: Mixtral"):
            with st.chat_message("assistant"):
                with st.spinner("Mixtral 분석 중..."):
                    text, m_id = run_groq(coding_system_rule, "mixtral")
                    st.markdown(f"### 🌪️ {m_id}\n{text}")
                    render_metadata_expander(m_id, target_stack)
                    current_messages.append({"role": "assistant", "content": f"**[{m_id}]**\n\n{text}"})

        elif ai_mode.startswith("🔥 [비교]"):
            col1, col2 = st.columns(2)
            with col1:
                with st.chat_message("assistant"):
                    with st.spinner("Gemini 분석 중..."):
                        res_gem, gem_name = run_gemini(input_data)
                        st.markdown(f"### ⚡ {gem_name}\n{res_gem}")
            with col2:
                with st.chat_message("assistant"):
                    with st.spinner("Llama 분석 중..."):
                        res_groq, groq_name = run_groq(coding_system_rule, "llama")
                        st.markdown(f"### 🚀 {groq_name}\n{res_groq}")
            
            render_metadata_expander(f"{gem_name} vs {groq_name}", target_stack)
            current_messages.append({"role": "assistant", "content": f"**[{gem_name}]**\n\n{res_gem}\n\n---\n\n**[{groq_name}]**\n\n{res_groq}"})

        elif ai_mode.startswith("🤝 [비교+합의]"):
            col1, col2 = st.columns(2)
            with col1:
                with st.chat_message("assistant"):
                    with st.spinner("🧠 DeepSeek 코딩 중..."):
                        res_ds, ds_name = run_groq(coding_system_rule, "deepseek")
                        st.markdown(f"### 🧠 {ds_name} 초안\n{res_ds}")
            with col2:
                with st.chat_message("assistant"):
                    with st.spinner("🚀 Llama 코딩 중..."):
                        res_llama, llama_name = run_groq(coding_system_rule, "llama")
                        st.markdown(f"### 🚀 {llama_name} 초안\n{res_llama}")
                            
            st.divider()
            
            with st.chat_message("assistant"):
                with st.spinner("🧑‍💻 수석 엔지니어(AI)가 출처를 정리하고 최종 합의안을 작성 중입니다..."):
                    consensus_prompt = (
                        f"사용자의 코딩 요청: {prompt}{file_text}\n\n"
                        f"--- AI 1 (DeepSeek) 초안 ---\n{res_ds}\n\n"
                        f"--- AI 2 (Llama) 초안 ---\n{res_llama}\n\n"
                        "너는 이 프로젝트의 수석 아키텍트야. 두 코드를 리뷰하고 조합하여 최고의 '최종 합의안'을 만들어줘.\n"
                        "**반드시 다음 구조로 명확하게 답변해줘:**\n\n"
                        "### 📊 AI별 채택 분석\n"
                        "- **🧠 DeepSeek 장점 적용**: (어떤 로직을 가져왔는지)\n"
                        "- **🚀 Llama 장점 적용**: (어떤 구조를 가져왔는지)\n\n"
                        "### 🏆 최종 통합 코드\n"
                        "```\n(통합된 최종 코드)\n```"
                    )
                    res_final, final_name = run_groq(consensus_prompt, "llama")
                    st.markdown(res_final)
                    
                    render_metadata_expander(f"DeepSeek ({ds_name}) + Llama ({llama_name}) ➔ Evaluated by {final_name}", target_stack)
                    
                    combined_log = (
                        f"**[🧠 DeepSeek 초안]**\n\n{res_ds}\n\n---\n\n"
                        f"**[🚀 Llama 초안]**\n\n{res_llama}\n\n---\n\n"
                        f"**[🏆 최종 합의안 & 출처 분석]**\n\n{res_final}"
                    )
                    current_messages.append({"role": "assistant", "content": combined_log})
                    
    except Exception as e:
        st.error(f"오류 발생: {e}")

    # 답변 완료 후 자동 저장 및 화면 리렌더링
    save_history(st.session_state.chat_sessions)
    st.rerun()

else:
    # 대기 상태일 때 사이드바 히스토리 출력
    draw_sidebar_history()
