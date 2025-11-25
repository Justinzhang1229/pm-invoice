import streamlit as st
import pandas as pd
import io

# 1. 设置网页配置 (使用图表 Emoji 代表 Excel)
st.set_page_config(page_title="Peppermayo 数据归类", page_icon="📊")

# --- 🔐 登录保护功能 (开始) ---
def check_login():
    """检查用户名和密码"""
    # 初始化 session state
    if "login_success" not in st.session_state:
        st.session_state["login_success"] = False

    # 定义验证逻辑
    def verify_login():
        user = st.session_state.get("input_user", "")
        pwd = st.session_state.get("input_password", "")
        
        # 从 Streamlit Secrets 获取刚才设置的账号密码
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

    # 如果未登录，显示登录界面
    if not st.session_state["login_success"]:
        st.markdown("## 🔒 请登录系统")
        st.markdown("---")
        # 创建两列布局，让输入框好看一点
        c1, c2 = st.columns([1, 2])
        with c1:
            st.image("https://img.icons8.com/color/96/microsoft-excel-2019--v1.png", width=80)
        with c2:
            st.text_input("👤 用户名", key="input_user")
            st.text_input("🔑 密码", type="password", key="input_password")
            st.button("登录", on_click=verify_login, type="primary")
        return False
    
    return True

# 执行登录检查，如果没过就停止运行下面代码
if not check_login():
    st.stop()
# --- 🔐 登录保护功能 (结束) ---


# --- 📦 主程序功能 (开始) ---

st.title("📦 Peppermayo Manifest 归类工具")

st.markdown("### 📤 步骤：上传 Manifest → 自动归类 → 下载/预览结果文件")
st.markdown("---")

st.info("""
💡 **重要提醒：HS CODE（海关编码）可能存在不准确的情况**

由于源文件内的海关编码并非总是精确，请特别注意：

如果在导出的文件中发现 **同一个 HS CODE 被用于不同的产品大类**，请务必进行如下人工检查：

1. **优先检查件数较少的品类；**
2. **将其 HS CODE 替换为正确且独立的编码；**

⚠️ **请务必遵守：不同产品大类不能使用同一个 HS CODE！**
如发现编码重叠，请及时核查与调整，以避免造成清关或申报问题。
""")

st.markdown("---")

# 上传区域
uploaded_file = st.file_uploader("📂 请把 Manifest (Excel/CSV) 拖到这里或点击Browse files上传", type=['xlsx', 'csv'])

# ⭐ 修改过的列匹配函数：忽略大小写 + 去掉前后空格
def get_col(df, candidates):
    """
    在 df 中寻找列：
    - 忽略大小写
    - 忽略前后空格
    找到后返回该列（Series），找不到返回 None
    """
    # 构建「标准化列名」到「原始列名」的映射
    norm_map = {col.strip().lower(): col for col in df.columns}

    for cand in candidates:
        key = cand.strip().lower()
        if key in norm_map:
            return df[norm_map[key]]
    return None


def process_data(file):
    # 读取文件
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

    # ⭐ 去掉列名两侧空格，配合上面的 get_col 一起更稳
    df.columns = df.columns.str.strip()

    # 寻找列名
    desc_col = get_col(df, ['Item Description', 'Goods Description', 'Description', 'Goods of Description'])
    qty_col = get_col(df, ['Unit', 'Item Quantity', 'Qty', 'Pieces'])
    amt_col = get_col(df, ['Amount', 'Item Value', 'Total Value'])
    hs_col = get_col(df, ['HS CODE', 'Item HS Code'])
    origin_col = get_col(df, ['Country Of Origin', 'Country of origin', 'Origin'])

    if desc_col is None:
        st.error("❌ 错误：找不到‘产品描述’列，请检查表格表头！(例如：Item Description / Goods Description / Description / Goods of Description)")
        return None

    # ⭐ 新增：数量 / 金额列本身缺失（整个列都没有）
    missing_cols_msg = []
    if qty_col is None:
        missing_cols_msg.append("数量列（Unit / Item Quantity / Qty / Pieces）")
    if amt_col is None:
        missing_cols_msg.append("金额列（Amount / Item Value / Total Value）")

    if missing_cols_msg:
        st.error("❌ 错误：找不到以下必填列，请检查源文件表头后重新上传：\n- " + "\n- ".join(missing_cols_msg))
        return None

    # ⭐ 新增：检查每一行是否有数量/金额为空的情况
    # 这里用原始数据检查“空值”，再让用户修改源文件
    missing_mask = qty_col.isna() | amt_col.isna()
    if missing_mask.any():
        # Excel 一般是第 1 行是表头，所以行号 +2 更符合用户看到的行号
        excel_rows = (df.index[missing_mask] + 2).tolist()

        # 为了防止行号太多，把前 20 行列出来，其余给个统计数字
        if len(excel_rows) > 20:
            display_rows = excel_rows[:20]
            row_str = ", ".join(map(str, display_rows)) + f" ……（共 {len(excel_rows)} 行有问题）"
        else:
            row_str = ", ".join(map(str, excel_rows))

        st.error(
            "❌ 错误：检测到有行的【数量】或【金额】为空，请先修改源文件后再重新上传。\n\n"
            f"示例问题行（Excel 行号）：{row_str}"
        )
        return None

    # 归类逻辑 (Tops 优先) —— 按你原来的逻辑保持不动
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

    # 原来的逻辑：转数字，非法的当成 NaN 再填 0 —— 这里保持不变
    df['Qty'] = pd.to_numeric(qty_col, errors='coerce').fillna(0)
    df['Amt'] = pd.to_numeric(amt_col, errors='coerce').fillna(0)
    df['Origin'] = origin_col.fillna('CN') if origin_col is not None else 'CN'
    
    # HS CODE 这块你说先不动，也不改
    if hs_col is not None:
        df['HS_Code'] = hs_col.astype(str).str.replace(r'\.0$', '', regex=True).replace('nan', '')
    else:
        df['HS_Code'] = ''

    # 智能 HS Code 选择 (优先找 0000 结尾) —— 保持原来的逻辑
    def select_best_hscode(series):
        valid_codes = [c for c in series if c and str(c).strip() != '']
        if not valid_codes: return ''
        zeros_codes = [c for c in valid_codes if str(c).endswith('0000')]
        if zeros_codes: return pd.Series(zeros_codes).mode()[0]
        return pd.Series(valid_codes).mode()[0]

    # 汇总
    summary = df.groupby('Category').agg({
        'HS_Code': select_best_hscode,
        'Qty': 'sum',
        'Amt': 'sum',
        'Origin': 'first'
    }).reset_index()

    summary.columns = ['Goods of Description', 'HS CODE', 'Unit', 'Amount', 'Country of origin']

    # 添加合计行 (TOTAL)
    total_unit = summary['Unit'].sum()
    total_amount = summary['Amount'].sum()
    total_row = pd.DataFrame([{
        'Goods of Description': 'TOTAL',
        'HS CODE': '',
        'Unit': total_unit,
        'Amount': total_amount,
        'Country of origin': ''
    }])
    summary = pd.concat([summary, total_row], ignore_index=True)
    
    return summary

# 主界面逻辑
if uploaded_file is not None:
    st.write("🔄 正在处理...")
    result_df = process_data(uploaded_file)
    
    if result_df is not None:
        st.success("✅ 处理完成！拿走！不谢！")
        st.dataframe(result_df, use_container_width=True)
        
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
