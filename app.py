import streamlit as st
import geopandas as gpd
import simplekml
import os
from io import BytesIO
import zipfile

# Initialize a dictionary to keep track of ID counts
id_count = {}


def shp_to_kml(shp_path, output_dir):
    """
    Convert a shapefile into KML files and save them in the output directory.
    """
    try:
        # Read the shapefile into a GeoDataFrame
        data = gpd.read_file(shp_path)
        
        # Check and reproject the CRS if necessary
        if data.crs.to_string() != 'EPSG:4326':
            data = data.to_crs(epsg=4326)
        
        # Iterate over each row of the GeoDataFrame
        for index, row in data.iterrows():
            kml = simplekml.Kml()
            polygon = kml.newpolygon(name=str(row['ID']))
            polygon.outerboundaryis = [tuple(x) for x in list(row.geometry.exterior.coords)]
            
            if row['ID'] in id_count:
                id_count[row['ID']] += 1
                kml_path = os.path.join(output_dir, f"ID_{row['ID']}_{id_count[row['ID']] - 1}.kml")
            else:
                id_count[row['ID']] = 1
                kml_path = os.path.join(output_dir, f"ID_{row['ID']}.kml")
            
            kml.save(kml_path)
        
        return True
    except KeyError:
        st.error("Please check if the 'ID' field (case-sensitive) exists in the shapefile.")
    return False


# Streamlit app layout
st.title("Shapefile to KML Converter")
st.write("Upload all files associated with a shapefile (e.g., .shp, .shx, .dbf, .prj), and download the converted KML files.")

# File uploader
uploaded_files = st.file_uploader(
    "Upload Shapefile Components",
    type=["shp", "shx", "dbf", "prj"],
    accept_multiple_files=True
)

# Submit button
if st.button("Convert to KML"):
    if uploaded_files:
        # Create a temporary directory to save the uploaded files
        temp_dir = "temp_shp"
        os.makedirs(temp_dir, exist_ok=True)
        
        # Save all uploaded files locally
        for uploaded_file in uploaded_files:
            file_path = os.path.join(temp_dir, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
        
        # Find the main .shp file in the uploaded files
        shp_file = next((f for f in uploaded_files if f.name.endswith(".shp")), None)
        
        if shp_file:
            shp_path = os.path.join(temp_dir, shp_file.name)
            
            # Output directory for KML files
            output_dir = os.path.join(temp_dir, "kml_output")
            os.makedirs(output_dir, exist_ok=True)
            
            # Call the conversion function
            success = shp_to_kml(shp_path, output_dir)
            
            if success:
                # Create a ZIP file for download
                zip_buffer = BytesIO()
                with zipfile.ZipFile(zip_buffer, "w") as zf:
                    for file_name in os.listdir(output_dir):
                        file_path = os.path.join(output_dir, file_name)
                        zf.write(file_path, file_name)

                # Provide the ZIP file for download
                st.download_button(
                    label="Download KML Files",
                    data=zip_buffer.getvalue(),
                    file_name="kml_files.zip",
                    mime="application/zip",
                )
            else:
                st.error("An error occurred during conversion.")
        else:
            st.error("No .shp file found in the uploaded files.")
        
        # Clean up the temporary directory
        for file_name in os.listdir(temp_dir):
            os.remove(os.path.join(temp_dir, file_name))
        os.rmdir(temp_dir)
    else:
        st.error("Please upload all shapefile components.")
