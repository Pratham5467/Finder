import streamlit as st
import pandas as pd
import io

# Function to read uploaded file
def read_file(uploaded_file):
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, encoding='latin1', engine='python')
        elif uploaded_file.name.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(uploaded_file)
        else:
            st.error("Unsupported file format. Please upload a CSV or Excel file.")
            return None

        # Normalize column names
        df.columns = df.columns.str.strip().str.lower()
        st.success("File uploaded and data loaded successfully!")
        return df
    except Exception as e:
        st.error(f"Error reading file: {e}")
        return None

# Function to clean and preprocess the data
def preprocess_data(df):
    # Clean the 'qty' column to handle mixed data
    if 'qty (01.02.24)' in df.columns:
        df['qty (01.02.24)'] = df['qty (01.02.24)'].replace(r'\D+', '', regex=True).fillna(0).astype(int)

    # Fill missing values in key columns with placeholders
    for col in ['storage location', 'used location', 'capacity', 'type']:
        if col in df.columns:
            df[col] = df[col].fillna('Not Specified')

    return df

# Function to search products
def flexible_product_search(search_term, df, material_details_col, material_code_col):
    try:
        search_term = search_term.strip().lower()
        results = df[
            df[material_details_col].str.contains(search_term, case=False, na=False) |
            df[material_code_col].astype(str).str.contains(search_term, na=False)
        ]
        return results
    except Exception as e:
        st.error(f"Error in search: {e}")
        return pd.DataFrame()

# Streamlit app setup
st.title("Inventory Management System")

st.sidebar.subheader("Upload File")
uploaded_file = st.sidebar.file_uploader("Choose a CSV or Excel file", type=["csv", "xls", "xlsx"])

df_uploaded = None
material_details_col = None
material_code_col = None
qty_col = None
storage_location_col = None
used_location_col = None
capacity_col = None
type_col = None

if uploaded_file is not None:
    df_uploaded = read_file(uploaded_file)
    if df_uploaded is not None:
        df_uploaded = preprocess_data(df_uploaded)

        # Allow user to map the columns dynamically
        st.sidebar.subheader("Column Mapping")

        # Dynamically select columns for mapping
        all_columns = df_uploaded.columns.tolist()
        material_details_col = st.sidebar.selectbox("Select Material Details Column", all_columns)
        material_code_col = st.sidebar.selectbox("Select Material Code Column", all_columns)
        
        # Additional column mappings can be added if needed (e.g., qty, storage location, etc.)
        qty_col = st.sidebar.selectbox("Select Quantity Column", all_columns)
        storage_location_col = st.sidebar.selectbox("Select Storage Location Column", all_columns)
        used_location_col = st.sidebar.selectbox("Select Used Location Column", all_columns)
        capacity_col = st.sidebar.selectbox("Select Capacity Column", all_columns)
        type_col = st.sidebar.selectbox("Select Type Column", all_columns)

page = st.sidebar.selectbox("Select Operation", ["Search & Analyze", "Add New Product", "Update Product", "Delete Product"])

# Search & Analyze Page
if page == "Search & Analyze":
    st.subheader("Search Products in Uploaded File")
    if df_uploaded is not None and material_details_col and material_code_col:
        search_term = st.text_input("Enter product name or material code")

        if search_term:
            results = flexible_product_search(search_term, df_uploaded, material_details_col, material_code_col)

            if not results.empty:
                st.write(f"Found {len(results)} result(s).")
                st.write(results)
            else:
                st.warning("No products found in the uploaded file.")
    else:
        st.warning("Please upload a file and map the columns to search.")

# Add New Product Page
elif page == "Add New Product":
    st.subheader("Add New Product")

    if df_uploaded is not None and material_details_col and material_code_col:
        with st.form("add_product_form"):
            material_details = st.text_input("Material Details")
            material_code = st.text_input("Material Code")
            qty = st.number_input("Initial Quantity", min_value=0)
            storage_location = st.text_input("Storage Location")
            used_location = st.text_input("Used Location")
            capacity = st.number_input("Capacity", min_value=0)
            type_ = st.text_input("Type")

            submitted = st.form_submit_button("Add Product")

        if submitted:
            if material_code in df_uploaded[material_code_col].astype(str).values:
                st.error("Product with this material code already exists!")
            else:
                new_product = pd.DataFrame({
                    material_code_col: [material_code],
                    material_details_col: [material_details],
                    qty_col: [qty],
                    storage_location_col: [storage_location],
                    used_location_col: [used_location],
                    capacity_col: [capacity],
                    type_col: [type_]
                })

                df_uploaded = pd.concat([df_uploaded, new_product], ignore_index=True)
                st.success("Product added successfully!")

                # Provide a download button for the updated file
                towrite = io.BytesIO()
                with pd.ExcelWriter(towrite, engine="xlsxwriter") as writer:
                    df_uploaded.to_excel(writer, index=False, sheet_name="Sheet1")
                towrite.seek(0)

                st.download_button(
                    label="Download Updated File",
                    data=towrite,
                    file_name="updated_inventory.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
    else:
        st.warning("Please upload a file and map the columns to add a product.")

# Update Product Page
elif page == "Update Product":
    st.subheader("Update Product")

    if df_uploaded is not None and material_details_col and material_code_col:
        search_term = st.text_input("Search for product to update")
        
        if search_term:
            results = flexible_product_search(search_term, df_uploaded, material_details_col, material_code_col)

            if not results.empty:
                product_options = [f"{row[material_details_col]} ({row[material_code_col]})" for idx, row in results.iterrows()]
                selected_product = st.selectbox("Select Product to Update", product_options)

                if selected_product:
                    selected_idx = product_options.index(selected_product)
                    product_data = results.iloc[selected_idx]

                    with st.form("update_product_form"):
                        new_name = st.text_input("Material Details", value=product_data[material_details_col])
                        new_qty = st.number_input("Quantity", value=int(product_data[qty_col]), min_value=0)
                        new_storage_location = st.text_input("Storage Location", value=product_data[storage_location_col])
                        new_used_location = st.text_input("Used Location", value=product_data[used_location_col])
                        new_capacity = st.number_input("Capacity", value=int(product_data[capacity_col]), min_value=0)
                        new_type = st.text_input("Type", value=product_data[type_col])

                        update_submitted = st.form_submit_button("Update Product")

                    if update_submitted:
                        df_uploaded.at[product_data.name, material_details_col] = new_name
                        df_uploaded.at[product_data.name, qty_col] = new_qty
                        df_uploaded.at[product_data.name, storage_location_col] = new_storage_location
                        df_uploaded.at[product_data.name, used_location_col] = new_used_location
                        df_uploaded.at[product_data.name, capacity_col] = new_capacity
                        df_uploaded.at[product_data.name, type_col] = new_type

                        st.success("Product updated successfully!")

                        # Provide a download button for the updated file
                        towrite = io.BytesIO()
                        with pd.ExcelWriter(towrite, engine="xlsxwriter") as writer:
                            df_uploaded.to_excel(writer, index=False, sheet_name="Sheet1")
                        towrite.seek(0)

                        st.download_button(
                            label="Download Updated File",
                            data=towrite,
                            file_name="updated_inventory.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
            else:
                st.warning("No matching products found.")
    else:
        st.warning("Please upload a file and map the columns to update a product.")

# Delete Product Page
elif page == "Delete Product":
    st.subheader("Delete Product")

    if df_uploaded is not None and material_details_col and material_code_col:
        search_term = st.text_input("Search for product to delete")
        
        if search_term:
            results = flexible_product_search(search_term, df_uploaded, material_details_col, material_code_col)

            if not results.empty:
                product_options = [f"{row[material_details_col]} ({row[material_code_col]})" for idx, row in results.iterrows()]
                selected_product = st.selectbox("Select Product to Delete", product_options)

                if selected_product:
                    selected_idx = product_options.index(selected_product)
                    product_data = results.iloc[selected_idx]

                    st.warning(f"Are you sure you want to delete {product_data[material_details_col]}?")
                    if st.button("Yes, Delete Product"):
                        df_uploaded = df_uploaded.drop(product_data.name)
                        st.success("Product deleted successfully!")

                        # Provide a download button for the updated file
                        towrite = io.BytesIO()
                        with pd.ExcelWriter(towrite, engine="xlsxwriter") as writer:
                            df_uploaded.to_excel(writer, index=False, sheet_name="Sheet1")
                        towrite.seek(0)

                        st.download_button(
                            label="Download Updated File",
                            data=towrite,
                            file_name="updated_inventory.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
            else:
                st.warning("No matching products found.")
