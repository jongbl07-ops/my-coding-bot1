import streamlit as st
import google.generativeai as genai
from openai import OpenAI
from PIL import Image

# 페이지 설정
st.set_page_config(page_title="전문 코딩 AI 비교 비서", page_icon="💻", layout="wide")

# ==========================================
# 1. API 키 설정
# ==========================================
try:
    gemini_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=gemini_key)
    model_flash = genai.GenerativeModel('gemini-3.5-flash')
    model_pro = genai.GenerativeModel('gemini-3.1-pro')
    
    kimi_key = st.secrets["KIMI_API_KEY"]
    kimi_client = OpenAI(api_key=kimi_key, base_url="https://api.moonshot.ai/v1")
except Exception as e:
    st.error(f"API 키 설정 오류: {e}. Streamlit Secrets에 'GEMINI_API_KEY'와 'KIMI_API_KEY'가 올바르게 등록되었는지 확인하세요.")
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
# 3. 사이드바 (개발 전용 모드 및 숏컷)
# ==========================================
with st.sidebar:
    st.header("💻 코딩 작업실 설정")
    ai_mode = st.radio(
        "사용할 AI 분석 엔진:",
        [
            "Gemini 3.5 Flash (빠른 코드 작성)", 
            "Gemini 3.1 Pro (고난도 로직/추론)", 
            "Kimi (대용량 소스 분석)",
            "🔥 3개 모델 코딩 동시 비교"
        ],
        index=3
    )

    st.divider()
    
    st.subheader("🛠️ 개발자 퀵 숏컷")
    if st.button("🐛 버그 및 에러 원인 분석"):
        st.session_state.pre_prompt = "첨부된 에러 로그나 코드를 분석해서, 원인이 무엇이고 어떻게 수정해야 하는지 정확한 수정 코드와 함께 설명해 줘."
    if st.button("⚡ 코드 성능 최적화 (Refactoring)"):
        st.session_state.pre_prompt = "이 코드의 성능을 높이고 가독성을 좋게 리팩토링해 줘."
    if st.button("🧪 단위 테스트 코드 생성"):
        st.session_state.pre_prompt = "이 코드를 검증할 수 있는 단위 테스트(Unit Test) 코드를 작성해 줘."

    st.divider()
    
    if st.button("➕ 새로운 코딩 작업"):
        new_session = {"title": f"작업 {len(st.session_state.chat_sessions) + 1}", "messages": []}
        st.session_state.chat_sessions.append(new_session)
        st.session_state.current_session_idx = len(st.session_state.chat_sessions) - 1
        st.rerun()

    if st.button("🧹 현재 대화 초기화"):
        st.session_state.chat_sessions[st.session_state.current_session_idx]["messages"] = []
        st.session_state.chat_sessions[st.session_state.current_session_idx]["title"] = "새로운 코딩 작업"
        st.rerun()

    st.divider()
    st.subheader("📜 이전 코딩 히스토리")
    for idx, session in enumerate(st.session_state.chat_sessions):
        btn_label = f"📁 {session['title']}"
        if idx == st.session_state.current_session_idx:
            btn_label = f"▶️ {session['title']}"
        if st.button(btn_label, key=f"session_btn_{idx}"):
            st.session_state.current_session_idx = idx
            st.rerun()

# ==========================================
# 4. 메인 화면 (개발 환경 인터페이스)
# ==========================================
current_title = st.session_state.chat_sessions[st.session_state.current_session_idx]["title"]
st.title(f"💻 AI 코딩 워크벤치 [{current_title}]")
st.markdown("소스 코드 파일을 업로드하거나 에러 화면을 캡처해 올리면 AI가 즉시 분석하고 수정안을 제시합니다.")

# 파일 업로드 (코드 파일 전용 강조)
uploaded_file = st.file_uploader(
    "📂 소스 코드 또는 에러 캡처 업로드 (.py, .js, .txt, .png 등)", 
    type=['png', 'jpg', 'jpeg', 'txt', 'py', 'json', 'csv', 'js', 'html', 'css', 'sql'],
    key=f"file_uploader_{st.session_state.current_session_idx}"
)

# 이전 대화 출력
for msg in current_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 사이드바 숏컷 버튼 처리
default_input = st.session_state.pop("pre_prompt", "")

if prompt := st.chat_input("어떤 코드를 구현할까요? 혹은 궁금한 에러를 입력하세요.", key=f"user_input_{st.session_state.current_session_idx}"):
    pass
elif default_input:
    prompt = default_input

if prompt:
    if len(current_messages) == 0:
        st.session_state.chat_sessions[st.session_state.current_session_idx]["title"] = prompt[:15] + "..."

    with st.chat_message("user"):
        st.markdown(prompt)
    current_messages.append({"role": "user", "content": prompt})

    # 첨부파일 가공
    file_text = ""
    image_data = None
    if uploaded_file is not None:
        if uploaded_file.name.lower().endswith(('png', 'jpg', 'jpeg')):
            image_data = Image.open(uploaded_file)
        else:
            string_data = uploaded_file.getvalue().decode("utf-8")
            file_text = f"\n\n[첨부된 소스코드/파일 '{uploaded_file.name}' 내용]\n```\n{string_data}\n```"

    full_prompt_text = prompt + file_text

    # ==========================================
    # 5. 개발 전용 AI 처리 로직
    # ==========================================
    if ai_mode == "Gemini 3.5 Flash (빠른 코드 작성)":
        with st.chat_message("assistant"):
            with st.spinner("Gemini 3.5 Flash가 코드를 작성 중입니다... ⚡"):
                try:
                    input_data = [full_prompt_text]
                    if image_data: input_data.append(image_data)
                    response = model_flash.generate_content(input_data)
                    st.markdown("### ⚡ Gemini 3.5 Flash 코드 솔루션")
                    st.markdown(response.text)
                    current_messages.append({"role": "assistant", "content": f"**[Gemini 3.5 Flash]**\n\n{response.text}"})
                except Exception as e:
                    st.error(f"오류 발생: {e}")

    elif ai_mode == "Gemini 3.1 Pro (고난도 로직/추론)":
        with st.chat_message("assistant"):
            with st.spinner("Gemini 3.1 Pro가 복잡한 알고리즘을 분석 중입니다... 🧠"):
                try:
                    input_data = [full_prompt_text]
                    if image_data: input_data.append(image_data)
                    response = model_pro.generate_content(input_data)
                    st.markdown("### 🧠 Gemini 3.1 Pro 코드 솔루션")
                    st.markdown(response.text)
                    current_messages.append({"role": "assistant", "content": f"**[Gemini 3.1 Pro]**\n\n{response.text}"})
                except Exception as e:
                    st.error(f"오류 발생: {e}")

    elif ai_mode == "Kimi (대용량 소스 분석)":
        with st.chat_message("assistant"):
            with st.spinner("Kimi가 대용량 소스코드를 검토 중입니다... 🌙"):
                try:
                    kimi_response = kimi_client.chat.completions.create(
                        model="kimi-k3",
                        messages=[{"role": "user", "content": full_prompt_text}]
                    )
                    answer = kimi_response.choices[0].message.content
                    st.markdown("### 🌙 Kimi 코드 솔루션")
                    st.markdown(answer)
                    current_messages.append({"role": "assistant", "content": f"**[Kimi]**\n\n{answer}"})
                except Exception as e:
                    st.error(f"오류 발생: {e}")

    else:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            with st.chat_message("assistant"):
                with st.spinner("Flash 분석 중..."):
                    try:
                        input_data = [full_prompt_text]
                        if image_data: input_data.append(image_data)
                        res_flash = model_flash.generate_content(input_data).text
                        st.markdown("### ⚡ Flash")
                        st.markdown(res_flash)
                    except Exception as e:
                        st.error(f"Flash 오류: {e}")

        with col2:
            with st.chat_message("assistant"):
                with st.spinner("Pro 분석 중..."):
                    try:
                        input_data = [full_prompt_text]
                        if image_data: input_data.append(image_data)
                        res_pro = model_pro.generate_content(input_data).text
                        st.markdown("### 🧠 Pro")
                        st.markdown(res_pro)
                    except Exception as e:
                        st.error(f"Pro 오류: {e}")

        with col3:
            with st.chat_message("assistant"):
                with st.spinner("Kimi 분석 중..."):
                    try:
                        res_kimi = kimi_client.chat.completions.create(
                            model="kimi-k3",
                            messages=[{"role": "user", "content": full_prompt_text}]
                        ).choices[0].message.content
                        st.markdown("### 🌙 Kimi")
                        st.markdown(res_kimi)
                    except Exception as e:
                        st.error(f"Kimi 오류: {e}")

        combined_answer = f"**[Gemini 3.5 Flash]**\n\n{res_flash}\n\n---\n\n**[Gemini 3.1 Pro]**\n\n{res_pro}\n\n---\n\n**[Kimi]**\n\n{res_kimi}"
        current_messages.append({"role": "assistant", "content": combined_answer})
