import streamlit as st
import pandas as pd
import io

# 设置网页配置
st.set_page_config(page_title="Peppermayo 自动发票助手", page_icon="📊")

# --- 🔐 密码保护功能开始 ---
def check_password():
    """检查密码是否正确"""
    if "password" not in st.secrets:
        st.error("⚠️ 未设置密码，请在 Streamlit Secrets 中配置！")
        return False

    def password_entered():
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # 不保存密码，只保存状态
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # 第一次打开，显示输入框
        st.text_input("🔒 请输入公司访问密码", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        # 密码错了，提示错误
        st.text_input("🔒 请输入公司访问密码", type="password", on_change=password_entered, key="password")
        st.error("❌ 密码错误，请重试")
        return False
    else:
        # 密码正确
        return True

if not check_password():
    st.stop()  # ⛔️ 密码不对，立刻停止运行下面的代码
# --- 🔐 密码保护功能结束 ---

# 下面是您原来的所有功能代码，不用动 #
st.title("🧾 Peppermayo 自动发票生成器")
st.markdown("### 上传 Manifest -> 自动归类 + 智能 HS Code -> 下载发票")
st.info("💡 提示：您的文件是在云端内存中处理的，处理完即刻销毁，不会保存任何数据，请放心使用。")
st.markdown("---")

# ... (此处省略您原来的 process_data 函数和逻辑，保持原样即可) ...
# 请把您原来 app.py 剩下的代码完整的接在这里
# 包括 uploaded_file = st.file_uploader(...) 及其后面的所有内容

uploaded_file = st.file_uploader("📂 请把 Manifest (Excel/CSV) 拖到这里", type=['xlsx', 'csv'])

def process_data(file):
    # ... (保持原来的函数内容不变) ...
    # 为了节省篇幅，这里不重复显示，请确保您原来的逻辑都在
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

    def get_col(df, candidates):
        for col in candidates:
            if col in df.columns: return df[col]
        return None

    desc_col = get_col(df, ['Item Description', 'Goods Description', 'Description', 'Goods of Description'])
    qty_col = get_col(df, ['Unit', 'Item Quantity', 'Qty', 'Pieces'])
    amt_col = get_col(df, ['Amount', 'Item Value', 'Total Value'])
    hs_col = get_col(df, ['HS CODE', 'Item HS Code'])
    origin_col = get_col(df, ['Country Of Origin', 'Country of origin', 'Origin'])

    if desc_col is None:
        st.error("❌ 错误：找不到‘产品描述’列，请检查表格表头！")
        return None

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
    df['Origin'] = origin_col.fillna('CN') if origin_col is not None else 'CN'
    
    if hs_col is not None:
        df['HS_Code'] = hs_col.astype(str).str.replace(r'\.0$', '', regex=True).replace('nan', '')
    else:
        df['HS_Code'] = ''

    def select_best_hscode(series):
        valid_codes = [c for c in series if c and str(c).strip() != '']
        if not valid_codes: return ''
        zeros_codes = [c for c in valid_codes if str(c).endswith('0000')]
        if zeros_codes: return pd.Series(zeros_codes).mode()[0]
        return pd.Series(valid_codes).mode()[0]

    summary = df.groupby('Category').agg({
        'HS_Code': select_best_hscode,
        'Qty': 'sum',
        'Amt': 'sum',
        'Origin': 'first'
    }).reset_index()

    summary.columns = ['Goods of Description', 'HS CODE', 'Unit', 'Amount', 'Country of origin']

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

if uploaded_file is not None:
    st.write("🔄 正在处理...")
    result_df = process_data(uploaded_file)
    
    if result_df is not None:
        st.success("✅ 处理完成！")
        st.dataframe(result_df, use_container_width=True)
        
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            result_df.to_excel(writer, index=False, sheet_name='Invoice')
            
        st.download_button(
            label="⬇️ 点击下载 Excel 文件",
            data=buffer.getvalue(),
            file_name=f"[DONE]_{uploaded_file.name.split('.')[0]}.xlsx",
            mime="application/vnd.ms-excel"
        )
