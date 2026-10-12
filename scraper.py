from dotenv import load_dotenv
import requests
import time
import os
import json
from pathlib import Path
load_dotenv()


API_KEY = os.getenv("TMDB_API_KEY")

if not API_KEY:
    raise Exception("TMDB API key is missing")

BASE_URL = "https://api.themoviedb.org/3"
DATA_DIR = "./tmdb/"

PAGE_COUNT = 100

# Normal delay between successful requests
SLEEP_TIME = 2

# Number of times to retry a failed request
MAX_RETRIES = 3



class TMDBClient:

    def __init__(self, api_key):
        self._api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "TMDB-Movie-Downloader/1.0"})

    def get(self, endpoint, **params):
        params["api_key"] = self._api_key
        url = BASE_URL + endpoint
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                print(f"Requesting: {endpoint}")
                response = self.session.get(url,params=params,timeout=30)
                response.raise_for_status()
                data = response.json()
                # Normal delay between requests
                time.sleep(SLEEP_TIME)
                return data
            except requests.exceptions.ConnectionError as e:
                print(
                    f"Connection error "
                    f"(attempt {attempt}/{MAX_RETRIES})"
                )
                if attempt == MAX_RETRIES:
                    print("Maximum retries reached.")
                    raise
                # Exponential backoff
                wait_time = 2 ** attempt
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            except requests.exceptions.Timeout:
                print(
                    f"Timeout "
                    f"(attempt {attempt}/{MAX_RETRIES})")

                if attempt == MAX_RETRIES:
                    raise
                wait_time = 2 ** attempt
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            except requests.exceptions.HTTPError as e:
                print(f"HTTP error: {response.status_code}")
                # Don't retry most HTTP errors
                raise
    def get_popular_movies(self, page):
        return self.get("/movie/popular",page=page)
    def get_movie_details(self, movie_id):
        return self.get(f"/movie/{movie_id}")
    def get_movie_recommendations(self, movie_id):
        return self.get(f"/movie/{movie_id}/recommendations")
    def get_movie_credits(self, movie_id):
        return self.get(f"/movie/{movie_id}/credits")
    def get_movie_keywords(self, movie_id):
        return self.get(f"/movie/{movie_id}/keywords")

client = TMDBClient(API_KEY)

os.makedirs(DATA_DIR, exist_ok=True)

for page in range(1, PAGE_COUNT + 1):

    print("\n" + "=" * 80)
    print(f"Downloading data from page {page}")
    print("=" * 80)

    movies = client.get_popular_movies(page=page)

    print(f"Found {len(movies.get('results', []))} movies")
    
    for movie in movies.get("results", []):
        movie_id = movie["id"]

        file_name = f"./tmdb/{movie_id}.json"
        path = Path(file_name)
        if path.exists():
            print(f"movie : {movie_id} is already there")
            continue

        print("\n" + "-" * 80)
        print(f"Processing movie: {movie['title']}")
        print(f"Movie ID: {movie_id}")
        print("-" * 80)

        try:
            print("Getting movie details...")

            movie_details = client.get_movie_details(
                movie_id
            )
            print("Getting movie credits...")

            movie_credits = client.get_movie_credits(
                movie_id
            )
            print("Getting movie recommendations...")

            movie_recommendations = (
                client.get_movie_recommendations(
                    movie_id
                )
            )
            print("Getting movie keywords...")

            movie_keywords = client.get_movie_keywords(
                movie_id
            )
            document = {
                "id": movie_id,"details": movie_details,"credits": movie_credits.get("cast",[]),
                "crew": movie_credits.get("crew",[]),
                "keywords": movie_keywords.get("keywords",[]),
                "recommendations":movie_recommendations.get("results",[])
            }
            file_name = os.path.join(
                DATA_DIR,
                f"{movie_id}.json"
            )

            with open(
                file_name,
                "w",
                encoding="utf-8"
            ) as file:

                json.dump(
                    document,
                    file,
                    indent=4,
                    ensure_ascii=False
                )
            print(f"Saved successfully: {file_name}")
        except requests.exceptions.RequestException as e:

            print(
                f"Failed to process movie "
                f"{movie_id}: {e}"
            )
            # Continue with next movie
            continue