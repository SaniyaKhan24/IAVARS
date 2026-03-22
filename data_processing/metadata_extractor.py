def extract_data(df):
    data = []

    for _, row in df.iterrows():
        item = {
            "brand": str(row.get("Brand", "")).strip(),
            "campaign": str(row.get("Campaign", "")).strip(),
            "link": str(row.get("Video Link", "")).strip(),
        }
        data.append(item)

    return data