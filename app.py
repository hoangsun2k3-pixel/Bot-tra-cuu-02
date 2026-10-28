import time
import streamlit as st
from google import genai
from google.genai import types
from google.genai.errors import APIError

# -------------------------------------------------------------
# 1. CẤU HÌNH GIAO DIỆN & TIÊU ĐỀ
# -------------------------------------------------------------
st.set_page_config(
    page_title="Trợ lý Nghiệp vụ Xe cơ giới VBI",
    page_icon="🚗",
    layout="centered"
)

# -------------------------------------------------------------
# 2. TỐI ƯU BỘ NHỚ ĐỆM (CACHE) ĐỂ TĂNG TỐC & CHỐNG NGHẼN
# -------------------------------------------------------------
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

# -------------------------------------------------------------
# 3. THANH BÊN (SIDEBAR) & NÚT LÀM MỚI CUỘC TRÒ CHUYỆN
# -------------------------------------------------------------
with st.sidebar:
    st.header("📌 Hướng dẫn sử dụng")
    st.markdown(
        """
        **5 thông tin cần cung cấp khi tính phí:**
        1. **Loại xe & Mục đích sử dụng** (Cá nhân, tổ chức, KD vận tải, bán tải...)
        2. **Giá trị xe** (VNĐ)
        3. **Năm sản xuất / Số năm sử dụng**
        4. **Kênh khai thác** (Bancas hay Kênh khác)
        5. **Điều khoản bổ sung** (BS01, BS02, BS05...)

        💡 *Ví dụ câu lệnh:*
        - *"Xe cá nhân 600 triệu, sử dụng 2 năm, kênh Bancas, thêm BS01, BS02, BS05"*
        - *"Xe những đối tượng nào không thuộc phân cấp giảm phí của ĐVKD?"*
        """
    )
    st.divider()
    if st.button("🔄 Bắt đầu cuộc trò chuyện mới", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

st.title("🚗 Trợ lý Tra cứu & Tính phí Xe cơ giới VBI")

# -------------------------------------------------------------
# 4. CÔNG CỤ TÍNH NHANH 0.1 GIÂY (DỰ PHÒNG KHI AI QUÁ TẢI)
# -------------------------------------------------------------
with st.expander("⚡ Bấm vào đây để Mở Bảng Tính Phí Tự Động (0.1 giây - Không cần chờ AI)"):
    st.caption("Tra cứu trực tiếp theo Quyết định 4595/QĐ-VBI6 — Hoạt động tức thì 24/7.")
    col1, col2 = st.columns(2)
    with col1:
        nhom_kh = st.selectbox(
            "1. Loại xe & Đối tượng KH",
            [
                "Xe chở người không KD - KH Cá nhân",
                "Xe chở người không KD - KH Tổ chức",
                "Xe bán tải (Pickup) / Xe Van",
                "Xe chở khách du lịch theo hợp đồng",
                "Xe tải thùng / Đầu kéo / Container / Tải ben / Chuyên dùng",
                "Rơ moóc / Sơ mi rơ moóc",
                "Xe cứu hộ",
                "Xe KD vận tải hành khách / Cứu thương / Tải bảo ôn",
                "Xe tải đông lạnh / Xe buýt"
            ]
        )
        gia_tri_xe = st.number_input("2. Giá trị xe (Triệu VNĐ)", min_value=50.0, max_value=20000.0, value=500.0, step=50.0)
        kenh_kt = st.radio("3. Kênh khai thác", ["Kênh Bancas", "Kênh khai thác khác"], horizontal=True)

    with col2:
        tuoi_xe = st.selectbox(
            "4. Thời gian sử dụng xe",
            ["Dưới 3 năm", "Từ 3 đến dưới 6 năm", "Từ 6 đến dưới 10 năm", "Từ 10 năm trở lên"]
        )
        tlp_chuan = st.number_input("5. Tỷ lệ phí chuẩn chưa giảm (% - nếu có)", min_value=0.0, max_value=10.0, value=1.50, step=0.05)
        so_ngay_bh = st.number_input("6. Số ngày bảo hiểm", min_value=1, max_value=365, value=365)

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

    idx_tuoi = ["Dưới 3 năm", "Từ 3 đến dưới 6 năm", "Từ 6 đến dưới 10 năm", "Từ 10 năm trở lên"].index(tuoi_xe)
    pp_01_02 = [0.0, 0.025, 0.05, 0.075][idx_tuoi]
    tong_pp = (pp_01_02 if bs01 else 0.0) + (pp_01_02 if bs02 else 0.0) + (0.05 if bs05 else 0.0) + (0.07 if bs07 else 0.0) + (0.05 if bs08 else 0.0) + (0.025 if bs10 else 0.0)

    if "Xe chở người không KD" in nhom_kh or "Xe buýt" in nhom_kh:
        tlp_thuan_cb = [0.80, 0.85, 0.95, 1.05][idx_tuoi]
    elif "Xe bán tải" in nhom_kh:
        tlp_thuan_cb = [1.05, 1.10, 1.15, 1.20][idx_tuoi]
    elif "du lịch theo hợp đồng" in nhom_kh:
        tlp_thuan_cb = [0.95, 1.00, 1.05, 1.10][idx_tuoi]
    elif "Rơ moóc" in nhom_kh:
        tlp_thuan_cb = [0.50, 0.60, 0.65, 0.80][idx_tuoi]
    elif "Xe cứu hộ" in nhom_kh or "Xe tải thùng" in nhom_kh:
        tlp_thuan_cb = [0.95, 1.00, 1.10, 1.20][idx_tuoi]
    elif "vận tải hành
