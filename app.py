import streamlit as st
import google.generativeai as genai
from PIL import Image

# 페이지 설정
st.set_page_config(page_title="전문 코딩 AI 비교 비서", page_icon="💻", layout="wide")

# ==========================================
# 1. API 키 설정 및 동적 모델 검색
# ==========================================
try:
    gemini_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=gemini_key)
    
    # API에서 generateContent를 지원하는 모든 모델 목록을 가져옴
    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    
    # 목록 중 'flash'와 'pro'라는 단어가 포함된 첫 번째 모델을 자동으로 찾음
    flash_model_name = next((m for m in available_models if 'flash' in m.lower()), 'gemini-1.5-flash')
    pro_model_name = next((m for m in available_models if 'pro' in m.lower()), 'gemini-1.5-pro')
    
    model_flash = genai.GenerativeModel(flash_model_name)
    model_pro = genai.GenerativeModel(pro_model_name)
    
except Exception as e:
    st.error(f"API 연결 오류: {e}. Streamlit Secrets에 'GEMINI_API_KEY'가 올바르게 등록되었는지 확인하세요.")
    st.stop()

# ==========================================
# 2. 세션 상태 초기화
# ==========================================
if "chat_sessions" not in st.session_state:
    st.session_state.chat_sessions = [{"title": "새로운 코딩 작업", "messages": []}]

if "current_session_idx" not in st.session_state:
    st.session_state.current_session_idx = 0

current_messages = st.session_state.chat_sessions[st.session_state.current_session_idx]["messages"]
current_title = st.session_state.chat_sessions[st.session_state.current_session_idx]["title"]

# ==========================================
# 3. 사이드바 (개발 설정 및 숏컷)
# ==========================================
with st.sidebar:
    st.header("💻 코딩 작업실 설정")
    
    st.info(f"**현재 연결된 모델**\n\n⚡ Flash: `{flash_model_name.split('/')[-1]}`\n\n🧠 Pro: `{pro_model_name.split('/')[-1]}`")
    
    ai_mode = st.radio(
        "사용할 AI 분석 엔진:",
        ["Flash (초고속)", "Pro (고난도 추론)", "🔥 두 모델 동시 비교"],
        index=0
    )

    st.divider()
    
    # [신규 기능 1] AI 페르소나 설정
    st.subheader("🎭 AI 페르소나 설정")
    persona_options = {
        "시니어 소프트웨어 엔지니어": "세계 최고 수준의 시니어 소프트웨어 엔지니어",
        "프론트엔드 전문가 (React/Vue)": "최신 UI/UX 트렌드와 React, Vue 등 프론트엔드 프레임워크에 정통한 웹 개발 전문가",
        "백엔드/DB 설계자 (Python/SQL)": "대용량 트래픽 처리, 시스템 아키텍처 및 복잡한 SQL/DB 성능 최적화 전문가",
        "데이터 사이언티스트 (ML/Pandas)": "데이터 분석, 머신러닝, 파이썬(Pandas, NumPy)을 활용한 데이터 파이프라인 설계 전문가"
    }
    selected_persona = st.selectbox("AI의 전문 분야를 선택하세요:", list(persona_options.keys()))

    # [신규 기능 2] Temperature 조절
    st.subheader("🎛️ 답변 정밀도 (Temperature)")
    temperature = st.slider(
        "값을 조절하세요", 
        min_value=0.0, max_value=1.0, value=0.2, step=0.1,
        help="0에 가까울수록 정확하고 보수적인 코드, 1에 가까울수록 창의적이고 다양한 구조를 시도합니다. (디버깅은 0.0~0.2 권장)"
    )

    st.divider()
    
    st.subheader("🛠️ 개발자 퀵 숏컷")
    def get_effective_context():
        if not current_messages:
            return ""
        for msg in reversed(current_messages):
            content = msg["content"]
            if "분석할 대상 소스 코드가 제공되지 않았습니다" in content:
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
    
    # [신규 기능 3] 대화 내역 다운로드
    st.subheader("💾 세션 백업")
    if current_messages:
        md_text = f"# {current_title}\n\n"
        for m in current_messages:
            role_name = "🧑‍💻 User" if m["role"] == "user" else "🤖 AI Assistant"
            md_text += f"### {role_name}\n{m['content']}\n\n---\n\n"
        
        st.download_button(
            label="현재 대화내역 저장 (.md)",
            data=md_text,
            file_name=f"{current_title}_backup.md",
            mime="text/markdown"
        )
    else:
        st.write("저장할 대화 내역이 없습니다.")

    st.divider()
    
    # 대화 세션 관리
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
        st.rerun()

# ==========================================
# 4. 메인 화면 (개발 환경 인터페이스)
# ==========================================
st.title(f"💻 AI 코딩 워크벤치 [{current_title}]")
st.markdown("오직 **프로그래밍, 코드 분석, 에러 디버깅**에만 집중하는 전문 개발 AI 비서입니다.")

uploaded_file = st.file_uploader(
    "📂 소스 코드 또는 에러 캡처 업로드 (.py, .js, .txt, .png, .jpg 등)", 
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

    # 동적 페르소나 적용 시스템 프롬프트
    role_description = persona_options[selected_persona]
    coding_system_rule = (
        f"너는 {role_description}야. "
        "사용자의 질문은 **오직 프로그래밍, 소스 코드 작성, 버그 디버깅, 단위 테스트 작성**과 관련된 내용뿐이야. "
        "인사말이나 불필요한 사설은 최대한 배제하고, 즉시 실행 가능한 깨끗한 코드와 핵심 기술적 설명 위주로 답변해. "
        "만약 참고할 코드가 없다면 '분석할 대상 소스 코드가 제공되지 않았습니다.'라고 안내해 줘.\n\n"
        f"[사용자 요청 및 컨텍스트]\n{prompt}{file_text}"
    )

    gen_config = genai.types.GenerationConfig(temperature=temperature)

    # ==========================================
    # 5. 개발 전용 AI 처리 로직
    # ==========================================
    if ai_mode == "Flash (초고속)":
        with st.chat_message("assistant"):
            with st.spinner("Flash 모델이 분석 중입니다... ⚡"):
                try:
                    input_data = [coding_system_rule]
                    if image_data: input_data.append(image_data)
                    response = model_flash.generate_content(input_data, generation_config=gen_config)
                    st.markdown(f"### ⚡ Flash 코드 솔루션 ({selected_persona})")
                    st.markdown(response.text)
                    current_messages.append({"role": "assistant", "content": f"**[Flash]**\n\n{response.text}"})
                except Exception as e:
                    st.error(f"오류 발생: {e}")

    elif ai_mode == "Pro (고난도 추론)":
        with st.chat_message("assistant"):
            with st.spinner("Pro 모델이 분석 중입니다... 🧠"):
                try:
                    input_data = [coding_system_rule]
                    if image_data: input_data.append(image_data)
                    response = model_pro.generate_content(input_data, generation_config=gen_config)
                    st.markdown(f"### 🧠 Pro 코드 솔루션 ({selected_persona})")
                    st.markdown(response.text)
                    current_messages.append({"role": "assistant", "content": f"**[Pro]**\n\n{response.text}"})
                except Exception as e:
                    st.error(f"오류 발생: {e}")

    else:
        # 두 모델 동시 비교 모드
        col1, col2 = st.columns(2)
        
        res_flash = "Flash 분석 실패"
        res_pro = "Pro 분석 실패"

        with col1:
            with st.chat_message("assistant"):
                with st.spinner("Flash 분석 중..."):
                    try:
                        input_data = [coding_system_rule]
                        if image_data: input_data.append(image_data)
                        res_flash = model_flash.generate_content(input_data, generation_config=gen_config).text
                        st.markdown("### ⚡ Flash")
                        st.markdown(res_flash)
                    except Exception as e:
                        res_flash = f"Flash 오류: {e}"
                        st.error(res_flash)

        with col2:
            with st.chat_message("assistant"):
                with st.spinner("Pro 분석 중..."):
                    try:
                        input_data = [coding_system_rule]
                        if image_data: input_data.append(image_data)
                        res_pro = model_pro.generate_content(input_data, generation_config=gen_config).text
                        st.markdown("### 🧠 Pro")
                        st.markdown(res_pro)
                    except Exception as e:
                        res_pro = f"Pro 오류: {e}"
                        st.error(res_pro)

        combined_answer = f"**[Flash]**\n\n{res_flash}\n\n---\n\n**[Pro]**\n\n{res_pro}"
        current_messages.append({"role": "assistant", "content": combined_answer})
