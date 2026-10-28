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

    if idx
