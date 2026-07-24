import streamlit as st
from streamlit_option_menu import option_menu
# from frontend.views import data_explorer
from views.auth import login, register 
from utils.auth import logout
from views import dashboard, settings, data_explorer

# ==========================================
# 1. CẤU HÌNH TRANG
# ==========================================
st.set_page_config(
    page_title="FSD Terminal - Data Lake",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Khởi tạo trạng thái đăng nhập và bộ nhớ Data Lake (Session)
if 'authenticated' not in st.session_state: st.session_state.authenticated = False
if 'show_register' not in st.session_state: st.session_state.show_register = False
if 'datalake_data' not in st.session_state: st.session_state['datalake_data'] = {} # Nơi lưu trữ datasets

# ==========================================
# 2. CUSTOM CSS
# ==========================================
st.markdown("""
<style>
    .stApp { background-color: #f8fafc; color: #0f172a; font-family: 'Inter', sans-serif; }
    #MainMenu { visibility: hidden; }
    
    .block-container { padding-top: 3.5rem !important; max-width: 100% !important; }
    
    .fsd-logo { font-family: 'Orbitron', sans-serif; font-size: 26px; font-weight: 900; background: linear-gradient(90deg, #2563eb, #0ea5e9); -webkit-background-clip: text; -webkit-text-fill-color: transparent; letter-spacing: 2px; }
    
    /* --- STYLE NÚT ACCOUNT BÊN NGOÀI --- */
    div[data-testid="stPopover"] > button { 
        border: 1px solid #cbd5e1 !important; 
        background-color: #ffffff !important; 
        color: #0f172a !important; 
        border-radius: 8px !important; 
        height: 44px !important; 
        font-weight: 600 !important;
        margin-top: 2px !important; 
    }
    
    div[data-testid="stPopover"] > button:hover { 
        border-color: #2563eb !important; 
        background-color: #f8fafc !important; 
    }
    
    /* --- TRANG TRÍ NÚT LOG OUT (Dùng kind="primary" để phân biệt) --- */
    div[data-testid="stPopoverBody"] button[kind="primary"] {
        background-color: #fff1f2 !important; /* Nền đỏ cực nhạt */
        border: 1px solid #ffe4e6 !important;
        color: #e11d48 !important; /* Chữ màu đỏ */
        border-radius: 6px !important;
        padding: 8px 12px !important;
        justify-content: center !important; /* Căn giữa nội dung */
        transition: all 0.2s ease-in-out !important;
        margin-top: 5px !important;
        box-shadow: none !important;
    }
    
    div[data-testid="stPopoverBody"] button[kind="primary"]:hover {
        background-color: #e11d48 !important; /* Chuyển nền đỏ đậm khi hover */
        color: #ffffff !important; /* Chữ trắng */
        border-color: #e11d48 !important;
    }
    
    div[data-testid="stPopoverBody"] button[kind="primary"] p {
        font-size: 14px !important;
        font-weight: 600 !important;
        margin: 0 !important;
        color: inherit !important; /* Kế thừa màu từ button để đổi màu mượt mà */
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. ĐIỀU HƯỚNG LOGIC (GATEKEEPER)
# ==========================================
if st.session_state.authenticated:
    
    # --- 3A. SIDEBAR (MENU CHÍNH) ---
    with st.sidebar:
        st.markdown("<div class='fsd-logo' style='margin-bottom: 20px; padding-left: 10px;'>FSD // </div>", unsafe_allow_html=True)
        
        # Menu mới theo đúng 6 module yêu cầu
        selected_page = option_menu(
            menu_title=None,
            options=["Dashboard", "Data Explorer", "Settings"],
            icons=["house-door", "search", "gear"],
            default_index=0,
            styles={
                "nav-link": {"font-size": "13px", "font-weight": "600", "text-transform": "uppercase"},
                "nav-link-selected": {"background-color": "rgba(37, 99, 235, 0.08)", "color": "#2563eb", "border-left": "4px solid #2563eb"}
            }
        )
        st.markdown("<br><br><br>", unsafe_allow_html=True)

    # --- 3B. THANH LỆNH TRÊN CÙNG (TOP BAR) ---
    col_memory, col_user = st.columns([5, 1])
    
    with col_memory:
        dataset_count = len(st.session_state['datalake_data'])
        st.markdown(f"""
            <div style='height: 44px; display: flex; align-items: center; padding: 0 15px; margin-top: 2px; background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px;'>
                <span style='font-size: 14px; font-weight: 600; color: #64748b;'>ACTIVE SESSION MEMORY:</span> 
                <span style='font-size: 14px; font-weight: 800; color: #2563eb; margin-left: 10px;'>{dataset_count} Datasets Loaded</span>
            </div>
        """, unsafe_allow_html=True)

    with col_user:
        with st.popover("👤 Account", width="stretch"):
            st.markdown("### 👤 User Profile")
            st.markdown("Terminal ID: <span class='mono-data' style='color: #2563eb; font-weight: bold;'>#X9-FSD</span>", unsafe_allow_html=True)
            st.divider()
            
            st.markdown("""
                <div style='font-size: 14px;'>
                    <p><b>Username:</b> FSD_Admin</p>
                    <p><b>Email:</b> admin@fsd-terminal.com</p>
                    <p><b>Password:</b> ••••••••••••</p>
                </div>
            """, unsafe_allow_html=True)
            
            st.divider()
            
            # Khôi phục type="primary" để CSS nhận diện và thêm icon cửa cho trực quan
            if st.button("🚪 Log out", type="primary", width="stretch"):
                logout()

    st.markdown("<hr style='border-color: #e2e8f0; margin: 10px 0;'>", unsafe_allow_html=True)

    # --- 3C. ROUTING (ĐIỀU HƯỚNG CÁC TRANG) ---
    try:
        if selected_page == "Dashboard": 
            dashboard.render()
        elif selected_page == "Settings": 
            settings.render()
        elif selected_page == "Data Explorer": 
            data_explorer.render()    
    except Exception as e:
        st.warning(f"🚧 Module '{selected_page}' đang được xây dựng. Vui lòng tạo file tương ứng trong thư mục views/.")

else:
    # --- GIAO DIỆN LOGIN/REGISTER ---
    if st.session_state.show_register:
        register.render()
    else:
        login.render()
