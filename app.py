import streamlit as st
import pandas as pd
import io

# ========== 基本配置 ==========
st.set_page_config(
    page_title="Peppermayo Manifest 归类工具",
    page_icon="📦",
    layout="wide",
)

# ========== 全局样式（自适配 1080p / 4K + SaaS 风格） ==========
st.markdown("""
<style>
/* 居中 + 最大宽度：适配 1080p / 2K / 4K */
.block-container {
    max-width: 1200px !important;
    margin-left: auto !important;
    margin-right: auto !important;
    padding-top: 2rem !important;
    padding-bottom: 2rem !important;
}

/* 深色背景稍微做一点渐变 */
body {
    background: radial-gradient(circle at top left, #20232a 0, #111 45%, #050505 100%);
}

/* 全局字体稍微大一点，适配高分屏 */
html, body, [class*="css"] {
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", system-ui, sans-serif;
    font-size: 15px;
}

/* 标题美化 */
h1 {
    font-weight: 700 !important;
    letter-spacing: 0.02em;
}
.pm-stepbar {
    font-size: 15px;
    margin-top: 4px;
    margin-bottom: 12px;
    padding: 8px 12px;
    border-radius: 999px;
    border: 1px solid rgba(255,255,255,0.08);
    background: rgba(0,0,0,0.35);
}

/* 蓝色说明卡片（内容完全不变，只改样式） */
.pm-info-card {
    background: #1c273a;
    padding: 20px 22px;
    border-radius: 12px;
    border: 1px solid rgba(255,255,255,0.10);
    font-size: 14px;
    line-height: 1.65;
    color: #e6eefc;
    box-shadow: 0px 6px 18px rgba(0,0,0,0.35);
    margin-top: 10px;
    margin-bottom: 24px;
}
.pm-info-card b {
    color: #ffffff;
}

/* 通用卡片 */
.pm-card {
    border-radius: 14px;
    padding: 14px 18px;
    background: #16181d;
    border: 1px solid rgba(255,255,255,0.06);
    box-shadow: 0 10px 30px rgba(0,0,0,0.4);
    margin-bottom: 18px;
}

/* 小标题 */
.pm-section-title {
    font-size: 15px;
    font-weight: 600;
    margin-bottom: 6px;
}

/* 上传控件美化 */
div[data-testid="stFileUploader"] > div:first-child {
    border: 1.5px dashed #555;
    background-color: #111;
    padding: 22px;
    border-radius: 12px;
}

/* 下载按钮放大一点 */
.stDownloadButton button {
    padding: 10px 24px !important;
    font-size: 15px !important;
    border-radius: 999px !important;
    font-weight: 600 !important;
}

/* DataFrame 圆角 */
.dataframe {
    border-radius: 12px !important;
    overflow: hidden !important;
}
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
            st.error("❌ 用户名或密码错误")

    if not st.session_state["login_success"]:
        st.markdown(
            "<h3 style='margin-bottom:4px;'>🔒 请先登录</h3>"
            "<p style='color:#aaaaaa;font-size:13px;margin-top:0;'>仅限内部同事使用，请输入账号密码。</p>",
            unsafe_allow_html=True,
        )
        st.markdown("---")
        c1, c2 = st.columns([1, 2])
        with c1:
            st.image("https://img.icons8.com/color/96/microsoft-excel-2019--v1.png", width=80)
        with c2:
            st.text_input("👤 用户名", key="input_user")
            st.text_input("🔑 密码", type="password", key="input_password")
            st.button("登录", on_click=verify_login, type="primary")
        return False

    return True

if not check_login():
    st.stop()

# ========== 顶部标题（内容保持不变） ==========
st.title("📦 Peppermayo Manifest 归类工具")

st.markdown(
    """
<div class="pm-stepbar">
📤 <b>步骤：</b> 上传 Manifest → 自动归类 → 下载/预览结果文件
</div>
""",
    unsafe_allow_html=True,
)

st.markdown("---")

# ========== HS CODE 提示（内容完全不变） ==========
st.markdown(
    """
<div class="pm-info-card">
💡 <b>重要提醒：HS CODE（海关编码）可能存在不准确的情况</b><br><br>
由于源文件内的海关编码并非总是精确，请特别注意：<br><br>
如果在导出的文件中发现 <b>同一个 HS CODE 被用于不同的产品大类</b>，请务必进行如下人工检查：<br><br>
1. <b>优先检查件数较少的品类；</b><br>
2. <b>将其 HS CODE 替换为正确且独立的编码；</b><br><br>
⚠️ <b>请务必遵守：不同产品大类不能使用同一个 HS CODE！</b><br>
如发现编码重叠，请及时核查与调整，以避免造成清关或申报问题。
</div>
""",
    unsafe_allow_html=True,
)

# ========== 上传区域 ==========
st.markdown(
    """
<div class="pm-card">
  <div class="pm-section-title">📤 请把 Manifest (Excel/CSV) 拖到下方区域或点击右侧按钮上传</div>
  <p style="font-size:13px;color:#aaaaaa;margin-top:2px;margin-bottom:6px;">
    支持 Excel (.xlsx) / CSV，系统会自动识别表头并生成汇总 Invoice。
  </p>
</div>
""",
    unsafe_allow_html=True,
)

uploaded_file = st.file_uploader(
    "📂 请把 Manifest (Excel/CSV) 拖到这里或点击Browse files上传",
    type=["xlsx", "csv"],
)

# ========== 列匹配工具函数 ==========
def get_col(df, candidates):
    """
    在 df 中寻找列：
    - 忽略大小写
    - 忽略前后空格
    找到后返回该列（Series），找不到返回 None
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
        if file.name.lower().endswith(".csv"):
            try:
                df = pd.read_csv(file, encoding="utf-8")
            except Exception:
                df = pd.read_csv(file, encoding="ISO-8859-1")
        else:
            df = pd.read_excel(file, engine="openpyxl")
    except Exception as e:
        st.error(f"读取失败: {e}")
        return None

    # 去掉列名两侧空格
    df.columns = df.columns.str.strip()

    # 寻找列名
    desc_col = get_col(df, ["Item Description", "Goods Description", "Description", "Goods of Description"])
    qty_col = get_col(df, ["Unit", "Item Quantity", "Qty", "Pieces"])
    amt_col = get_col(df, ["Amount", "Item Value", "Total Value"])
    hs_col = get_col(df, ["HS CODE", "Item HS Code"])
    origin_col = get_col(df, ["Country Of Origin", "Country of origin", "Origin"])  # 目前不用，只为以后扩展预留

    if desc_col is None:
        st.error(
            "❌ 错误：找不到‘产品描述’列，请检查表格表头！"
            "(例如：Item Description / Goods Description / Description / Goods of Description)"
        )
        return None

    # 必填列检查
    missing_cols_msg = []
    if qty_col is None:
        missing_cols_msg.append("数量列（Unit / Item Quantity / Qty / Pieces）")
    if amt_col is None:
        missing_cols_msg.append("金额列（Amount / Item Value / Total Value）")

    if missing_cols_msg:
        st.error(
            "❌ 错误：找不到以下必填列，请检查源文件表头后重新上传：\n- "
            + "\n- ".join(missing_cols_msg)
        )
        return None

    # ===== 空值检测 + 非数字检测 =====

    # 原始字符串（去空格）
    qty_str = qty_col.astype(str).str.strip()
    amt_str = amt_col.astype(str).str.strip()

    # ① 缺失检测：NaN 或 空字符串
    missing_mask = (
        qty_col.isna()
        | amt_col.isna()
        | qty_str.eq("")
        | amt_str.eq("")
    )

    if missing_mask.any():
        excel_rows = (df.index[missing_mask] + 2).tolist()
        if len(excel_rows) > 20:
            display_rows = excel_rows[:20]
            row_str = ", ".join(map(str, display_rows)) + f" ……（共 {len(excel_rows)} 行有数量/金额为空）"
        else:
            row_str = ", ".join(map(str, excel_rows))

        st.error(
            "❌ 错误：检测到有行的【数量】或【金额】为空（包括空单元格或只有空格），"
            "请先在源文件中补全后再重新上传。\n\n"
            f"示例问题行（Excel 行号）：{row_str}"
        )
        return None

    # ② 非数字检测
    qty_numeric = pd.to_numeric(qty_col, errors="coerce")
    amt_numeric = pd.to_numeric(amt_col, errors="coerce")

    invalid_qty_mask = qty_str.ne("") & qty_str.notna() & qty_numeric.isna()
    invalid_amt_mask = amt_str.ne("") & amt_str.notna() & amt_numeric.isna()
    invalid_mask = invalid_qty_mask | invalid_amt_mask

    if invalid_mask.any():
        excel_rows = (df.index[invalid_mask] + 2).tolist()
        if len(excel_rows) > 20:
            display_rows = excel_rows[:20]
            row_str = ", ".join(map(str, display_rows)) + f" ……（共 {len(excel_rows)} 行存在非数字的数量/金额）"
        else:
            row_str = ", ".join(map(str, excel_rows))

        st.error(
            "❌ 错误：检测到有行的【数量】或【金额】为非数字（例如：字母、符号、N/A 等），"
            "请先在源文件中改为数字后再重新上传。\n\n"
            f"示例问题行（Excel 行号）：{row_str}"
        )
        return None

    # ===== 分类逻辑（保持你原来的规则） =====
    def categorize(x):
        s = str(x).lower()
        if "dress" in s or "gown" in s:
            return "Dresses"
        if "bikini" in s or "swim" in s or "one piece" in s or "sarong" in s:
            return "Swimwear"
        if any(k in s for k in ["top", "shirt", "blouse", "cami", "bodysuit", "tee", "tank", "vest", "corset"]):
            return "Tops"
        if any(k in s for k in ["jacket", "coat", "blazer", "trench", "bomber", "cardigan", "sweater", "hoodie", "knit", "jumper"]):
            return "Outerwear"
        if any(k in s for k in ["skirt", "jeans", "pant", "trouser", "short", "skort", "bottom"]):
            return "Bottoms"
        if any(k in s for k in ["shoe", "heel", "boot", "sandal", "sneaker", "flat", "mule", "slide"]):
            return "Shoes"
        if "set" in s or "coord" in s:
            return "Outerwear"
        return "Accessories"

    df["Category"] = desc_col.apply(categorize)

    # 使用已经验证过的 numeric
    df["Qty"] = qty_numeric.fillna(0)
    df["Amt"] = amt_numeric.fillna(0)

    # 原产地全部 CN
    df["Origin"] = "CN"

    # HS CODE 保持你原来的规则
    if hs_col is not None:
        df["HS_Code"] = (
            hs_col.astype(str)
            .str.replace(r"\.0$", "", regex=True)
            .replace("nan", "")
        )
    else:
        df["HS_Code"] = ""

    # HS CODE 选择策略
    def select_best_hscode(series):
        valid_codes = [c for c in series if c and str(c).strip() != ""]
        if not valid_codes:
            return ""
        zeros_codes = [c for c in valid_codes if str(c).endswith("0000")]
        if zeros_codes:
            return pd.Series(zeros_codes).mode()[0]
        return pd.Series(valid_codes).mode()[0]

    # 汇总
    summary = (
        df.groupby("Category")
        .agg(
            {
                "HS_Code": select_best_hscode,
                "Qty": "sum",
                "Amt": "sum",
                "Origin": "first",
            }
        )
        .reset_index()
    )

    summary.columns = ["Goods of Description", "HS CODE", "Unit", "Amount", "Country of origin"]

    # TOTAL 行
    total_row = pd.DataFrame(
        [
            {
                "Goods of Description": "TOTAL",
                "HS CODE": "",
                "Unit": summary["Unit"].sum(),
                "Amount": summary["Amount"].sum(),
                "Country of origin": "",
            }
        ]
    )
    summary = pd.concat([summary, total_row], ignore_index=True)

    return summary

# ========== 主逻辑：上传后处理 ==========

if uploaded_file is not None:
    st.write("🔄 正在处理...")
    result_df = process_data(uploaded_file)

    if result_df is not None:
        st.success("✅ 处理完成！拿走！不谢！")
        st.dataframe(result_df, use_container_width=True)

        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            result_df.to_excel(writer, index=False, sheet_name="Invoice")

        st.download_button(
            label="📥 点击下载处理好的 Excel",
            data=buffer.getvalue(),
            file_name=f"[DONE]_{uploaded_file.name.split('.')[0]}.xlsx",
            mime="application/vnd.ms-excel",
            type="primary",
        )
