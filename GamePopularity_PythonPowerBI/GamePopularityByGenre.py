# Import needed libraries
import requests
import pandas as pd
import time

# Establish variables
CLIENT_ID = "omitted"
CLIENT_SECRET = "omitted"
url = "https://id.twitch.tv/oauth2/token"
params = {
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "grant_type": "client_credentials"
}

# Request access token
response = requests.post(url, params=params)

# Store access token
token = response.json()["access_token"]

# Establish variables
headers = {
    "Client-ID": CLIENT_ID,
    "Authorization": f"Bearer {token}"
}

all_games = []
all_ids = []
queried_ids = set()
limit = 500
offset = 0

# while loop to query all games that fit criteria
while True:

    # API query
    query = f"""
    fields name,genres.name,first_release_date;
    where genres.name != null & first_release_date != null & first_release_date >= 1577836800 & first_release_date <= 1767225600;
    limit {limit};
    offset {offset};
    """
    # Store API response 
    response = requests.post(
    "https://api.igdb.com/v4/games",
    headers=headers,
    data=query
)
    # Convert API response to JSON
    games = response.json()

    # Store the unique identifiers of the games in the current iteration
    current_ids = [game['id'] for game in games]
    
    # Breaks loop if there are duplicate IDs between the current iteration and all previous iterations
    if not set(current_ids).isdisjoint(set(all_ids)):
        print("Duplicate IDs found. Ending loop.")
        break

    # Updates the list of all IDs with the current IDs
    all_ids.extend(current_ids)
    #queried_ids = set(current_ids)

    # Breaks loop if the API response is not successful
    if response.status_code != 200:
        print(f"Error: {response.status_code} - {response.text}")
        break

    # Breaks loop if there is no more data to fetch
    if not games:
        break  # No more data to fetch
    
    # Appends the games from the current iteration to the list of all games
    all_games.extend(games)
    print(f"Retrieved {len(all_games)} records...")

    # Increment offset for the next iteration
    offset += limit
    
    # IGDB has a limit of 4 requests per second
    time.sleep(0.25) 
    
    # Counter to track the amount of rows retrieved
    print(f"Total games retrieved: {len(all_games)}")



# Convert the list of games to a DataFrame
df = pd.json_normalize(all_games)

#This code is used to extract the names of the genres and platforms from the JSON response and join them into a single string.
def extract_names(items):
    if isinstance(items, list):
        return ", ".join([x["name"] for x in items])
    return None
df["genres"] = df["genres"].apply(extract_names)

#This code is used to convert the release date from a timestamp to a datetime object.
df["release_date"] = pd.to_datetime(
    df["first_release_date"],
    unit="s"
)

# Adds a new column to the DataFrame that contains the release year extracted from the release date.
df["release_year"] = df["release_date"].dt.year

# Converts the dataframe to a CSV file and saves it to the local directory
df.to_csv("games.csv", index=False)