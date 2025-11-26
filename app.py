import streamlit as st
import pandas as pd
import io

# ========== 基本配置 ==========
st.set_page_config(
    page_title="Peppermayo 数据归类",
    page_icon="📊",
    layout="wide",
)

# ========== 全局样式（统一阴影/圆角/间距 + 登录页 + 表格 hover） ==========
st.markdown("""
<style>
/* ===== 布局：居中 + 最大宽度，适配 1080p / 2K / 4K ===== */
.block-container {
    max-width: 1320px !important;
    margin-left: auto !important;
    margin-right: auto !important;
    padding-top: 2rem !important;
    padding-bottom: 2rem !important;
}

/* 深色渐变背景 */
body {
    background: radial-gradient(circle at top left, #20232a 0, #111 45%, #050505 100%);
}

/* 全局字体微调，适配高分屏 */
html, body, [class*="css"] {
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", system-ui, sans-serif;
    font-size: 15px;
}

/* ========== 统一卡片风格：圆角 / 阴影 / 间距 ========== */
.pm-hero,
.pm-info-card,
.pm-card {
    border-radius: 16px;
    border: 1px solid rgba(255,255,255,0.06);
    box-shadow: 0 16px 40px rgba(0,0,0,0.45);
    margin-bottom: 24px;
}

/* ===== 顶部 Hero 区 ===== */
.pm-hero {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 20px 26px;
    background: linear-gradient(135deg, #20232a 0, #15171c 100%);
}
.pm-hero-icon {
    font-size: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 56px;
    height: 56px;
    border-radius: 16px;
    background: rgba(255,255,255,0.06);
}
.pm-hero-title {
    font-size: 24px;
    font-weight: 650;
}
.pm-hero-subtitle {
    font-size: 13px;
    color: #b9bcc5;
    margin-top: 3px;
}
.pm-hero-steps {
    margin-top: 8px;
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 6px;
    font-size: 12px;
}
.pm-step {
    padding: 4px 10px;
    border-radius: 999px;
    border: 1px solid rgba(255,255,255,0.12);
    background: rgba(0,0,0,0.35);
}
.pm-step-active {
    border-color: #ffb347;
    background: rgba(255,179,71,0.16);
    color: #ffd798;
}
.pm-step-arrow {
    opacity: 0.55;
}

/* ===== 顶部说明卡片 ===== */
.pm-info-card {
    background: #1c273a;
    padding: 20px 22px;
    font-size: 14px;
    line-height: 1.65;
    color: #e6eefc;
}
.pm-info-card b {
    color: #ffffff;
}

/* ===== 通用内容卡片（上传区域等） ===== */
.pm-card {
    padding: 14px 18px;
    background: #16181d;
}
.pm-section-title {
    font-size: 15px;
    font-weight: 600;
    margin-bottom: 6px;
}
.pm-card p {
    color: rgba(255,255,255,0.70) !important;
    font-size: 13px;
}

/* ===== 上传控件美化 ===== */
div[data-testid="stFileUploader"] > div:first-child {
    border: 1.5px dashed #555;
    background-color: #111;
    padding: 22px;
    border-radius: 12px;
}

/* ===== 下载按钮：蓝色主按钮风格 ===== */
.stDownloadButton button {
    padding: 10px 24px !important;
    font-size: 15px !important;
    border-radius: 999px !important;
    font-weight: 600 !important;
    background: #2563eb !important;       /* 主蓝 */
    border: 1px solid #1d4ed8 !important;  /* 深一点的蓝 */
    color: #ffffff !important;
}
.stDownloadButton button:hover {
    background: #1d4ed8 !important;
    border-color: #1d4ed8 !important;
}

/* ===== 提示条（st.info / st.success）精致化 ===== */
div[data-testid="stNotification"] {
    border-radius: 10px !important;
    padding-top: 6px !important;
    padding-bottom: 6px !important;
    box-shadow: 0 8px 20px rgba(0,0,0,0.35) !important;
    font-size: 14px !important;
}
div[data-testid="stNotification"] p {
    margin-bottom: 0 !important;
}

/* ===== DataFrame 统一视觉 + 居中 + hover 高亮 ===== */
[data-testid="stDataFrame"] table {
    border-radius: 12px;
    overflow: hidden;
    border-collapse: collapse !important;
}

[data-testid="stDataFrame"] table td,
[data-testid="stDataFrame"] table th {
    text-align: center !important;          /* 所有列居中 */
    padding-top: 6px;
    padding-bottom: 6px;
}

/* 表头背景统一 */
[data-testid="stDataFrame"] thead tr th {
    background-color: #111827 !important;
    border-bottom: 1px solid #374151 !important;
}

/* 行 hover 高亮 */
[data-testid="stDataFrame"] tbody tr:hover {
    background-color: #111827 !important;
}

/* TOTAL 行加粗 */
[data-testid="stDataFrame"] tbody tr:last-child td {
    font-weight: 600 !important;
}

/* ===== 登录卡片：玻璃效果 + 淡入动画 ===== */
.login-card {
    width: 480px;
    max-width: 94vw;
    margin: 96px auto 40px auto;
    padding: 28px 32px 24px 32px;
    background: rgba(18,20,25,0.86);
    border-radius: 18px;
    border: 1px solid rgba(255,255,255,0.10);
    box-shadow: 0 24px 60px rgba(0,0,0,0.80);
    backdrop-filter: blur(18px);
    -webkit-backdrop-filter: blur(18px);
}

.fade-in-up {
    animation: fadeInUp 0.45s ease-out;
}

@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(10px); }
    to   { opacity: 1; transform: translateY(0); }
}

.login-title {
    font-size: 20px;
    font-weight: 650;
    margin-bottom: 4px;
}
.login-subtitle {
    font-size: 13px;
    color: #a0a0a0;
    margin-bottom: 22px;
}
.login-icon {
    font-size: 32px;
    margin-bottom: 10px;
}

/* 登录区域中的输入框/按钮全宽 */
.login-card [data-testid="stTextInput"] > div > div {
    width: 100% !important;
}
.login-card [data-testid="stTextInput"] {
    margin-bottom: 10px;
}
.login-card .stButton button {
    width: 100%;
    padding: 9px 0 !important;
    font-size: 15px !important;
    border-radius: 999px !important;
    background: #2563eb !important;
    border: 1px solid #1d4ed8 !important;
}
.login-card .stButton button:hover {
    background: #1d4ed8 !important;
    border-color: #1d4ed8 !important;
}

/* 登录页在手机上更紧凑一点 */
@media (max-width: 640px) {
    .login-card {
        margin-top: 48px;
        padding: 22px 18px 20px 18px;
    }
}

/* =====（可选）隐藏 Streamlit 默认菜单/页脚，让界面更像独立系统 ===== */
/*
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
*/
</style>
""", unsafe_allow_html=True)

# ========== 登录保护 ==========
def check_login():
    """检查用户名和密码"""

    if "login_success" not in st.session_state:
        st.session_state["login_success"] = False

    def verify_login():
        user = st.session_state.get("input_user", "")
        pwd = st.session_state.get("input_password", "")

        if "admin_username" in st.secrets and "admin_password" in st.secrets:
            correct_user = st.secrets["admin_username"]
            correct_pwd = st.secrets["admin_password"]
        else:
            st.error("⚠️ 系统未配置密码，请联系管理员在 Secrets 中设置！")
            return

        if user == correct_user and pwd == correct_pwd:
            st.session_state["login_success"] = True
        else:
            st.session_state["login_success"] = False
            st.error("❌ 用户名或密码错误，请重试。")

    # 未登录：显示登录卡片
    if not st.session_state["login_success"]:
        with st.container():
            st.markdown(
                """
                <div class="login-card fade-in-up">
                    <div class="login-icon">📊</div>
                    <div class="login-title">请登录系统</div>
                    <div class="login-subtitle">仅限内部同事使用，请输入用户名和密码继续。</div>
                """,
                unsafe_allow_html=True,
            )

            st.text_input("👤 用户名", key="input_user")
            st.text_input("🔑 密码", type="password", key="input_password")

            st.button("登录", on_click=verify_login)

            st.markdown("</div>", unsafe_allow_html=True)

        return False

    return True


# 执行登录检查，如果没过就停止运行下面代码
if not check_login():
    st.stop()

# ========== 主界面（已登录） ==========

# 顶部 Hero
st.markdown("""
<div class="pm-hero">
  <div class="pm-hero-icon">📦</div>
  <div>
    <div class="pm-hero-title">Peppermayo Manifest 归类工具</div>
    <div class="pm-hero-subtitle">上传 Manifest → 自动归类 → 导出数据（含合计行）</div>
    <div class="pm-hero-steps">
      <span class="pm-step pm-step-active">① 上传 Manifest 文件</span>
      <span class="pm-step-arrow">→</span>
      <span class="pm-step">② 系统自动归类 + 汇总</span>
      <span class="pm-step-arrow">→</span>
      <span class="pm-step">③ 预览 / 下载 Excel</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# HS CODE 说明
st.markdown("""
<div class="pm-info-card">
💡 <b>重要提醒：HS CODE源文件数据可能存在不准确的情况</b><br><br>
由于源文件内的海关编码并非总是精确，请特别注意：<br><br>
如果在导出的文件中发现 <b>同一个 HS CODE 被用于不同的产品大类</b>，请务必进行如下人工检查：<br><br>
1. <b>优先检查件数较少的品类；</b><br>
2. <b>将其 HS CODE 替换为正确且独立的编码；</b><br><br>
⚠️ <b>请务必遵守：不同产品大类不能使用同一个 HS CODE！</b><br>
如发现编码重复使用在不同产品大类上，请及时核查与调整，以避免造成清关或申报问题。
</div>
""", unsafe_allow_html=True)

# 上传区域卡片
st.markdown("""
<div class="pm-card">
  <div class="pm-section-title">📤 上传 Manifest 文件</div>
  <p>
    支持 Excel (.xlsx) / CSV，系统会自动识别数据并生成分类汇总数据。
  </p>
</div>
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "📂 请把 Manifest (Excel/CSV) 拖到这里或点击Browse files上传文件",
    type=['xlsx', 'csv']
)

# ========== 列匹配工具函数 ==========
def get_col(df, candidates):
    """
    在 df 中寻找列（忽略大小写和两侧空格），返回 Series 或 None
    """
    norm_map = {col.strip().lower(): col for col in df.columns}
    for cand in candidates:
        key = cand.strip().lower()
        if key in norm_map:
            return df[norm_map[key]]
    return None

# ========== 核心处理函数 ==========
def process_data(file):
    # 读取文件
    try:
        if file.name.lower().endswith('.csv'):
            try:
                df = pd.read_csv(file, encoding='utf-8')
            except Exception:
                df = pd.read_csv(file, encoding='ISO-8859-1')
        else:
            df = pd.read_excel(file, engine='openpyxl')
    except Exception as e:
        st.error(f"读取失败: {e}")
        return None

    # 去掉列名空格
    df.columns = df.columns.str.strip()

    # 找关键列
    desc_col = get_col(df, ['Item Description', 'Goods Description', 'Description', 'Goods of Description'])
    qty_col  = get_col(df, ['Unit', 'Item Quantity', 'Qty', 'Pieces'])
    amt_col  = get_col(df, ['Amount', 'Item Value', 'Total Value'])
    hs_col   = get_col(df, ['HS CODE', 'Item HS Code'])
    origin_col = get_col(df, ['Country Of Origin', 'Country of origin', 'Origin'])

    if desc_col is None:
        st.error("❌ 错误：找不到‘产品描述’列，请检查表格表头！（例如：Item Description / Goods Description / Description / Goods of Description）")
        return None

    # 必填列存在性检查
    missing_cols_msg = []
    if qty_col is None:
        missing_cols_msg.append("数量列（Unit / Item Quantity / Qty / Pieces）")
    if amt_col is None:
        missing_cols_msg.append("金额列（Amount / Item Value / Total Value）")
    if missing_cols_msg:
        st.error("❌ 错误：找不到以下必填列，请检查源文件表头后重新上传：\n- " + "\n- ".join(missing_cols_msg))
        return None

    # ==== 空值 + 非数字检测 ====
    qty_str = qty_col.astype(str).str.strip()
    amt_str = amt_col.astype(str).str.strip()

    # ① 空值（NaN 或 空字符串）
    missing_mask = (
        qty_col.isna()
        | amt_col.isna()
        | qty_str.eq("")
        | amt_str.eq("")
    )
    if missing_mask.any():
        excel_rows = (df.index[missing_mask] + 2).tolist()
        if len(excel_rows) > 20:
            row_str = ", ".join(map(str, excel_rows[:20])) + f" ……（共 {len(excel_rows)} 行有数量/金额为空）"
        else:
            row_str = ", ".join(map(str, excel_rows))
        st.error(
            "❌ 错误：检测到有行的【数量】或【金额】为空（包括空单元格或只有空格），"
            "请先在源文件中补全后再重新上传。\n\n"
            f"示例问题行（Excel 行号）：{row_str}"
        )
        return None

    # ② 非数字检测
    qty_numeric = pd.to_numeric(qty_col, errors='coerce')
    amt_numeric = pd.to_numeric(amt_col, errors='coerce')

    invalid_qty_mask = qty_str.ne("") & qty_str.notna() & qty_numeric.isna()
    invalid_amt_mask = amt_str.ne("") & amt_str.notna() & amt_numeric.isna()
    invalid_mask = invalid_qty_mask | invalid_amt_mask

    if invalid_mask.any():
        excel_rows = (df.index[invalid_mask] + 2).tolist()
        if len(excel_rows) > 20:
            row_str = ", ".join(map(str, excel_rows[:20])) + f" ……（共 {len(excel_rows)} 行存在非数字的数量/金额）"
        else:
            row_str = ", ".join(map(str, excel_rows))
        st.error(
            "❌ 错误：检测到有行的【数量】或【金额】为非数字（例如：字母、符号、N/A 等），"
            "请先在源文件中改为数字后再重新上传。\n\n"
            f"示例问题行（Excel 行号）：{row_str}"
        )
        return None

    # ==== 分类逻辑（保持原规则） ====
    def categorize(x):
        s = str(x).lower()
        if 'dress' in s or 'gown' in s: return 'Dresses'
        if 'bikini' in s or 'swim' in s or 'one piece' in s or 'sarong' in s: return 'Swimwear'
        if any(k in s for k in ['top', 'shirt', 'blouse', 'cami', 'bodysuit', 'tee', 'tank', 'vest', 'corset']): return 'Tops'
        if any(k in s for k in ['jacket', 'coat', 'blazer', 'trench', 'bomber', 'cardigan', 'sweater', 'hoodie', 'knit', 'jumper']): return 'Outerwear'
        if any(k in s for k in ['skirt', 'jeans', 'pant', 'trouser', 'short', 'skort', 'bottom']): return 'Bottoms'
        if any(k in s for k in ['shoe', 'heel', 'boot', 'sandal', 'sneaker', 'flat', 'mule', 'slide']): return 'Shoes'
        if 'set' in s or 'coord' in s: return 'Outerwear'
        return 'Accessories'

    df['Category'] = desc_col.apply(categorize)
    df['Qty'] = qty_numeric.fillna(0)
    df['Amt'] = amt_numeric.fillna(0)
    df['Origin'] = 'CN'  # 默认全部 CN

    # HS CODE 处理
    if hs_col is not None:
        df['HS_Code'] = hs_col.astype(str).str.replace(r'\.0$', '', regex=True).replace('nan', '')
    else:
        df['HS_Code'] = ''

    # HS CODE 选择策略
    def select_best_hscode(series):
        valid_codes = [c for c in series if c and str(c).strip() != ""]
        if not valid_codes:
            return ''
        zeros_codes = [c for c in valid_codes if str(c).endswith('0000')]
        if zeros_codes:
            return pd.Series(zeros_codes).mode()[0]
        return pd.Series(valid_codes).mode()[0]

    # 汇总
    summary = df.groupby('Category').agg({
        'HS_Code': select_best_hscode,
        'Qty': 'sum',
        'Amt': 'sum',
        'Origin': 'first'
    }).reset_index()

    summary.columns = ['Goods of Description', 'HS CODE', 'Unit', 'Amount', 'Country of origin']

    # TOTAL 行
    total_row = pd.DataFrame([{
        'Goods of Description': 'TOTAL',
        'HS CODE': '',
        'Unit': summary['Unit'].sum(),
        'Amount': summary['Amount'].sum(),
        'Country of origin': ''
    }])
    summary = pd.concat([summary, total_row], ignore_index=True)

    return summary

# ========== 主流程 ==========
if uploaded_file is not None:
    st.write("🔄 正在处理 Manifest 文件，瞬间就会完成！✌️")
    result_df = process_data(uploaded_file)

    if result_df is not None:
        st.info(
            f"📄 当前文件：`{uploaded_file.name}` ｜ "
            f"检测到 {len(result_df) - 1} 个商品分类（不含 TOTAL）"
        )

        st.success("✅ 处理完成！拿走！不谢！")

        total_unit = result_df.loc[result_df["Goods of Description"] == "TOTAL", "Unit"].iloc[0]
        total_amount = result_df.loc[result_df["Goods of Description"] == "TOTAL", "Amount"].iloc[0]

        st.markdown(
            f"""
            <div style='margin-top:6px;margin-bottom:12px;'>
                <span style='font-size:16px;font-weight:600;'>📊 本次汇总概览</span><br>
                <span style='font-size:13px;color:#cccccc;'>
                    共 <b>{len(result_df) - 1}</b> 个分类，
                    总数量 <b>{int(total_unit)}</b> 件，
                    总金额约 <b>{total_amount:,.2f}</b>
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.dataframe(result_df, use_container_width=True)

        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            result_df.to_excel(writer, index=False, sheet_name='Invoice')

        st.download_button(
            label="📥 点击下载处理好的 Excel",
            data=buffer.getvalue(),
            file_name=f"[DONE]_{uploaded_file.name.split('.')[0]}.xlsx",
            mime="application/vnd.ms-excel",
            type="primary"
        )

# 底部说明
st.markdown(
    """
    <p style="font-size:11px;color:#777;margin-top:30px;text-align:center;opacity:0.8;">
    👿 本工具仅供战友们使用！请勿对外分享链接！😡
    </p>
    """,
    unsafe_allow_html=True
)
