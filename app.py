import streamlit as st
import pandas as pd
import io

# ========== 基本配置 ==========
st.set_page_config(
    page_title="Peppermayo 数据归类",
    page_icon="📊",
    layout="wide"
)

# ========== 全局 CSS（强制深色 + 自定义 UI + 隐藏 Streamlit 组件）==========
st.markdown("""
<style>

/* 强制深色背景（覆盖 Streamlit 内置主题） */
html, body, .block-container {
    background-color: #0f1117 !important;
    color: white !important;
}

/* 主内容最大宽度 + 居中 */
.block-container {
    max-width: 1320px;
    margin: auto;
    padding-top: 2rem;
    padding-bottom: 2rem;
}

/* ====== 卡片 ====== */
.pm-card, .pm-info-card, .pm-hero {
    border-radius: 16px;
    border: 1px solid rgba(255,255,255,0.06);
    box-shadow: 0 16px 40px rgba(0,0,0,0.45);
    margin-bottom: 24px;
}

/* 顶部 Hero 卡片 */
.pm-hero {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 20px 26px;
    background: linear-gradient(135deg, #20232a 0%, #15171c 100%);
}
.pm-hero-icon {
    font-size: 32px;
    width: 56px;
    height: 56px;
    display: flex;
    justify-content: center;
    align-items: center;
    border-radius: 16px;
    background: rgba(255,255,255,0.06);
}
.pm-hero-title { font-size: 24px; font-weight: 650; }
.pm-hero-subtitle { font-size: 13px; color: #b9bcc5; }
.pm-step { 
    padding: 4px 10px; 
    border-radius: 999px; 
    font-size: 12px;
    border: 1px solid rgba(255,255,255,0.12);
}

/* 说明卡片 */
.pm-info-card {
    background: #1c273a;
    padding: 20px;
    font-size: 14px;
}

/* 上传区域 */
.pm-card {
    padding: 14px 18px;
    background: #16181d;
}

/* 上传按钮外框 */
div[data-testid="stFileUploader"] > div:first-child {
    border: 1.5px dashed #555;
    background-color: #111;
    padding: 22px;
    border-radius: 12px;
}

/* 按钮 */
.stButton > button, .stDownloadButton > button {
    border-radius: 999px !important;
    background: #2563eb !important;
    border: 1px solid #1d4ed8 !important;
    color: white !important;
    padding: 10px 23px !important;
    font-size: 15px !important;
}
.stButton > button:hover, .stDownloadButton > button:hover {
    background: #1d4ed8 !important;
}

/* 表格容器固定宽度并居中 */
[data-testid="stDataFrame"] {
    max-width: 1100px;
    margin: auto;
}

/* 表格样式 */
[data-testid="stDataFrame"] table td,
[data-testid="stDataFrame"] table th {
    text-align: center !important;
    padding: 6px !important;
}
[data-testid="stDataFrame"] table thead tr th {
    background-color: #111827 !important;
}
[data-testid="stDataFrame"] tbody tr:hover {
    background-color: #111827 !important;
}
/* TOTAL 行样式 */
[data-testid="stDataFrame"] tbody tr:last-child td {
    font-weight: 700;
    background-color: #020617 !important;
    border-top: 1px solid #4b5563 !important;
}

/* 汇总居中展示 */
.pm-summary { text-align: center; margin-top: 6px; margin-bottom: 12px; }

/* ========== 隐藏 Streamlit 原生元素（最重要） ========== */
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
footer {visibility: hidden !important;}
[data-testid="stToolbar"] { display: none !important; }
button[kind="header"] { display: none !important; }
#stDecoration { display: none !important; }
[data-testid="stStatusWidget"] { display: none !important; }

</style>
""",
unsafe_allow_html=True)


# ========== 登录保护 ==========
def check_login():
    if "login_success" not in st.session_state:
        st.session_state["login_success"] = False

    def verify():
        if (st.session_state.input_user == st.secrets["admin_username"] and
            st.session_state.input_pwd == st.secrets["admin_password"]):
            st.session_state["login_success"] = True
        else:
            st.error("❌ 用户名或密码错误")

    if not st.session_state["login_success"]:
        st.markdown("<h3 style='text-align:center;margin-top:80px;'>📊 请登录系统</h3>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.text_input("用户名", key="input_user")
            st.text_input("密码", type="password", key="input_pwd")
            st.button("登录", on_click=verify)
        return False

    return True


# 执行登录检查
if not check_login():
    st.stop()


# ========== 页面主内容 ==========
st.markdown("""
<div class="pm-hero">
    <div class="pm-hero-icon">📦</div>
    <div>
        <div class="pm-hero-title">Peppermayo Manifest 归类工具</div>
        <div class="pm-hero-subtitle">上传 Manifest → 自动归类 → 导出 Excel</div>
    </div>
</div>
""", unsafe_allow_html=True)


# 说明卡片
st.markdown("""
<div class="pm-info-card">
<b>重要提醒：HS CODE 可能存在不准确情况，请务必人工复核！</b><br><br>
如出现相同 HS CODE 被用于不同品类，请优先检查件数较少的品类并手动修正。
<br><br>
⚠ 不同大类不能使用同一个 HS CODE！
</div>
""", unsafe_allow_html=True)


# 上传区域
st.markdown("""
<div class="pm-card">
  <div class="pm-section-title">📤 上传 Manifest 文件</div>
  <p>支持 Excel / CSV，系统会自动识别并分类。</p>
</div>
""", unsafe_allow_html=True)

uploaded = st.file_uploader("请上传 Manifest 文件", type=["xlsx","csv"])


# ========== 读取列函数 ==========
def get_col(df, names):
    lower = {col.lower(): col for col in df.columns}
    for name in names:
        if name.lower() in lower:
            return df[lower[name.lower()]]
    return None


# ========== 主处理函数 ==========
def process(file):
    try:
        if file.name.endswith(".csv"):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)
    except Exception as e:
        st.error(f"读取失败：{e}")
        return None

    df.columns = df.columns.str.strip()

    desc = get_col(df, ["Item Description","Goods Description","Description"])
    qty  = get_col(df, ["Unit","Qty","Pieces"])
    amt  = get_col(df, ["Amount","Item Value","Total Value"])
    hs   = get_col(df, ["HS CODE","Item HS Code"])

    if desc is None or qty is None or amt is None:
        st.error("❌ 缺少必要列，请检查表头")
        return None

    def cat(x):
        s = str(x).lower()
        if "dress" in s or "gown" in s: return "Dresses"
        if "swim" in s or "bikini" in s: return "Swimwear"
        if any(k in s for k in ["top","shirt","blouse","tee"]): return "Tops"
        if any(k in s for k in ["jacket","coat","blazer"]): return "Outerwear"
        if any(k in s for k in ["pant","jean","skirt","short"]): return "Bottoms"
        return "Accessories"

    df["Category"] = desc.apply(cat)
    df["Qty"] = pd.to_numeric(qty, errors="coerce").fillna(0)
    df["Amt"] = pd.to_numeric(amt, errors="coerce").fillna(0)
    df["Origin"] = "CN"

    if hs is not None:
        df["HS_Code"] = hs.fillna("").astype(str).str.replace(r"\.0$", "", regex=True)
    else:
        df["HS_Code"] = ""

    summary = df.groupby("Category").agg({
        "HS_Code":"first",
        "Qty":"sum",
        "Amt":"sum",
        "Origin":"first"
    }).reset_index()

    summary.rename(columns={
        "Category":"Goods of Description",
        "HS_Code":"HS CODE",
        "Qty":"Unit",
        "Amt":"Amount",
        "Origin":"Country of origin"
    }, inplace=True)

    total = pd.DataFrame([{
        "Goods of Description":"TOTAL",
        "HS CODE":"",
        "Unit":summary["Unit"].sum(),
        "Amount":summary["Amount"].sum(),
        "Country of origin":""
    }])

    summary = pd.concat([summary,total], ignore_index=True)
    summary.insert(0,"No.","")
    summary.loc[:-1,"No."] = range(1,len(summary))

    return summary


# ========== 主流程 ==========
if uploaded:
    st.info(f"正在处理：{uploaded.name}")

    df = process(uploaded)

    if df is not None:
        total_qty = df.loc[df["Goods of Description"]=="TOTAL","Unit"].iloc[0]
        total_amt = df.loc[df["Goods of Description"]=="TOTAL","Amount"].iloc[0]

        st.markdown(f"""
        <div class="pm-summary">
            <div style="font-size:16px;font-weight:600;">📊 本次汇总概览</div>
            <div style="font-size:13px;color:#ccc;">
                共 <b>{len(df)-1}</b> 个分类，总数量 <b>{int(total_qty)}</b> 件，总金额 <b>{total_amt:,.2f}</b>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.dataframe(df, hide_index=True, use_container_width=True)

        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Invoice")

        st.download_button(
            "📥 点击下载 Excel",
            buffer.getvalue(),
            file_name=f"DONE_{uploaded.name}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )


# 底部提示
st.markdown(
    "<div style='text-align:center;color:#777;font-size:11px;'>本工具仅限内部使用，请勿外传</div>",
    unsafe_allow_html=True
)
