import time
import streamlit as st
from google import genai
from google.genai import types
from google.genai.errors import APIError

st.set_page_config(page_title="Trợ lý Nghiệp vụ VBI", page_icon="🚗", layout="centered")

@st.cache_data
def doc_tai_lieu():
    try:
        with open("tailieu.txt", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "Chưa có tài liệu đính kèm."

@st.cache_resource
def lay_client():
    return genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

with st.sidebar:
    st.header("📌 Thông tin tính phí VBI")
    st.markdown(
        "- Loại xe & Mục đích sử dụng\n"
        "- Giá trị xe & Năm sản xuất\n"
        "- Kênh khai thác (Bancas / Khác)\n"
        "- Điều khoản bổ sung (BS01, BS02, BS05...)"
    )
    st.divider()
    if st.button("🔄 Cuộc trò chuyện mới", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

st.title("🚗 Trợ lý Tra cứu & Tính phí Xe cơ giới VBI")
noi_dung_tai_lieu = doc_tai_lieu()

sys_prompt = f"""
Bạn là Chuyên gia Nghiệp vụ Bảo hiểm Xe cơ giới VBI (xưng Em, gọi Anh/Chị).
TÀI LIỆU NỘI BỘ:
{noi_dung_tai_lieu}

QUY TẮC:
1. Tra cứu và tính phí bám sát tài liệu VBI (Loại xe, Giá trị xe, Tuổi xe, Kênh Bancas/Khác, ĐKBS).
2. Nếu người dùng nhập thiếu thông tin (VD: chỉ ghi "xe 500tr"), hãy liệt kê ngay các mức giảm tối đa và TLP tối thiểu của mốc 500 triệu trong bảng, đồng thời hỏi thêm thông tin còn thiếu.
3. Phân biệt rõ: TLP chuẩn, TLP thuần tối thiểu (Mục 3.1.1 & 3.1.3), Phụ phí ĐKBS và Mức giảm tối đa.
4. Công thức TLP thuần gộp (chưa VAT) = (TLP thuần + Phụ phí ĐKBS thuần) x Số ngày BH / 365. Kiểm tra phí tối thiểu 6,5 triệu (gồm VAT) và điều kiện trình TCT.
5. Câu hỏi kỹ năng chung ngoài quy chế: hỗ trợ bình thường bằng kiến thức của Gemini.
"""

if "messages" not in st.session_state or not st.session_state.messages:
    st.session_state.messages = [{
        "role": "assistant",
        "content": "👋 **Xin chào anh/chị!** Em là Trợ lý Phân cấp & Tính phí Xe cơ giới VBI 2026. Anh/chị cần tra cứu quy định hay tính phí xe nào cứ nhắn cho em nhé!"
    }]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("Nhập thông tin xe hoặc câu hỏi vào đây...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    lich_su = [
        types.Content(role="user" if m["role"] == "user" else "model", parts=[types.Part.from_text(text=m["content"])])
        for m in st.session_state.messages[-6:]
    ]

    with st.chat_message("assistant"):
        hop_cho = st.empty()
        client = lay_client()
        bot_reply = None
        ds_model = ["gemini-3.8-flash", "gemini-2.5-flash", "gemini-2.0-flash"]

        for lan in range(4):
            for ten_model in ds_model:
                try:
                    hop_cho.info(f"⏳ Đang tra cứu dữ liệu... (Lần {lan + 1})")
                    res = client.models.generate_content(
                        model=ten_model,
                        contents=lich_su,
                        config=types.GenerateContentConfig(system_instruction=sys_prompt, temperature=0.1)
                    )
                    bot_reply = res.text
                    break
                except APIError as e:
                    if "404" in str(e) or "NOT_FOUND" in str(e):
                        continue
                    time.sleep(2)
            if bot_reply:
                break
            time.sleep(3)

        hop_cho.empty()
        if not bot_reply:
            bot_reply = "⚠️ Máy chủ AI đang quá tải tạm thời, anh/chị vui lòng gửi lại sau vài giây nhé!"
        st.markdown(bot_reply)
        st.session_state.messages.append({"role": "assistant", "content": bot_reply})
