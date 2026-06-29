import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd

# Cấu hình trang giao diện
st.set_page_config(page_title="Hệ thống Dự toán Điện Mặt Trời", layout="wide")

st.title("☀️ Hệ thống Bốc Dự toán & Cập nhật Giá Pin Mặt Trời")


# --- PHẦN 1: CÀO DỮ LIỆU TỰ ĐỘNG TỪ WEBSITE ---
st.header("🔄 1. Cập nhật Giá Thiết bị Tự động")


# Giả sử đây là danh sách link sản phẩm của nhà cung cấp bạn thường mua
# Bạn có thể thay đổi link và cấu trúc thẻ HTML cho phù hợp với web thực tế
@st.cache_data(ttl=3600)  # Lưu bộ nhớ đệm 1 tiếng để tránh tải lại quá nhiều lần làm chậm app
def crawl_solar_prices():
    data = {
        "Thiết bị": ["Tấm pin Longi 550W", "Inverter Growatt 10kW", "Inverter Deye 5kW", "Vật tư phụ & Khung (m²)"],
        "Giá gốc (VNĐ)": [2400000, 22000000, 18500000, 450000]  # Giá dự phòng nếu lỗi mạng
    }

    # Đoạn code mẫu để cào giá từ một trang web (Bạn có thể cấu hình lại theo web cụ thể)
    # try:
    #     response = requests.get("https://example-solar-provider.com/product/longi-550w")
    #     soup = BeautifulSoup(response.text, 'html.parser')
    #     # Tìm thẻ chứa giá, ví dụ: <span class="price">2.400.000đ</span>
    #     price_text = soup.find("span", {"class": "price"}).text
    #     price = int(''.join(filter(str.isdigit, price_text)))
    #     data["Giá gốc (VNĐ)"][0] = price
    # except Exception as e:
    #     st.warning("Không thể kết nối cào giá tự động, đang sử dụng giá dự phòng gần nhất.")

    return pd.DataFrame(data)

df_prices = crawl_solar_prices()
st.table(df_prices) #  Thay bằng dòng này
#df_prices = crawl_solar_prices()
#st.dataframe(df_prices, use_container_width=True)

# --- PHẦN 2: NHẬP LIỆU TƯ VẤN (BÀN GIAO TIẾP VỚI KHÁCH) ---
st.header("📋 2. Nhập Thông số Khách hàng")

col1, col2 = st.columns(2)

with col1:
    customer_name = st.text_input("Tên khách hàng / Dự án", "Khách hàng thân thiết")
    selection_type = st.radio("Tính toán quy mô hệ thống dựa trên:",
                              ["Số tiền điện hàng tháng (VNĐ)", "Diện tích mái khả dụng (m²)"])

with col2:
    if selection_type == "Số tiền điện hàng tháng (VNĐ)":
        monthly_bill = st.number_input("Tiền điện trung bình tháng (VNĐ)", min_value=500000, value=3000000, step=100000)
        # Ước tính công suất: Tiền điện / 3000đ/kwh / 4 giờ nắng trung bình / 30 ngày
        estimated_kwp = round((monthly_bill / 3000) / (4 * 30), 2)
        st.info(f"💡 Công suất khuyến nghị dựa trên hóa đơn điện: **{estimated_kwp} kWp**")
    else:
        roof_area = st.number_input("Diện tích mái nhà (m²)", min_value=10, value=50, step=5)
        # 1 kWp cần khoảng 6m² mái
        estimated_kwp = round(roof_area / 6, 2)
        st.info(f"💡 Công suất tối đa có thể lắp trên diện tích mái: **{estimated_kwp} kWp**")

# Biên lợi nhuận mong muốn của bạn (Quản lý nội bộ)
st.sidebar.header("⚙️ Cấu hình Biên Lợi nhuận")
profit_margin = st.sidebar.slider("Biên lợi nhuận của bạn (%)", min_value=10, max_value=50, value=25)
installation_fee_per_kwp = st.sidebar.number_input("Chi phí nhân công / 1 kWp (VNĐ)", value=1500000)

# --- PHẦN 3: XUẤT BẢN DỰ TOÁN BÁO GIÁ ---
st.header("📊 3. Bảng Dự toán Chi tiết cho Khách xem")

# Tính toán số lượng vật tư dựa trên kWp đề xuất
panel_power = 550  # W
panels_needed = int((estimated_kwp * 1000) / panel_power) + 1
area_needed = panels_needed * 2.6  # Mỗi tấm khoảng 2.6m²

# Chọn loại Inverter phù hợp
if estimated_kwp <= 6:
    inverter_name = "Inverter Deye 5kW"
    inverter_price = df_prices.loc[df_prices["Thiết bị"] == "Inverter Deye 5kW", "Giá gốc (VNĐ)"].values[0]
else:
    inverter_name = "Inverter Growatt 10kW"
    inverter_price = df_prices.loc[df_prices["Thiết bị"] == "Inverter Growatt 10kW", "Giá gốc (VNĐ)"].values[0]

panel_unit_price = df_prices.loc[df_prices["Thiết bị"] == "Tấm pin Longi 550W", "Giá gốc (VNĐ)"].values[0]
material_unit_price = df_prices.loc[df_prices["Thiết bị"] == "Vật tư phụ & Khung (m²)", "Giá gốc (VNĐ)"].values[0]

# Tính tổng chi phí gốc
total_panel_cost = panels_needed * panel_unit_price
total_material_cost = area_needed * material_unit_price
total_labor_cost = estimated_kwp * installation_fee_per_kwp
total_cost_base = total_panel_cost + inverter_price + total_material_cost + total_labor_cost

# Áp biên lợi nhuận để ra giá báo cho khách
total_quote = total_cost_base * (1 + profit_margin / 100)

# Hiển thị bảng kết quả thiết bị
quote_data = {
    "Hạng mục": ["Tấm pin mặt trời", "Biến tần (Inverter)", "Hệ khung giàn & Vật tư phụ", "Chi phí nhân công lắp đặt"],
    "Chi tiết kỹ thuật": [
        f"{panels_needed} tấm Longi {panel_power}W (Tổng: {round(panels_needed * panel_power / 1000, 2)} kWp)",
        f"1 bộ - {inverter_name}", f"Ước tính cho {round(area_needed, 1)} m² diện tích tấm pin",
        f"Thi công trọn gói hệ {estimated_kwp} kWp"],
    "Đơn giá báo cho khách (VNĐ)": [
        f"{int(panel_unit_price * (1 + profit_margin / 100)):,}",
        f"{int(inverter_price * (1 + profit_margin / 100)):,}",
        f"{int(material_unit_price * (1 + profit_margin / 100)):,}/m²",
        f"{int(installation_fee_per_kwp * (1 + profit_margin / 100)):,}/kWp"
    ]
}

st.table(pd.DataFrame(quote_data))

st.subheader(f"💰 TỔNG GIÁ TRỊ HỢP ĐỒNG DỰ KIẾN: {int(total_quote):,} VNĐ")

# Nút xuất file để gửi nhanh cho khách qua Zalo nếu cần
if st.button("🖨️ Xuất File Báo Giá Nhanh"):
    st.success(
        f"Đã chuẩn bị xong dữ liệu cho dự án của khách hàng: {customer_name}. Bạn có thể chụp ảnh màn hình này hoặc in ra PDF để gửi cho khách!")
