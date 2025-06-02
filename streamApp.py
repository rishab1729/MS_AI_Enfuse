import streamlit as st
import os
import tempfile
import shutil
from zipfile import ZipFile
from enfuse import process_folder, process_folderY  # Your logic placed in a separate file
from pathlib import Path

def zip_folder(folder_path, zip_path):
    with ZipFile(zip_path, 'w') as zipf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, folder_path)
                zipf.write(file_path, arcname)

st.set_page_config(page_title="Image Blending App", layout="centered")
st.title("📸 RAW Image Blending Tool")

uploaded_zip = st.file_uploader("Upload a ZIP folder containing images", type="zip")

if uploaded_zip:
    with tempfile.TemporaryDirectory() as temp_dir:
        input_dir = os.path.join(temp_dir, "input")
        output_dir = os.path.join(temp_dir, "output")
        os.makedirs(input_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)

        # Save and extract uploaded zip
        zip_path = os.path.join(temp_dir, "uploaded.zip")
        with open(zip_path, "wb") as f:
            f.write(uploaded_zip.read())

        with ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(input_dir)

        st.success("Images extracted successfully. Processing...")

        # Call your image processing logic
        # result = process_folder(input_dir, output_dir)
        for status in process_folderY(input_dir, output_dir):
            st.success(f"Status: {status}")  # Or use st.write(status) in Streamlit for live updates
        
        # status_placeholder = st.empty()
        # for status in process_folderY(input_dir, output_dir):
        #     status_placeholder.write(f"Status: {status}")
        # Create output zip
        result_zip = os.path.join(temp_dir, "result.zip")
        zip_folder(output_dir, result_zip)

        st.success("✅ Processing complete!")
        st.download_button("Download Blended Images", open(result_zip, "rb"), file_name="blended_output.zip", mime="application/zip")
