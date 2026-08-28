from typing import Optional, Literal
from .models import Movie, LibraryEntry, Actor, Director, LibraryItem, MovieStatus
from .tmdb_client import fetch_tmbd_movie
from .repositories import LibraryRepository, MovieRepository
from sqlite3 import Connection


class LibraryService:
    def __init__(self, connection: Connection) -> None:
        self.connection = connection
        self.movie_repo = MovieRepository(connection=connection)
        self.lib_repo = LibraryRepository(connection=connection)

    def add_to_watchlist(self, title: str, year: int | None = None):
        movie = fetch_tmbd_movie(title=title, year=year)
        entry = LibraryEntry.from_flags(
            movie_id=movie.id, watched=False, watchlist=True
        )
        with self.connection:
            self.movie_repo.save(movie)
            self.lib_repo.save(entry)

    def mark_watched(self, movie_id: int, rating: Optional[int] = None) -> None:
        with self.connection:
            self.lib_repo.mark_watched(movie_id=movie_id)
            if rating is not None:
                self.lib_repo.update_rating(movie_id=movie_id, rating=rating)

    def like(self, movie_id: int) -> None:
        with self.connection:
            self.lib_repo.like(movie_id)

    def dismiss(self, movie_id: int) -> None:
        with self.connection:
            self.lib_repo.dismiss(movie_id=movie_id)

    def remove(self, movie_id: int) -> None:
        with self.connection:
            self.lib_repo.remove(movie_id=movie_id)

    def get_item(self, movie_id: int) -> LibraryItem | None:
        entry = self.lib_repo.get(movie_id=movie_id)
        movie = self.movie_repo.get_movie(movie_id=movie_id)
        if (entry is None) or (movie is None):
            return None
        return LibraryItem(movie=movie, entry=entry)

    def list_items_by_status(self, status: MovieStatus) -> list[LibraryItem]:
        entries = self.lib_repo.list_by_status(status=status)
        movies = self.movie_repo.get_many(
            movie_ids=[entry.movie_id for entry in entries]
        )
        movies_by_id = {movie.id: movie for movie in movies}

        items = [
            LibraryItem(
                movie=movies_by_id[entry.movie_id],
                entry=entry,
            )
            for entry in entries
        ]
        return items
