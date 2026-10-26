import time
from google.genai.errors import APIError

user_input = st.chat_input("Nhập câu hỏi hoặc số liệu cần tính vào đây...")

if user_input:
    # 1. Hiển thị câu hỏi của người dùng
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # 2. Xử lý gọi Gemini API với cơ chế tự động thử lại nếu máy chủ quá tải
    with st.chat_message("assistant"):
        with st.spinner("Đang tra cứu dữ liệu..."):
            client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
            bot_reply = None
            max_retries = 3

            for attempt in range(max_retries):
                try:
                    response = client.models.generate_content(
                        model="gemini-3.8-flash",
                        contents=user_input,
                        config=types.GenerateContentConfig(system_instruction=sys_prompt)
                    )
                    bot_reply = response.text
                    break  # Thành công thì thoát vòng lặp
                except APIError as e:
                    # Nếu gặp lỗi quá tải 503, chờ 2 giây rồi thử lại
                    if "503" in str(e) and attempt < max_retries - 1:
                        time.sleep(2)
                        continue
                    else:
                        bot_reply = "⚠️ Hệ thống máy chủ AI đang quá tải tạm thời, anh/chị vui lòng thử lại sau 30 giây nhé!"
                        break

            st.markdown(bot_reply)
            st.session_state.messages.append({"role": "assistant", "content": bot_reply})
