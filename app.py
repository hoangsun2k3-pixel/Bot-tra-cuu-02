import streamlit as st
from google import genai
from google.genai import types

# 1. Cấu hình giao diện Web
st.set_page_config(page_title="Trợ lý Nội bộ", page_icon="💬")
st.title("💬 Trợ lý Tra cứu & Tính toán Nội bộ")

# Khởi tạo bộ nhớ hội thoại
if "messages" not in st.session_state:
    st.session_state.messages = []

# Hiển thị lại các tin nhắn cũ trên màn hình
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Khung nhập liệu ở đáy trang
user_input = st.chat_input("Nhập câu hỏi tra cứu hoặc số liệu cần tính...")

if user_input:
    # Hiện tin nhắn người dùng vừa gửi
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # ==========================================
    # 4 DÒNG CODE CỐT LÕI: KÍCH HOẠT NÃO BỘ GEMINI
    # ==========================================
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
    
    sys_prompt = "Bạn là trợ lý bảo hiểm VBI. Hãy trả lời ngắn gọn, đối chiếu đúng tài liệu và tính toán chính xác theo công thức quy định."
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=user_input,
        config=types.GenerateContentConfig(system_instruction=sys_prompt)
    )
    
    bot_reply = response.text
    # ==========================================

    # Hiện câu trả lời của AI ra giao diện
    with st.chat_message("assistant"):
        st.markdown(bot_reply)
    st.session_state.messages.append({"role": "assistant", "content": bot_reply})