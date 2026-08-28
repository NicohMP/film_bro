import requests
import dotenv
from pathlib import Path
import os
from typing import Optional
from src.film_bro.models import Movie

dotenv.load_dotenv(Path(os.getcwd()) / ".env")

TOKEN = os.getenv("TMDB_READ_TOKEN")
BASE = "https://api.themoviedb.org/3"
SEARCH_ENDPOINT = "/search/movie"


def fetch_tmbd_id(title: str, year: Optional[int] = None) -> Optional[int]:
    search_url = BASE + SEARCH_ENDPOINT
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "accept": "application/json",
    }
    params = {"query": title}
    if year is not None:
        params["primary_release_year"] = str(year)
    search_response = requests.get(url=search_url, headers=headers, params=params)
    search_response.raise_for_status()
    results = search_response.json()["results"]

    if not results:
        return None

    return results[0]["id"]


def movie_from_tmdb_id(tmbd_id: int) -> Movie:

    endpoint = f"/movie/{tmbd_id}"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "accept": "application/json",
    }
    resp = requests.get(
        url=BASE + endpoint,
        headers=headers,
        params={"append_to_response": "credits,keywords"},
    )

    resp.raise_for_status()
    data = resp.json()
    return Movie.from_json(data=data)


def fetch_tmbd_movie(title: str, year: Optional[int] = None) -> Movie:
    id = fetch_tmbd_id(title, year)
    if id is None:
        raise ValueError(f"No movie found in TMDB for {title} and ({year})")
    movie = movie_from_tmdb_id(tmbd_id=id)
    return movie
