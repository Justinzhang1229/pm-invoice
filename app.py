import streamlit as st
import pandas as pd
import io

# 1. 设置网页配置
st.set_page_config(page_title="Peppermayo 数据归类", page_icon="📊")

# ===== 全局 CSS =====
st.markdown("""
<style>
/* 限制页面宽度 */
.block-container {
    max-width: 1200px !important;
    padding-top: 2rem;
}

/* 顶部说明卡片 */
.pm-info-card {
    background: #1c273a;
    padding: 20px 22px;
    border-radius: 12px;
    border: 1px solid rgba(255,255,255,0.10);
    font-size: 14px;
    line-height: 1.6;
    color: #e6eefc;
    box-shadow: 0 6px 18px rgba(0,0,0,0.35);
    margin-bottom: 25px;
}
.pm-info-card b {
    color: white;
}

/* 上传区域标题 */
.pm-section-title {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 6px;
}
</style>
""", unsafe_allow_html=True)

# -------- 登录模块 --------
def check_login():
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
            st.error("❌ 用户名或密码错误")

    if not st.session_state["login_success"]:
        st.markdown("## 🔒 请登录系统")
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

# ===== 主体内容 =====

st.title("📦 Peppermayo Manifest 归类工具")
st.markdown("### 📤 步骤：上传 Manifest → 自动归类 → 下载/预览结果文件")
st.markdown("---")

# 顶部说明卡片（内容不变）
st.markdown("""
<div class="pm-info-card">
💡 <b>重要提醒：HS CODE（海关编码）可能存在不准确的情况</b><br><br>
由于源文件内的海关编码并非总是精确，请特别注意：<br><br>
如果在导出的文件中发现 <b>同一个 HS CODE 被用于不同的产品大类</b>，请务必进行如下人工检查：<br><br>
1. <b>优先检查件数较少的品类；</b><br>
2. <b>将其 HS CODE 替换为正确且独立的编码；</b><br><br>

⚠️ <b>请务必遵守：不同产品大类不能使用同一个 HS CODE！</b><br>
如发现编码重叠，请及时核查与调整，以避免造成清关或申报问题。
</div>
""", unsafe_allow_html=True)

# 文件上传
uploaded_file = st.file_uploader("📂 请把 Manifest (Excel/CSV) 拖到这里或点击Browse files上传", type=['xlsx', 'csv'])


# ===== 列名匹配函数 =====
def get_col(df, candidates):
    norm_map = {col.strip().lower(): col for col in df.columns}
    for cand in candidates:
        key = cand.strip().lower()
        if key in norm_map:
            return df[norm_map[key]], norm_map[key]
    return None, None


# ===== 主数据处理逻辑 =====
def process_data(file):
    try:
        if file.name.lower().endswith('.csv'):
            try:
                df = pd.read_csv(file, encoding='utf-8')
            except:
                df = pd.read_csv(file, encoding='ISO-8859-1')
        else:
            df = pd.read_excel(file)
    except Exception as e:
        st.error(f"读取失败: {e}")
        return None

    df.columns = df.columns.str.strip()

    desc_col, desc_name = get_col(df, ['Item Description', 'Goods Description', 'Description', 'Goods of Description'])
    qty_col, qty_name = get_col(df, ['Unit', 'Item Quantity', 'Qty', 'Pieces'])
    amt_col, amt_name = get_col(df, ['Amount', 'Item Value', 'Total Value'])
    hs_col, hs_name = get_col(df, ['HS CODE', 'Item HS Code'])
    origin_col, origin_name = get_col(df, ['Country Of Origin', 'Country of origin', 'Origin'])

    if desc_col is None:
        st.error("❌ 错误：找不到‘产品描述’列，请检查表头！")
        return None

    missing = []
    if qty_col is None:
        missing.append("数量列（Unit / Item Quantity / Qty / Pieces）")
    if amt_col is None:
        missing.append("金额列（Amount / Item Value / Total Value）")
    if missing:
        st.error("❌ 错误：缺少必填列：\n- " + "\n- ".join(missing))
        return None

    # 空值检测
    missing_mask = qty_col.isna() | amt_col.isna()
    if missing_mask.any():
        excel_rows = (df.index[missing_mask] + 2).tolist()
        if len(excel_rows) > 20:
            row_str = ", ".join(map(str, excel_rows[:20])) + f" ……（共 {len(excel_rows)} 行有问题）"
        else:
            row_str = ", ".join(map(str, excel_rows))
        st.error(f"❌ 检测到数量/金额为空，请修复源文件后再上传。\n问题行：{row_str}")
        return None

    # 分类逻辑
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
    df['Qty'] = pd.to_numeric(qty_col, errors='coerce').fillna(0)
    df['Amt'] = pd.to_numeric(amt_col, errors='coerce').fillna(0)
    df['Origin'] = 'CN'

    if hs_col is not None:
        df['HS_Code'] = hs_col.astype(str).str.replace(r'\.0$', '', regex=True).replace('nan', '')
    else:
        df['HS_Code'] = ''

    def select_best_hscode(series):
        valid = [c for c in series if c and str(c).strip() != ""]
        if not valid: return ""
        zeros = [c for c in valid if str(c).endswith("0000")]
        base = zeros if zeros else valid
        return pd.Series(base).mode()[0]

    summary = df.groupby('Category').agg({
        'HS_Code': select_best_hscode,
        'Qty': 'sum',
        'Amt': 'sum',
        'Origin': 'first'
    }).reset_index()

    summary.columns = ['Goods of Description', 'HS CODE', 'Unit', 'Amount', 'Country of origin']

    total_row = pd.DataFrame([{
        'Goods of Description': 'TOTAL',
        'HS CODE': '',
        'Unit': summary['Unit'].sum(),
        'Amount': summary['Amount'].sum(),
        'Country of origin': ''
    }])

    return pd.concat([summary, total_row], ignore_index=True)


# ===== 上传文件触发处理 =====
if uploaded_file is not None:
    st.write("🔄 正在处理...")
    result_df = process_data(uploaded_file)

    if result_df is not None:

        # ⭐ 文件摘要
        st.info(
            f"📄 当前文件：`{uploaded_file.name}` ｜ "
            f"检测到 {len(result_df) - 1} 个商品分类（不含 TOTAL）"
        )

        st.success("✅ 处理完成！拿走！不谢！")

        # ⭐ 汇总概览
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

        # 导出 Excel
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            result_df.to_excel(writer, index=False, sheet_name='Invoice')

        st.download_button(
            label="⬇️ 点击下载处理好的 Excel",
            data=buffer.getvalue(),
            file_name=f"[DONE]_{uploaded_file.name.split('.')[0]}.xlsx",
            mime="application/vnd.ms-excel",
            type="primary"
        )

# ===== 内部声明 =====
st.markdown(
    """
    <p style="font-size:11px;color:#555;margin-top:30px;text-align:center;opacity:0.6;">
    本工具仅供 Wiseway 内部使用，请勿对外分享链接。
    </p>
    """,
    unsafe_allow_html=True
)
