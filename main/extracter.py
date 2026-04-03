import pandas as pd

# Load spreadsheet
file_path = "iavars_video_assets_dataset.xlsx"
df = pd.read_excel(file_path)

video_column = None

# # -------- Approach 1: Check column names --------
# keywords = ["video", "videos", "assets", "links", "link", "url", "urls", "asset", "media"]

# for col in df.columns:
#     col_lower = col.lower()
#     if any(keyword in col_lower for keyword in keywords):
#         video_column = col
#         print(f"Video column identified from column name: {video_column}")
#         break

# -------- Approach 2: Scan first 15 rows for URLs --------
if video_column is None:
    for col in df.columns:
        print("Columns: ", col)
        if df[col].astype(str).head(15).str.contains("http").any():
            video_column = col
            print(f"Video column identified by scanning cells: {video_column}")
            break

# -------- Extract links --------
video_links = []

if video_column:
    video_links = df[video_column].dropna().tolist()
    print("\nExtracted Links:")
    for link in video_links:
        print(link)
else:
    print("No video link column found.")