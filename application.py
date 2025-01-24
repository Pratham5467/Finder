import streamlit as st
import pandas as pd
import io

def read_excel_file(uploaded_file):
    try:
        df = pd.read_excel(uploaded_file)
        df.columns = df.columns.str.strip().str.lower()
        
        if 'stock_level' not in df.columns:
            df['stock_level'] = 0
        
        st.success("File uploaded and data loaded successfully!")
        return df
    except Exception as e:
        st.error(f"Error reading file: {e}")
        return None

def flexible_product_search(search_term, df):
    """
    Search products by material code or name with flexible matching
    """
    try:
        search_term_int = int(search_term)
        code_results = df[df["material_code"] == search_term_int]
        if not code_results.empty:
            return code_results
    except ValueError:
        pass
    
    name_results = df[
        df["material details"].str.contains(search_term, case=False, na=False) |  
        df["material details"].str.lower() == search_term.lower()  
    ]
    
    return name_results

st.title("Inventory Management System")

st.sidebar.subheader("Upload Excel File")
uploaded_file = st.sidebar.file_uploader("Choose an Excel file", type=["xlsx"])

df_uploaded = None
if uploaded_file is not None:
    df_uploaded = read_excel_file(uploaded_file)

page = st.sidebar.selectbox("Select Operation", ["Search & Analyze", "Add New Product", "Update Product", "Delete Product"])

# Search & Analyze Page
if page == "Search & Analyze":
    st.subheader("Search Products in Uploaded File")
    if df_uploaded is not None:
        search_term = st.text_input("Enter product name or material code")

        if search_term:
            results = flexible_product_search(search_term, df_uploaded)

            if not results.empty:
                st.write(f"Found {len(results)} result(s).")
                st.write(results)
            else:
                st.warning("No products found in the uploaded file.")

    else:
        st.warning("Please upload a file to search.")

# Add New Product Page
elif page == "Add New Product":
    st.subheader("Add New Product")

    with st.form("add_product_form"):
        material_details = st.text_input("Material Details")
        material_code = st.text_input("Material Code")
        stock_level = st.number_input("Initial Stock Level", min_value=0)

        submitted = st.form_submit_button("Add Product")

    if submitted and df_uploaded is not None:
        df_uploaded.columns = df_uploaded.columns.str.strip().str.lower()
        
        if int(material_code) in df_uploaded["material_code"].values:
            st.error("Product with this material code already exists!")
        else:
            new_product = pd.DataFrame({
                "material_code": [int(material_code)],
                "material details": [material_details],
                "stock_level": [stock_level]
            })
            
            df_uploaded = pd.concat([df_uploaded, new_product], ignore_index=True)
            st.success("Product added successfully!")

            towrite = io.BytesIO()
            with pd.ExcelWriter(towrite, engine="xlsxwriter") as writer:
                df_uploaded.to_excel(writer, index=False, sheet_name="Sheet1")
            towrite.seek(0)

            st.download_button(
                label="Download Updated Excel File",
                data=towrite,
                file_name="updated_inventory.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

# Update Product Page
elif page == "Update Product":
    st.subheader("Update Product")

    search_term = st.text_input("Search for product to update")
    update_result = None

    if search_term:
        if df_uploaded is not None:
            df_uploaded.columns = df_uploaded.columns.str.strip().str.lower()

            results = flexible_product_search(search_term, df_uploaded)

            if not results.empty:
                product_options = [f"{r['material_details']} ({r['material_code']})" for idx, r in results.iterrows()]
                selected_product = st.selectbox("Select Product to Update", product_options)

                if selected_product:
                    selected_idx = product_options.index(selected_product)
                    product_data = results.iloc[selected_idx]

                    with st.form("update_product_form"):
                        new_name = st.text_input("Material Details", value=product_data['material_details'])
                        new_stock_level = st.number_input(
                            "Stock Level", 
                            value=int(product_data.get('stock_level', 0)), 
                            min_value=0
                        )

                        update_submitted = st.form_submit_button("Update Product")

                    if update_submitted:
                        df_uploaded.at[product_data.name, "material_details"] = new_name
                        df_uploaded.at[product_data.name, "stock_level"] = new_stock_level

                        st.success("Product updated successfully!")

                        towrite = io.BytesIO()
                        with pd.ExcelWriter(towrite, engine="xlsxwriter") as writer:
                            df_uploaded.to_excel(writer, index=False, sheet_name="Sheet1")
                        towrite.seek(0)

                        st.download_button(
                            label="Download Updated Excel File",
                            data=towrite,
                            file_name="updated_inventory.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
            else:
                st.warning("No matching products found.")

# Delete Product Page
elif page == "Delete Product":
    st.subheader("Delete Product")

    search_term = st.text_input("Search for product to delete")
    if search_term:
        if df_uploaded is not None:
            df_uploaded.columns = df_uploaded.columns.str.strip().str.lower()

            results = flexible_product_search(search_term, df_uploaded)

            if not results.empty:
                product_options = [f"{r['material_details']} ({r['material_code']})" for idx, r in results.iterrows()]
                selected_product = st.selectbox("Select Product to Delete", product_options)

                if selected_product:
                    selected_idx = product_options.index(selected_product)
                    product_data = results.iloc[selected_idx]

                    st.warning(f"Are you sure you want to delete {product_data['material_details']}?")
                    if st.button("Yes, Delete Product"):
                        df_uploaded = df_uploaded.drop(product_data.name)

                        st.success("Product deleted successfully!")

                        towrite = io.BytesIO()
                        with pd.ExcelWriter(towrite, engine="xlsxwriter") as writer:
                            df_uploaded.to_excel(writer, index=False, sheet_name="Sheet1")
                        towrite.seek(0)

                        st.download_button(
                            label="Download Updated Excel File",
                            data=towrite,
                            file_name="updated_inventory.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
            else:
                st.warning("No matching products found.")