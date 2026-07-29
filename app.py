import streamlit as st
import google.generativeai as genai
from openai import OpenAI  # 퍼플렉시티 연동용
from PIL import Image

# 페이지 설정 (넓은 화면 레이아웃)
st.set_page_config(page_title="트리플 AI 코딩 비교 비서", page_icon="🤖", layout="wide")

# ==========================================
# 1. API 키 설정 (Google & Perplexity)
# ==========================================
try:
    # 구글 Gemini 설정 (단일 키로 3.5 Flash와 3.1 Pro 모두 사용 가능)
    gemini_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=gemini_key)
    
    # 구글 모델 두 개 준비
    model_flash = genai.GenerativeModel('gemini-3.5-flash')
    model_pro = genai.GenerativeModel('gemini-3.1-pro')
    
    # 퍼플렉시티(Perplexity) 설정
    perplexity_key = st.secrets["PERPLEXITY_API_KEY"]
    pplx_client = OpenAI(api_key=perplexity_key, base_url="https://api.perplexity.ai")
    
except Exception as e:
    st.error(f"API 키 설정 오류: {e}. Streamlit Secrets에 'GEMINI_API_KEY'와 'PERPLEXITY_API_KEY'가 올바르게 등록되었는지 확인하세요.")
    st.stop()

# ==========================================
# 2. 사이드바 구성 (모드 선택 및 세션 관리)
# ==========================================
with st.sidebar:
    st.header("⚙️ AI 작동 모드")
    ai_mode = st.radio(
        "답변 방식을 선택하세요:",
        [
            "Gemini 3.5 Flash 단독", 
            "Gemini 3.1 Pro 단독 (심층 추론)", 
            "Perplexity 단독 (실시간 검색)", 
            "🔥 3개 모델 동시 비교 (추천)"
        ],
        index=3
    )

    st.divider()
    
    if "chat_sessions" not in st.session_state:
        st.session_state.chat_sessions = [{"title": "새로운 작업", "messages": []}]
    if "current_session_idx" not in st.session_state:
        st.session_state.current_session_idx = 0

    if st.button("➕ 새로운 작업 시작하기"):
        new_session = {"title": f"작업 {len(st.session_state.chat_sessions) + 1}", "messages": []}
        st.session_state.chat_sessions.append(new_session)
        st.session_state.current_session_idx = len(st.session_state.chat_sessions) - 1
        st.rerun()

    st.divider()
    st.subheader("📜 이전 작업 불러오기")
    current_messages = st.session_state.chat_sessions[st.session_state.current_session_idx]["messages"]
    
    for idx, session in enumerate(st.session_state.chat_sessions):
        btn_label = f"💬 {session['title']}"
        if idx == st.session_state.current_session_idx:
            btn_label = f"▶️ {session['title']}"
        if st.button(btn_label, key=f"session_btn_{idx}"):
            st.session_state.current_session_idx = idx
            st.rerun()

# ==========================================
# 3. 메인 화면 디자인
# ==========================================
current_title = st.session_state.chat_sessions[st.session_state.current_session_idx]["title"]
st.title(f"🤖 트리플 AI 코딩 비교 비서 [{current_title}]")
st.write(f"현재 선택된 모드: **{ai_mode}**")

# 파일 업로드 창
uploaded_file = st.file_uploader(
    "파일 첨부 (코드, 이미지 등)", 
    type=['png', 'jpg', 'jpeg', 'txt', 'py', 'json', 'csv', 'js', 'html', 'css'],
    key=f"file_uploader_{st.session_state.current_session_idx}"
)

# 이전 대화 출력
for msg in current_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 채팅 입력
if prompt := st.chat_input("어떤 코드를 짜드릴까요?", key=f"user_input_{st.session_state.current_session_idx}"):
    if len(current_messages) == 0:
        st.session_state.chat_sessions[st.session_state.current_session_idx]["title"] = prompt[:15] + "..."

    # 사용자 메시지 출력 및 저장
    with st.chat_message("user"):
        st.markdown(prompt)
    current_messages.append({"role": "user", "content": prompt})

    # 첨부파일 처리 텍스트화
    file_text = ""
    image_data = None
    if uploaded_file is not None:
        if uploaded_file.name.lower().endswith(('png', 'jpg', 'jpeg')):
            image_data = Image.open(uploaded_file)
        else:
            string_data = uploaded_file.getvalue().decode("utf-8")
            file_text = f"\n\n[첨부파일 '{uploaded_file.name}' 내용]\n{string_data}"

    full_prompt_text = prompt + file_text

    # ==========================================
    # 4. AI 답변 생성 로직 (모드별 분기)
    # ==========================================
    
    # [모드 1] Gemini 3.5 Flash 단독
    if ai_mode == "Gemini 3.5 Flash 단독":
        with st.chat_message("assistant"):
            with st.spinner("Gemini 3.5 Flash 분석 중... ⏳"):
                try:
                    input_data = [full_prompt_text]
                    if image_data: input_data.append(image_data)
                    response = model_flash.generate_content(input_data)
                    st.markdown("### ⚡ Gemini 3.5 Flash 답변")
                    st.markdown(response.text)
                    current_messages.append({"role": "assistant", "content": f"**[Gemini 3.5 Flash]**\n\n{response.text}"})
                except Exception as e:
                    st.error(f"오류 발생: {e}")

    # [모드 2] Gemini 3.1 Pro 단독
    elif ai_mode == "Gemini 3.1 Pro 단독 (심층 추론)":
        with st.chat_message("assistant"):
            with st.spinner("Gemini 3.1 Pro 심층 추론 중... ⏳"):
                try:
                    input_data = [full_prompt_text]
                    if image_data: input_data.append(image_data)
                    response = model_pro.generate_content(input_data)
                    st.markdown("### 🧠 Gemini 3.1 Pro 답변")
                    st.markdown(response.text)
                    current_messages.append({"role": "assistant", "content": f"**[Gemini 3.1 Pro]**\n\n{response.text}"})
                except Exception as e:
                    st.error(f"오류 발생: {e}")

    # [모드 3] Perplexity 단독
    elif ai_mode == "Perplexity 단독 (실시간 검색)":
        with st.chat_message("assistant"):
            with st.spinner("Perplexity 실시간 검색 및 분석 중... ⏳"):
                try:
                    pplx_response = pplx_client.chat.completions.create(
                        model="sonar",
                        messages=[{"role": "user", "content": full_prompt_text}]
                    )
                    answer = pplx_response.choices[0].message.content
                    st.markdown("### 🔵 Perplexity 답변")
                    st.markdown(answer)
                    current_messages.append({"role": "assistant", "content": f"**[Perplexity]**\n\n{answer}"})
                except Exception as e:
                    st.error(f"오류 발생: {e}")

    # [모드 4] 3개 모델 동시 비교 (화면을 3열로 분할)
    else:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            with st.chat_message("assistant"):
                with st.spinner("Flash 분석 중..."):
                    try:
                        input_data = [full_prompt_text]
                        if image_data: input_data.append(image_data)
                        res_flash = model_flash.generate_content(input_data).text
                        st.markdown("### ⚡ Gemini 3.5 Flash")
                        st.markdown(res_flash)
                    except Exception as e:
                        st.error(f"Flash 오류: {e}")

        with col2:
            with st.chat_message("assistant"):
                with st.spinner("Pro 추론 중..."):
                    try:
                        input_data = [full_prompt_text]
                        if image_data: input_data.append(image_data)
                        res_pro = model_pro.generate_content(input_data).text
                        st.markdown("### 🧠 Gemini 3.1 Pro")
                        st.markdown(res_pro)
                    except Exception as e:
                        st.error(f"Pro 오류: {e}")

        with col3:
            with st.chat_message("assistant"):
                with st.spinner("Perplexity 검색 중..."):
                    try:
                        res_pplx = pplx_client.chat.completions.create(
                            model="sonar",
                            messages=[{"role": "user", "content": full_prompt_text}]
                        ).choices[0].message.content
                        st.markdown("### 🔵 Perplexity")
                        st.markdown(res_pplx)
                    except Exception as e:
                        st.error(f"Perplexity 오류: {e}")

        # 동시 비교 결과 통합 기록
        combined_answer = f"**[Gemini 3.5 Flash]**\n\n{res_flash}\n\n---\n\n**[Gemini 3.1 Pro]**\n\n{res_pro}\n\n---\n\n**[Perplexity]**\n\n{res_pplx}"
        current_messages.append({"role": "assistant", "content": combined_answer})
