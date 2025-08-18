import pandas as pd
import json
import re
from tqdm import tqdm

def extract_year(title):
    match = re.search(r"\((\d{4})\)$", title)
    return int(match.group(1)) if match else None

YEAR_THRESHOLD   = 2000
N_MOVIES_PER_TAG = 20

selected_tags = pd.read_excel("data/label_selection.xlsx")["English Label"].to_list()
tagdl_df      = pd.read_csv("data/tagdl.csv")

item_to_title = {}
with open("data/metadata_updated.json", 'r', encoding='utf-8') as f:
    for line in f:
        movie = json.loads(line)
        item_to_title[movie['item_id']] = movie['title']

metadata_df = pd.DataFrame([
    {"item_id": item_id, "title": title, "year": extract_year(title)}
    for item_id, title in item_to_title.items()
])

metadata_df = metadata_df.dropna(subset=["year"])

data = []
for tag in tqdm(selected_tags):
    read_df = tagdl_df[tagdl_df["tag"] == tag].copy()
    read_df = read_df.merge(metadata_df, on="item_id", how="left")
    read_df = read_df[read_df["year"] >= YEAR_THRESHOLD]
    read_df = read_df.sort_values(by="score", ascending=False).head(N_MOVIES_PER_TAG)
    
    data.append(read_df)

if data:
    final_df = pd.concat(data, ignore_index=True)
    final_df = final_df[["item_id", "title", "year", "tag", "score"]]
    final_df.to_csv("data/filtered_movies_by_tag.csv", index=False)
else:
    print("No data")