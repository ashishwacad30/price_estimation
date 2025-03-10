import os
import pandas as pd
import json
import time
import re
import streamlit as st
from io import BytesIO
from langchain_groq import ChatGroq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
llm = ChatGroq(model="llama-3.3-70b-versatile", api_key=GROQ_API_KEY)

# Streamlit Page Configuration
st.set_page_config(page_title="Parts Price Calculator", layout="wide")

# Add Logo (Replace 'logo.jpg' with your actual file name)
logo_path = r"/Users/ashish/urban_rez/price_estimation/Screenshot 2025-03-10 at 8.34.30 PM.png"
if os.path.exists(logo_path):
    st.image(logo_path, width=150)  # Adjust width as needed

# Streamlit App Title
st.title("🔧 Parts Price Calculator")

# File Uploader
uploaded_file = st.file_uploader("Upload an Excel file", type=["xlsx"])

def analyze_csv(file):
    df = pd.read_excel(file)

    # Convert DataFrame to string for LLM
    table_str = df.to_string(index=False)

    # Strict prompt for JSON output
    prompt = f"""
    You are an AI that analyzes a product pricing table and suggests the optimal price for a company.

    ### Instructions:
    - Consider **market price, company history, raw material cost, assembly cost, labor cost, overhead cost, complexity, material, and manufacturing process**.
    - Estimate **manufacturing time** in hours based on complexity, material, and process.
    - Return **only JSON**, formatted as:

    ```json
    [
        {{
            "part_name": "name of the part",
            "price_without_tax": 0.00,
            "price_with_tax": 0.00,
            "estimated_time(in hours)": 0.0
        }}
    ]
    ```

    **Do not include any explanations, footnotes, or comments. Only return the JSON.**

    ### **Product Data Table:**
    {table_str}
    """

    # Show Streamlit status messages before processing
    time.sleep(0.8)
    st.write("🤖 **Agent calculating estimated price without tax...**")
    time.sleep(0.8)
    st.write("💰 **Agent calculating price estimated with tax...**")
    time.sleep(0.8)
    st.write("⏳ **Agent calculating estimated time in hours...**")

    response = llm.invoke(prompt)
    response_text = response.content  # Extract text from AIMessage

    # Extract JSON using regex
    match = re.search(r"\[.*\]", response_text, re.DOTALL)
    if match:
        response_text = match.group(0)  # Extract only JSON
    else:
        st.error("Error: No valid JSON found in response.")
        return None

    # Convert response to DataFrame
    try:
        recommended_data = json.loads(response_text)
    except json.JSONDecodeError as e:
        st.error(f"JSON Decode Error: {e}")
        return None

    recommended_df = pd.DataFrame(recommended_data)

    # Ensure column names match for merging
    if "part_name" not in df.columns:
        st.error("Error: 'part_name' column not found in Excel file.")
        return None

    # Merge new data with the original DataFrame
    df = df.merge(recommended_df, on="part_name", how="left")

    return df

# Process Button
if uploaded_file:
    if st.button("🔍 Process"):
        with st.spinner("Analyzing file..."):
            updated_df = analyze_csv(uploaded_file)

            if updated_df is not None:
                # Display DataFrame in Streamlit
                st.success("✅ Analysis Complete!")
                st.dataframe(updated_df)

                # Convert DataFrame to Excel for download
                output = BytesIO()
                with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                    updated_df.to_excel(writer, index=False)
                output.seek(0)

                # Provide Download Button
                st.download_button(
                    label="📥 Download Updated Excel",
                    data=output,
                    file_name="updated_parts_price.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
