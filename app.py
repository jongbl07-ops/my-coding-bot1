import streamlit as st
import google.generativeai as genai
from PIL import Image

# ==========================================
# 1. API 키 설정
# ==========================================
# 따옴표 안에 키를 직접 쓰지 말고, 아래처럼 'GEMINI_API_KEY'라는 이름표를 적어주세요!
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-3.5-flash')
