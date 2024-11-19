import streamlit as st
import geopandas as gpd
import simplekml
import os
import tempfile
from io import BytesIO
import zipfile

st.sidebar.title("Aidash image team assistant")
st.sidebar.header("Environment selection")
options = st.sidebar.radio("Choose a page:", ["Shapefile to kml", "Shapefile to feature ZIP", "AI assistant"])
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
    def shp_to_kml(shp_path, output_dir):
        try:
            # Read the shapefile into a GeoDataFrame
            data = gpd.read_file(shp_path)
            
            # Ensure CRS is WGS84 (EPSG:4326)
            if data.crs is None or data.crs.to_string() != "EPSG:4326":
                data = data.to_crs(epsg=4326)
            
            # Check if 'ID' field exists
            if "ID" not in data.columns:
                st.error("The shapefile must have an 'ID' field.")
                return False

            # Generate KML files
            for _, row in data.iterrows():
                kml = simplekml.Kml()
                polygon = kml.newpolygon(name=str(row["ID"]))
                polygon.outerboundaryis = [
                    tuple(coord) for coord in row.geometry.exterior.coords
                ]
                kml.save(os.path.join(output_dir, f"ID_{row['ID']}.kml"))

            return True
        except Exception as e:
            st.error(f"Error during conversion: {e}")
            return False


    # Submit button
    if st.button("Convert to KML"):
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

                        # Output directory for KML files
                        output_dir = os.path.join(temp_dir, "kml_output")
                        os.makedirs(output_dir, exist_ok=True)

                        # Convert Shapefile to KML
                        if shp_to_kml(shp_path, output_dir):
                            # Create a ZIP archive for download
                            zip_buffer = BytesIO()
                            with zipfile.ZipFile(zip_buffer, "w") as zf:
                                for file_name in os.listdir(output_dir):
                                    zf.write(
                                        os.path.join(output_dir, file_name), file_name
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
                        st.error("No .shp file found among the uploaded files.")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")
        else:
            st.error("Please upload all shapefile components.")

if options=="AI assistant":
    groq_api_key='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'
    llm=ChatGroq(model='Gemma2-9b-it',groq_api_key=groq_api_key)
    prompt=ChatPromptTemplate(
    [
        ("system","You are a helpful AI assitant. You have to reply to the user."),
        MessagesPlaceholder(variable_name="messege")
    ])
    parser=StrOutputParser()
    chain=prompt|llm|parser
    human=st.text_input("What's in your mind today?")
    response=chain.invoke(["messege",HumanMessage(content=human)])
    st.write(response)
