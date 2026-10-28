import time
import streamlit as st
from google import genai
from google.genai import types
from google.genai.errors import APIError

# 1. CẤU HÌNH GIAO DIỆN
st.set_page_config(
    page_title="Trợ lý Nghiệp vụ Xe cơ giới VBI",
    page_icon="🚗",
    layout="centered"
)

# 2. BỘ NHỚ ĐỆM (CACHE) TĂNG TỐC & CHỐNG NGHẼN
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

noi_dung_tai_lieu = doc_tai_lieu()

# 3. THANH BÊN (SIDEBAR)
with st.sidebar:
    st.header("📌 Hướng dẫn sử dụng")
    st.markdown(
        """
        **5 thông tin cần khi tính phí:**
        1. Loại xe & Mục đích sử dụng
        2. Giá trị xe (VNĐ)
        3. Năm sản xuất / Số năm sử dụng
        4. Kênh khai thác (Bancas / Khác)
        5. Điều khoản bổ sung (BS01, BS02, BS05...)
        """
    )
    st.divider()
    if st.button("🔄 Bắt đầu cuộc trò chuyện mới", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

st.title("🚗 Trợ lý Tra cứu & Tính phí Xe cơ giới VBI")

# 4. BẢNG TÍNH PHÍ TỰ ĐỘNG 0.1 GIÂY (KHÔNG PHỤ THUỘC AI)
with st.expander("⚡ Bấm vào đây để Mở Bảng Tính Phí Tự Động (0.1 giây)"):
    st.caption("Tra cứu trực tiếp theo Quyết định 4595/QĐ-VBI6 — Hoạt động 24/7.")
    DS_NHOM = [
        "1. Xe chở người không KD - KH Cá nhân",
        "2. Xe chở người không KD - KH Tổ chức",
        "3. Xe bán tải (Pickup) / Xe Van",
        "4. Xe chở khách du lịch theo hợp đồng",
        "5. Xe tải thùng / Đầu kéo / Container / Tải ben / Chuyên dùng",
        "6. Rơ moóc / Sơ mi rơ moóc",
        "7. Xe cứu hộ",
        "8. Xe KD vận tải hành khách / Cứu thương / Tải bảo ôn",
        "9. Xe tải đông lạnh / Xe buýt"
    ]
    DS_TUOI = [
        "Dưới 3 năm",
        "Từ 3 đến dưới 6 năm",
        "Từ 6 đến dưới 10 năm",
        "Từ 10 năm trở lên"
    ]

    col1, col2 = st.columns(2)
    with col1:
        nhom_kh = st.selectbox("1. Loại xe & Đối tượng KH", DS_NHOM)
        gia_tri_xe = st.number_input("2. Giá trị xe (Triệu VNĐ)", 50.0, 20000.0, 500.0, 50.0)
        kenh_kt = st.radio("3. Kênh khai thác", ["Kênh Bancas", "Kênh khác"], horizontal=True)

    with col2:
        tuoi_xe = st.selectbox("4. Thời gian sử dụng xe", DS_TUOI)
        tlp_chuan = st.number_input("5. TLP chuẩn chưa giảm (%)", 0.0, 10.0, 1.50, 0.05)
        so_ngay_bh = st.number_input("6. Số ngày bảo hiểm", 1, 365, 365)

    c1, c2, c3 = st.columns(3)
    with c1:
        bs01 = st.checkbox("BS01 (Mới thay cũ)", value=True)
        bs02 = st.checkbox("BS02 (Chọn cơ sở sửa chữa)", value=True)
    with c2:
        bs05 = st.checkbox("BS05 (Ngập nước 0,05%)", value=True)
        bs07 = st.checkbox("BS07 (Mất cắp bộ phận 0,07%)")
    with c3:
        bs08 = st.checkbox("BS08 (Xe tập lái 0,05%)")
        bs10 = st.checkbox("BS10 (Xe chuyên dùng 0,025%)")

    idx_nhom = DS_NHOM.index(nhom_kh) + 1
    idx_tuoi = DS_TUOI.index(tuoi_xe)
    pp_01_02 = [0.0, 0.025, 0.05, 0.075][idx_tuoi]

    tong_pp = 0.0
    if bs01:
        tong_pp += pp_01_02
    if bs02:
        tong_pp += pp_01_02
    if bs05:
        tong_pp += 0.05
    if bs07:
        tong_pp += 0.07
    if bs08:
        tong_pp += 0.05
    if bs10:
        tong_pp += 0.025

   if idx_nhom in [1, 2]:
        tlp_thuan_cb = [0.80, 0.85, 0.95, 1.05][idx_tuoi]
    elif idx_nhom == 3:
        tlp_thuan_cb = [1.05, 1.10, 1.15, 1.20][idx_tuoi]
    elif idx_nhom == 4:
        tlp_thuan_cb = [0.95, 1.00, 1.05, 1.10][idx_tuoi]
    elif idx_nhom == 6:
        tlp_thuan_cb = [0.50, 0.60, 0.65, 0.80][idx_tuoi]
    elif idx_nhom in [5, 7]:
        tlp_thuan_cb = [0.95, 1.00, 1.10, 1.20][idx_tuoi]
    elif idx_nhom == 8:
        tlp_thuan_cb = [1.15, 1.20, 1.30, 1.40][idx_tuoi]
    else:
        tlp_thuan_cb = [1.35, 1.45, 1.50, 1.70][idx_tuoi]

    tlp_thuan_gop = (tlp_thuan_cb + tong_pp) * (so_ngay_bh / 365.0)
    muc_giam_max = 0.0
    tlp_san_khac = None
    la_bancas = (kenh_kt == "Kênh Bancas")

    if idx_nhom == 1:
        if 300 <= gia_tri_xe < 500:
            muc_giam_max = 25.0 if la_bancas else 20.0
            if not la_bancas and idx_tuoi < 3:
                tlp_san_khac = [1.23, 1.32, 1.50][idx_tuoi]
        elif 500 <= gia_tri_xe < 800:
            muc_giam_max = 30.0 if la_bancas else 25.0
            if not la_bancas and idx_tuoi < 3:
                tlp_san_khac = [1.14, 1.23, 1.41][idx_tuoi]
        elif 800 <= gia_tri_xe < 1500:
            muc_giam_max = 35.0
        elif gia_tri_xe >= 1500:
            muc_giam_max = -1.0
    elif idx_nhom == 2:
        if 300 <= gia_tri_xe < 500:
            muc_giam_max = 25.0 if la_bancas else 20.0
        elif 500 <= gia_tri_xe < 800:
            muc_giam_max = 35.0
        elif gia_tri_xe >= 800:
            muc_giam_max = -1.0
    elif idx_nhom in [3, 4]:
        muc_giam_max = 30.0 if la_bancas else 25.0
    elif idx_nhom in [5, 6]:
        muc_giam_max = 35.0
    elif idx_nhom == 7:
        muc_giam_max = 30.0
    elif idx_nhom == 8:
        muc_giam_max = 25.0
    else:
        muc_giam_max = 20.0

    tlp_truoc_giam = tlp_chuan + tong_pp
    if muc_giam_max >= 0:
        tlp_sau_giam = tlp_truoc_giam * (1.0 - muc_giam_max / 100.0)
    else:
        tlp_sau_giam = tlp_thuan_gop

    muc_san = max(tlp_thuan_gop, tlp_san_khac) if tlp_san_khac else tlp_thuan_gop
    tlp_hop_le = max(tlp_sau_giam, muc_san)

    phi_co_vat = gia_tri_xe * 1_000_000 * (tlp_hop_le / 100.0) * 1.10
    if idx_nhom == 1 or (idx_nhom in [3, 4] and gia_tri_xe < 800):
        phi_co_vat = max(phi_co_vat, 6_500_000 * (so_ngay_bh / 365.0))

    txt_giam = "Theo TLP thuần gộp" if muc_giam_max == -1.0 else f"{muc_giam_max:.0f}%"
    txt_san = f"{tlp_san_khac:.2f}%" if tlp_san_khac else "Áp theo TLP thuần gộp"

    st.info(
        f"**Kết quả tra nhanh:**\n"
        f"- **Mức giảm phí tối đa:** `{txt_giam}`\n"
        f"- **TLP thuần gộp tối thiểu (chưa VAT):** `{tlp_thuan_gop:.3f}%` "
        f"(Thuần `{tlp_thuan_cb}%` + ĐKBS `{tong_pp:.3f}%`)\n"
        f"- **TLP tối thiểu Kênh khác (Mục 3.1.1):** `{txt_san}`\n"
        f"- **TLP hợp lệ sau giảm (chưa VAT):** **`{tlp_hop_le:.3f}%`**\n"
        f"- **Tổng phí thanh toán (Đã gồm 10% VAT):** **`{phi_co_vat:,.0f} VNĐ`**"
    )

# 5. CHỈ DẪN HỆ THỐNG CHO AI (SYS_PROMPT)
sys_prompt = f"""
Bạn là Chuyên gia Nghiệp vụ Bảo hiểm Xe cơ giới của VBI, hỗ trợ 25 thành viên trong phòng ban.

--- TÀI LIỆU PHÂN CẤP KHAI THÁC BẢO HIỂM VBI 2026 ---
{noi_dung_tai_lieu}
-----------------------------------------------------

QUY TẮC ĐỌC HIỂU VÀ TÍNH PHÍ BẢO HIỂM VẬT CHẤT XE CƠ GIỚI VBI:
1. Xác định đủ 5 yếu tố: Giá trị xe, Năm sản xuất (thời gian sử dụng), Kênh khai thác (Bancas/Kênh khác), Loại xe/mục đích sử dụng, và các ĐKBS áp dụng.
2. Nếu người dùng hỏi ngắn gọn (ví dụ: "tỉ lệ phí xe 500tr"), hãy liệt kê ngay các mức giảm tối đa và tỷ lệ phí tối thiểu ứng với mốc 500 triệu trong bảng (cả KH cá nhân và tổ chức, kênh Bancas và kênh khác), ĐỒNG THỜI hỏi thêm các thông tin còn thiếu để tính chính xác.
3. Phân biệt rõ: Tỷ lệ phí chuẩn, Tỷ lệ phí thuần tối thiểu (Mục 3.1.1 và 3.1.3), Phụ phí ĐKBS thuần và Mức giảm phí tối đa.
4. Công thức TLP bảo hiểm thuần gộp (chưa VAT) = (TLP bảo hiểm thuần + Phụ phí ĐKBS thuần) x Số ngày bảo hiểm / 365 ngày.
5. Kiểm tra đồng thời phí bảo hiểm tối thiểu (6.500.000đ/xe/năm gồm VAT) và các đối tượng vượt phân cấp phải trình TCT.
6. Đối với câu hỏi kỹ năng chung (soạn email, dịch thuật...), được sử dụng tri thức của Google Gemini để hỗ trợ.
7. Văn phong: Xưng 'Em' và gọi 'Anh/Chị', trình bày rõ ràng.
"""

# 6. KHỞI TẠO LỜI CHÀO
if "messages" not in st.session_state or len(st.session_state.messages) == 0:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "👋 **Xin chào anh/chị!** Em là Trợ lý Tra cứu Phân cấp & Tính phí Xe cơ giới VBI 2026.\n\n"
                "Anh/chị có thể nhắn câu hỏi vào khung chat bên dưới, hoặc bấm mở mục "
                "**⚡ Bảng Tính Phí Tự Động (0.1 giây)** ở ngay phía trên để tính phí tức thì nhé!"
            )
        }
    ]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 7. XỬ LÝ CHAT & GỌI GEMINI API (CÓ NHỚ NGỮ CẢNH & TỰ ĐỘNG THỬ LẠI)
user_input = st.chat_input("Nhập thông tin xe cần tính phí hoặc câu hỏi phân cấp...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    lich_su = []
    for m in st.session_state.messages[-8:]:
        r_api = "user" if m["role"] == "user" else "model"
        lich_su.append(types.Content(role=r_api, parts=[types.Part.from_text(text=m["content"])]))

    with st.chat_message("assistant"):
        hop_trang_thai = st.empty()
        client = lay_client()
        bot_reply = None
        max_retries = 5

        for attempt in range(max_retries):
            try:
                hop_trang_thai.info(f"⏳ Đang tra cứu phân cấp VBI... (Lần thử {attempt + 1}/{max_retries})")
                response = client.models.generate_content(
                    model="gemini-3.8-flash",
                    contents=lich_su,
                    config=types.GenerateContentConfig(
                        system_instruction=sys_prompt,
                        temperature=0.1
                    )
                )
                bot_reply = response.text
                break
            except APIError as e:
                err_msg = str(e)
                if ("503" in err_msg or "429" in err_msg or "UNAVAILABLE" in err_msg) and attempt < max_retries - 1:
                    wait_sec = (attempt + 1) * 3
                    hop_trang_thai.warning(f"Máy chủ đang đông, tự động thử lại sau {wait_sec} giây...")
                    time.sleep(wait_sec)
                    continue
                else:
                    bot_reply = (
                        "⚠️ Máy chủ AI đang quá tải tạm thời. Anh/chị hãy bấm mở mục "
                        "**⚡ Bảng Tính Phí Tự Động (0.1 giây)** ở đầu trang để tra cứu ngay lập tức nhé!"
                    )
                    break
            except Exception as e:
                bot_reply = f"⚠️ Đã xảy ra lỗi kỹ thuật: `{str(e)}`"
                break

        hop_trang_thai.empty()
        st.markdown(bot_reply)
        st.session_state.messages.append({"role": "assistant", "content": bot_reply})

