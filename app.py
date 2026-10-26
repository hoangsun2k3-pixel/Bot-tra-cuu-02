import time
import streamlit as st
from google import genai
from google.genai import types
from google.genai.errors import APIError

# -------------------------------------------------------------
# 1. CẤU HÌNH GIAO DIỆN & TIÊU ĐỀ
# -------------------------------------------------------------
st.set_page_config(
    page_title="Trợ lý Số Nội bộ",
    page_icon="🤖",
    layout="centered"
)

# -------------------------------------------------------------
# 2. THANH BÊN (SIDEBAR) & NÚT LÀM MỚI CUỘC TRÒ CHUYỆN
# -------------------------------------------------------------
with st.sidebar:
    st.header("📌 Hướng dẫn sử dụng")
    st.markdown(
        """
        - **Tra cứu:** Gõ từ khóa quy chế, điều khoản, bảng giá.
        - **Tính toán:** Nhập số liệu cụ thể (Doanh số, số lượng, tỷ lệ...).
        - **Hỗ trợ chung:** Soạn thảo văn bản, dịch thuật, giải đáp nghiệp vụ.
        
        💡 *Ví dụ câu lệnh:*
        - *"Quy định chiết khấu khách hàng VIP là gì?"*
        - *"Tính chiết khấu đơn 50 triệu thanh toán ngay."*
        """
    )
    st.divider()
    if st.button("🔄 Bắt đầu cuộc trò chuyện mới", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

st.title("🤖 Trợ lý Tra cứu & Tính toán Nội bộ")

# -------------------------------------------------------------
# 3. ĐỌC DỮ LIỆU TÀI LIỆU NỘI BỘ
# -------------------------------------------------------------
try:
    with open("tailieu.txt", "r", encoding="utf-8") as f:
        noi_dung_tai_lieu = f.read()
except FileNotFoundError:
    noi_dung_tai_lieu = "Chưa có tài liệu đính kèm."

# -------------------------------------------------------------
# 4. CHỈ DẪN VAI TRÒ & NGUYÊN TẮC CỦA BOT (LINH HOẠT)
# -------------------------------------------------------------
sys_prompt = f"""
Bạn là Trợ lý Số nội bộ phục vụ cho 25 thành viên trong phòng ban.

--- TÀI LIỆU QUY CHẾ VÀ CÔNG THỨC NỘI BỘ ---
{noi_dung_tai_lieu}
---------------------------------------------

QUY TẮC XỬ LÝ CÂU HỎI:
1. ĐỐI VỚI QUY CHẾ, BẢNG GIÁ, CÔNG THỨC CỦA PHÒNG BAN:
   - Bắt buộc lấy chính xác từ mục 'TÀI LIỆU QUY CHẾ VÀ CÔNG THỨC NỘI BỘ'.
   - Nếu câu hỏi về nội bộ nhưng trong tài liệu không có, trả lời: "Dạ thông tin này hiện chưa có trong tài liệu quy định nội bộ của phòng ban mình ạ."
   - Khi tính toán, luôn nêu rõ các bước: Biến số đầu vào -> Công thức áp dụng -> Phép tính chi tiết -> Kết quả in đậm.

2. ĐỐI VỚI CÁC CÂU HỎI KỸ NĂNG VÀ HỖ TRỢ CHUNG (Viết email, dịch thuật, kiến thức phổ thông):
   - Bạn được phép sử dụng tri thức tổng quát của Google Gemini để hỗ trợ người dùng nhiệt tình, ngắn gọn và chuẩn xác.

3. VĂN PHONG: Xưng 'Em' và gọi người dùng là 'Anh/Chị'. Tác phong chuyên nghiệp, lịch sự.
"""

# -------------------------------------------------------------
# 5. KHỞI TẠO TIN NHẮN CHÀO TỰ ĐỘNG
# -------------------------------------------------------------
if "messages" not in st.session_state or len(st.session_state.messages) == 0:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "👋 **Xin chào anh/chị!** Em là Trợ lý Tra cứu & Tính toán Nội bộ.\n\nEm đã nắm rõ các quy định trong tài liệu phòng ban. Anh/chị cần tra cứu điều khoản, tính toán số liệu hay cần hỗ trợ soạn thảo nội dung gì cứ nhắn cho em nhé!"
        }
    ]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# -------------------------------------------------------------
# 6. KHUNG CHAT & GỬI YÊU CẦU ĐẾN GEMINI (CÓ AUTO-RETRY 503)
# -------------------------------------------------------------
user_input = st.chat_input("Nhập câu hỏi hoặc số liệu cần tính vào đây...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

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
                    break
                except APIError as e:
                    if "503" in str(e) and attempt < max_retries - 1:
                        time.sleep(2)
                        continue
                    else:
                        bot_reply = "⚠️ Máy chủ AI đang tạm thời bận xử lý, anh/chị vui lòng gửi lại câu hỏi sau vài giây nhé!"
                        break

            st.markdown(bot_reply)
            st.session_state.messages.append({"role": "assistant", "content": bot_reply})
