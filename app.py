import streamlit as st
import geopandas as gpd
import simplekml
import os
import tempfile
from io import BytesIO
import zipfile

st.sidebar.title("Aidash image team assistant")
st.sidebar.header("Environment selection")
options = st.sidebar.radio("Choose a page:", ["Shapefile to kml", "Shapefile to feature ZIP"])
if options=="Shapefile to kml":
    # Streamlit app layout
    st.title("Shapefile to KML Converter")
    st.write(
        "Upload all files associated with a shapefile (e.g., .shp, .shx, .dbf, .prj), and download the converted KML files."
    )

    # File uploader
    uploaded_files = st.file_uploader(
        "Upload Shapefile Components",
        type=["shp", "shx", "dbf", "prj"],
        accept_multiple_files=True,
    )

    # Shapefile to KML conversion function
    def shp_to_kml(shp_path, output_dir, field_name):
        try:
            id_count = {}
            # Read the shapefile into a GeoDataFrame
            data = gpd.read_file(shp_path)
            
            # Ensure CRS is WGS84 (EPSG:4326)
            if data.crs is None or data.crs.to_string() != "EPSG:4326":
                data = data.to_crs(epsg=4326)
            
            # Generate KML files
            for _, row in data.iterrows():
                kml = simplekml.Kml()
                polygon = kml.newpolygon(name=str(row[field_name]))
                polygon.outerboundaryis = [
                    tuple(coord) for coord in row.geometry.exterior.coords
                ]
                if row[field_name] in id_count:
                    id_count[row[field_name]] += 1
                    kml.save(os.path.join(output_dir, f"ID_{row[field_name]}_{(id_count[row[field_name]])-1}.kml"))
                else:
                    id_count[row[field_name]] = 1
                    kml.save(os.path.join(output_dir, f"ID_{row[field_name]}.kml"))

            return True
        except Exception as e:
            st.error(f"Error during conversion: {e}")
            return False

    if uploaded_files:
        try:
            # Create a temporary directory for uploaded files and output
            with tempfile.TemporaryDirectory() as temp_dir:
                # Save uploaded files to the temporary directory
                for uploaded_file in uploaded_files:
                    file_path = os.path.join(temp_dir,uploaded_file.name)
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                # Locate the main .shp file
                shp_file = next(
                    (f for f in uploaded_files if f.name.endswith(".shp")),None
                )
                if shp_file:
                    shp_path = os.path.join(temp_dir,shp_file.name)
                    # Output directory for KML files
                    output_dir = os.path.join(temp_dir, "kml_output")
                    os.makedirs(output_dir, exist_ok=True)
                    shape = gpd.read_file(shp_path)
                    columns = list(shape.columns)
                    # Take the naming field from user
                    field=st.selectbox("Choose a field for naming:",columns[:-1])
                    if field:
                        if st.button("Convert to KML"):
                            # Convert shapefile to kml
                            if shp_to_kml(shp_path, output_dir, field):
                                # Create a ZIP archive for download
                                zip_buffer = BytesIO()
                                with zipfile.ZipFile(zip_buffer, "w") as zf:
                                    for file_name in os.listdir(output_dir):
                                         zf.write(
                                              os.path.join(output_dir, file_name),file_name
                                         )
                                # Provide the ZIP file for download
                                st.download_button(
                                    label="Download KML Files",
                                    data=zip_buffer.getvalue(),
                                    file_name="kml_files.zip",
                                    mime="application/zip",
                                )
                            else:
                                 st.error("KML conversion failed.")
                else:
                    st.error("Please upload all shapefile components.")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

if options == "Shapefile to feature ZIP":
    # Streamlit app layout
    st.title("Shapefile to Feature ZIP Converter")
    st.write(
        "Upload all files associated with a shapefile (e.g., .shp, .shx, .dbf, .prj), and download the zipped shapefiles for each feature."
    )

    # File uploader
    uploaded_files = st.file_uploader(
        "Upload Shapefile Components",
        type=["shp", "shx", "dbf", "prj"],
        accept_multiple_files=True,
    )

    # Shapefile to individual feature ZIP conversion function
    def shp_to_feature_zip(shp_path, output_dir):
        try:
            # Read the shapefile into a GeoDataFrame
            data = gpd.read_file(shp_path)

            # Ensure CRS is set
            if data.crs is None:
                st.error("The shapefile must have a valid CRS.")
                return False

            # Check if 'ID' field exists
            if "ID" not in data.columns:
                st.error("The shapefile must have an 'ID' field.")
                return False

            # Generate individual shapefiles and ZIP them
            for idx, row in data.iterrows():
                output_file = os.path.join(output_dir, f"{row['ID']}.shp")
                feature = gpd.GeoDataFrame([row], crs=data.crs)
                feature.to_file(output_file)

                # Create a ZIP file for each feature
                zip_file_path = os.path.join(output_dir, f"{row['ID']}.zip")
                with zipfile.ZipFile(zip_file_path, "w") as zipf:
                    for ext in [".shp", ".cpg", ".dbf", ".prj", ".shx"]:
                        file_path = os.path.splitext(output_file)[0] + ext
                        if os.path.exists(file_path):
                            zipf.write(file_path, os.path.basename(file_path))

            return True
        except Exception as e:
            st.error(f"Error during conversion: {e}")
            return False

    # Submit button
    if st.button("Convert to Feature ZIP"):
        if uploaded_files:
            try:
                # Create a temporary directory for uploaded files and output
                with tempfile.TemporaryDirectory() as temp_dir:
                    # Save uploaded files to the temporary directory
                    for uploaded_file in uploaded_files:
                        file_path = os.path.join(temp_dir, uploaded_file.name)
                        with open(file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())

                    # Locate the main .shp file
                    shp_file = next(
                        (f for f in uploaded_files if f.name.endswith(".shp")), None
                    )

                    if shp_file:
                        shp_path = os.path.join(temp_dir, shp_file.name)

                        # Output directory for feature ZIP files
                        output_dir = os.path.join(temp_dir, "feature_output")
                        os.makedirs(output_dir, exist_ok=True)

                        # Convert Shapefile to feature ZIPs
                        if shp_to_feature_zip(shp_path, output_dir):
                            # Create a ZIP archive for download
                            zip_buffer = BytesIO()
                            with zipfile.ZipFile(zip_buffer, "w") as zf:
                                for file_name in os.listdir(output_dir):
                                    if file_name.endswith(".zip"):
                                        zf.write(
                                            os.path.join(output_dir, file_name),
                                            file_name,
                                        )

                            # Provide the ZIP file for download
                            st.download_button(
                                label="Download Feature ZIP Files",
                                data=zip_buffer.getvalue(),
                                file_name="feature_zips.zip",
                                mime="application/zip",
                            )
                        else:
                            st.error("Feature ZIP conversion failed.")
                    else:
                        st.error("No .shp file found among the uploaded files.")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")
        else:
            st.error("Please upload all shapefile components.")
