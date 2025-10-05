from fastapi import FastAPI
import json
import pandas as pd
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

@app.get("/locations")
def get_locations():
    with open("../openaq/transformed/locations.json") as f:
        return json.load(f)

@app.get("/locations/{location_id}")
def get_location_data(location_id: str):
    with open("../openaq/transformed/locations.json") as f:
        locations = json.load(f)

    if location_id not in locations:
        return {"error": "Location not found"}

    location = locations[location_id]
    files = location["files"]

    data = {}
    for file in files:
        parameter = file.split("_")[-1].split(".")[0]
        df = pd.read_csv(f"../openaq/transformed/{file}")
        data[parameter] = df.to_dict(orient="records")

    return data

def main():
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()