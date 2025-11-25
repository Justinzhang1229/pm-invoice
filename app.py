 (cd "$(git rev-parse --show-toplevel)" && git apply --3way <<'EOF' 
diff --git a/app.py b/app.py
index 1be976e557f08f3a0b0176c954dcaecc145812f8..9c351113b05ffa5cf0aa3e1fed60207f4c74c755 100644
--- a/app.py
+++ b/app.py
@@ -63,124 +63,177 @@ st.markdown("---")
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
 
 def process_data(file):
     # 读取文件
     try:
         if file.name.lower().endswith('.csv'):
             try:
                 df = pd.read_csv(file, encoding='utf-8')
-            except:
+            except Exception:
                 df = pd.read_csv(file, encoding='ISO-8859-1')
         else:
             df = pd.read_excel(file)
     except Exception as e:
         st.error(f"读取失败: {e}")
-        return None
+        return None, []
+
+    diagnostics = []
 
     # 寻找列名
     def get_col(df, candidates):
         for col in candidates:
-            if col in df.columns: return df[col]
-        return None
+            if col in df.columns:
+                return df[col], col
+        return None, None
 
-    desc_col = get_col(df, ['Item Description', 'Goods Description', 'Description', 'Goods of Description'])
-    qty_col = get_col(df, ['Unit', 'Item Quantity', 'Qty', 'Pieces'])
-    amt_col = get_col(df, ['Amount', 'Item Value', 'Total Value'])
-    hs_col = get_col(df, ['HS CODE', 'Item HS Code'])
-    origin_col = get_col(df, ['Country Of Origin', 'Country of origin', 'Origin'])
+    desc_col, desc_name = get_col(df, ['Item Description', 'Goods Description', 'Description', 'Goods of Description'])
+    qty_col, qty_name = get_col(df, ['Unit', 'Item Quantity', 'Qty', 'Pieces'])
+    amt_col, amt_name = get_col(df, ['Amount', 'Item Value', 'Total Value'])
+    hs_col, hs_name = get_col(df, ['HS CODE', 'Item HS Code'])
+    origin_col, origin_name = get_col(df, ['Country Of Origin', 'Country of origin', 'Origin'])
 
     if desc_col is None:
         st.error("❌ 错误：找不到‘产品描述’列，请检查表格表头！")
-        return None
+        return None, diagnostics
 
     # 归类逻辑 (Tops 优先)
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
-    df['Qty'] = pd.to_numeric(qty_col, errors='coerce').fillna(0)
-    df['Amt'] = pd.to_numeric(amt_col, errors='coerce').fillna(0)
-    df['Origin'] = origin_col.fillna('CN') if origin_col is not None else 'CN'
+
+    if qty_col is None:
+        st.error("❌ 未找到数量列，请补充准确件数后重新上传（清关申报不可为 0）。")
+        return None, diagnostics
+    else:
+        qty_numeric = pd.to_numeric(qty_col, errors='coerce')
+        invalid_qty_mask = qty_numeric.isna()
+        invalid_qty = int(invalid_qty_mask.sum())
+        if invalid_qty:
+            error_rows = ', '.join(map(str, (df.index[invalid_qty_mask] + 2).tolist()))
+            st.error(
+                f"❌ 发现 {invalid_qty} 行数量缺失或无法转换为数字（行号：{error_rows}），"
+                "请修正原文件后重新上传（清关申报不可为 0）。"
+            )
+            return None, diagnostics
+        df['Qty'] = qty_numeric
+
+    if amt_col is None:
+        st.error("❌ 未找到金额列，请补充准确金额后重新上传（清关申报不可为 0）。")
+        return None, diagnostics
+    else:
+        amt_numeric = pd.to_numeric(amt_col, errors='coerce')
+        invalid_amt_mask = amt_numeric.isna()
+        invalid_amt = int(invalid_amt_mask.sum())
+        if invalid_amt:
+            error_rows = ', '.join(map(str, (df.index[invalid_amt_mask] + 2).tolist()))
+            st.error(
+                f"❌ 发现 {invalid_amt} 行金额缺失或无法转换为数字（行号：{error_rows}），"
+                "请修正原文件后重新上传（清关申报不可为 0）。"
+            )
+            return None, diagnostics
+        df['Amt'] = amt_numeric
+
+    # 产地一律设为 CN（覆盖原始数据），提醒用户确认
+    df['Origin'] = 'CN'
+    diagnostics.append("所有产地已统一设为 CN，请确认后如有需要在原文件中修改后再上传。")
     
     # 修复 HS Code (转字符串 + 去除 .0)
     if hs_col is not None:
         df['HS_Code'] = hs_col.astype(str).str.replace(r'\.0$', '', regex=True).replace('nan', '')
     else:
+        diagnostics.append("未找到 HS CODE 列，已默认留空，建议补充或检查清关要求。")
         df['HS_Code'] = ''
 
     # 智能 HS Code 选择 (优先找 0000 结尾)
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
-    
-    return summary
+
+    # 数据质量提示
+    empty_desc = int(df[desc_name].isna().sum()) if desc_name else 0
+    if empty_desc:
+        diagnostics.append(f"有 {empty_desc} 行产品描述为空，可能导致分类不准确。")
+
+    accessories_count = int((df['Category'] == 'Accessories').sum())
+    if accessories_count:
+        diagnostics.append(
+            f"有 {accessories_count} 行被归为 Accessories（兜底分类），建议检查描述以提升分类精度。"
+        )
+
+    return summary, diagnostics
 
 # 主界面逻辑
 if uploaded_file is not None:
     st.write("🔄 正在处理...")
-    result_df = process_data(uploaded_file)
-    
+    result_df, diagnostics = process_data(uploaded_file)
+
     if result_df is not None:
         st.success("✅ 处理完成！拿走！不谢！")
         st.dataframe(result_df, use_container_width=True)
-        
+
+        if diagnostics:
+            st.subheader("🔍 数据质量检查")
+            for tip in diagnostics:
+                st.info(f"• {tip}")
+
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
 
EOF
)
