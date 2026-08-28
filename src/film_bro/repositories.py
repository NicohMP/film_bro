import sqlite3

from .models import (
    Actor,
    Director,
    LibraryEntry,
    Movie,
    MovieGenre,
    MovieKeyword,
    MovieStatus,
)


class MovieRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def save(self, movie: Movie) -> None:
        self._upsert_movie(movie)
        self._replace_genres(movie)
        self._replace_keywords(movie)
        self._replace_credits(movie)

    def get_movie(self, movie_id: int) -> Movie | None:
        row = self.connection.execute(
            """ SELECT id, title, overview, release_date FROM movies WHERE id = ?""",
            (movie_id,),
        ).fetchone()

        if row is None:
            return None

        return self._row_to_movie(row)

    def get_many(self, movie_ids: list[int]) -> list[Movie]:
        if not movie_ids:
            return []

        unique_movie_ids = list(dict.fromkeys(movie_ids))
        # permet de mettre suffisament de conteneurs de valeurs dans chaque requette
        placeholders = ", ".join("?" for _ in unique_movie_ids)
        rows = self.connection.execute(
            f""" SELECT id, title, overview, release_date FROM movies
            WHERE id IN ({placeholders})""",
            unique_movie_ids,
        ).fetchall()

        rows_by_id = {row["id"]: row for row in rows}
        return [
            self._row_to_movie(rows_by_id[movie_id])
            for movie_id in movie_ids
            if movie_id in rows_by_id
        ]

    def exists(self, movie_id: int) -> bool:
        row = self.connection.execute(
            """
            SELECT 1
            FROM movies
            WHERE id = ?
            """,
            (movie_id,),
        ).fetchone()
        return row is not None

    def _row_to_movie(self, row: sqlite3.Row) -> Movie:
        movie_id = row["id"]
        return Movie(
            id=movie_id,
            title=row["title"],
            overview=row["overview"],
            release_date=row["release_date"],
            genres=self._load_genres(movie_id),
            keywords=self._load_keywords(movie_id),
            cast=self._load_cast(movie_id),
            director=self._load_director(movie_id),
        )

    def _upsert_movie(self, movie: Movie) -> None:
        self.connection.execute(
            """
        INSERT INTO movies (id, title, overview, release_date)
        VALUES (?,?,?,?)
        ON CONFLICT(id) DO UPDATE SET
            title = excluded.title,
            overview = excluded.overview,
            release_date = excluded.release_date,
            fetched_at = CURRENT_TIMESTAMP
        """,
            (
                movie.id,
                movie.title,
                movie.overview,
                movie.release_date,
            ),
        )

    def _replace_genres(self, movie: Movie) -> None:
        genre_rows = [(genre.id, genre.name) for genre in movie.genres]
        # Ensure every genre row exists in the genre db first
        self.connection.executemany(
            """ INSERT INTO genres (id, name) VALUES (?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name """,
            genre_rows,
        )
        # Remove all genre/movie link with movie_id
        self.connection.execute(
            """
            DELETE FROM movie_genres
            WHERE movie_id = ?
            """,
            (movie.id,),
        )
        # Insert new genre/movie relationships
        relationship_rows = [(movie.id, genre.id) for genre in movie.genres]
        self.connection.executemany(
            """INSERT INTO movie_genres (movie_id, genre_id) VALUES (?, ?)""",
            relationship_rows,
        )

    def _replace_keywords(self, movie: Movie) -> None:
        keyword_rows = [(keyword.id, keyword.name) for keyword in movie.keywords]
        self.connection.executemany(
            """INSERT INTO keywords (id, name) VALUES (?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name""",
            keyword_rows,
        )
        self.connection.execute(
            """ DELETE FROM movie_keywords WHERE movie_id = ?""",
            (movie.id,),
        )
        relationship_rows = [(movie.id, keyword.id) for keyword in movie.keywords]
        self.connection.executemany(
            """ INSERT INTO movie_keywords (movie_id, keyword_id) VALUES (?, ?)""",
            relationship_rows,
        )

    def _replace_credits(self, movie: Movie) -> None:
        people_by_id = {
            person.id: person.name for person in [*movie.cast, movie.director]
        }
        self.connection.executemany(
            """
            INSERT INTO people (id, name)
            VALUES (?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name = excluded.name
            """,
            people_by_id.items(),
        )

        self.connection.execute(
            """ DELETE FROM movie_credits WHERE movie_id = ? AND role IN ('cast', 'director')""",
            (movie.id,),
        )

        cast_rows = [
            (movie.id, actor.id, "cast", None, billing_order)
            for billing_order, actor in enumerate(movie.cast)
        ]
        director_row = (movie.id, movie.director.id, "director", None, None)
        self.connection.executemany(
            """
            INSERT INTO movie_credits (movie_id,person_id,role,character,billing_order)
            VALUES (?, ?, ?, ?, ?)
            """,
            [*cast_rows, director_row],
        )

    def _load_genres(self, movie_id: int) -> list[MovieGenre]:
        rows = self.connection.execute(
            """
            SELECT genres.id, genres.name -- get id and name from join table on genre id for row with movie_id
            FROM genres
            JOIN movie_genres
                ON movie_genres.genre_id = genres.id
            WHERE movie_genres.movie_id = ?
            ORDER BY genres.name
            """,
            (movie_id,),
        ).fetchall()

        return [MovieGenre(id=row["id"], name=row["name"]) for row in rows]

    def _load_keywords(self, movie_id: int) -> list[MovieKeyword]:
        rows = self.connection.execute(
            """
            SELECT keywords.id, keywords.name
            FROM keywords
            JOIN movie_keywords
                ON movie_keywords.keyword_id = keywords.id
            WHERE movie_keywords.movie_id = ?
            ORDER BY keywords.name
            """,
            (movie_id,),
        ).fetchall()

        return [MovieKeyword(id=row["id"], name=row["name"]) for row in rows]

    def _load_cast(self, movie_id: int) -> list[Actor]:
        rows = self.connection.execute(
            """
            SELECT people.id, people.name
            FROM people
            JOIN movie_credits
                ON movie_credits.person_id = people.id
            WHERE movie_credits.movie_id = ?
                AND movie_credits.role = 'cast'
            ORDER BY movie_credits.billing_order
            """,
            (movie_id,),
        ).fetchall()

        return [Actor(id=row["id"], name=row["name"]) for row in rows]

    def _load_director(self, movie_id: int) -> Director:
        row = self.connection.execute(
            """
            SELECT people.id, people.name
            FROM people
            JOIN movie_credits
                ON movie_credits.person_id = people.id
            WHERE movie_credits.movie_id = ?
                AND movie_credits.role = 'director'
            LIMIT 1
            """,
            (movie_id,),
        ).fetchone()

        if row is None:
            raise LookupError(f"No director stored for movie {movie_id}")

        return Director(id=row["id"], name=row["name"])


class LibraryRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def save(self, entry: LibraryEntry) -> None:
        self.connection.execute(
            """
        INSERT INTO library_entries (movie_id, status, liked, rejected, rating)
        VALUES (?,?,?,?,?)
        ON CONFLICT(movie_id) DO UPDATE SET
            status = excluded.status,
            liked = excluded.liked,
            rejected = excluded.rejected,
            rating = excluded.rating,
            updated_at = CURRENT_TIMESTAMP
        """,
            (
                entry.movie_id,
                entry.status,
                entry.liked,
                entry.rejected,
                entry.rating,
            ),
        )

    def get(self, movie_id: int) -> LibraryEntry | None:
        row = self.connection.execute(
            """
            SELECT movie_id, status, liked ,rejected, rating FROM library_entries  WHERE movie_id = ?
            """,
            (movie_id,),
        ).fetchone()
        return None if row is None else self._row_to_entry(row)

    def _row_to_entry(self, row: sqlite3.Row) -> LibraryEntry:
        return LibraryEntry(
            movie_id=row["movie_id"],
            status=row["status"],
            liked=None if row["liked"] is None else bool(row["liked"]),
            rejected=None if row["rejected"] is None else bool(row["rejected"]),
            rating=row["rating"],
        )

    def remove(self, movie_id: int) -> None:
        self.connection.execute(
            """DELETE FROM library_entries where movie_id = ?""",
            (movie_id,),
        )

    def list_all(self) -> list[LibraryEntry]:
        rows = self.connection.execute("""SELECT * FROM library_entries""").fetchall()
        entries = [self._row_to_entry(row) for row in rows]
        return entries

    def list_by_status(self, status: MovieStatus) -> list[LibraryEntry]:
        rows = self.connection.execute(
            """SELECT * FROM library_entries WHERE status = ?""",
            (status,),
        ).fetchall()
        return [self._row_to_entry(row) for row in rows]

    def update_rating(self, movie_id: int, rating: int) -> None:
        self.connection.execute(
            """
            UPDATE library_entries
            SET rating = ?, updated_at = CURRENT_TIMESTAMP
            WHERE movie_id = ?
            """,
            (rating, movie_id),
        )

    def mark_watched(self, movie_id: int) -> None:
        self.connection.execute(
            """
            UPDATE library_entries
            SET status = "watched", updated_at = CURRENT_TIMESTAMP
            WHERE movie_id = ?
            """,
            (movie_id,),
        )

    def like(self, movie_id: int) -> None:
        self.connection.execute(
            """
            UPDATE library_entries
            SET liked = 1, updated_at = CURRENT_TIMESTAMP
            WHERE movie_id = ?
            """,
            (movie_id,),
        )

    def dismiss(self, movie_id: int) -> None:
        self.connection.execute(
            """
            UPDATE library_entries
            SET status = "dismissed", rejected = 1, rating = NULL, liked = 0 updated_at = CURRENT_TIMESTAMP
            WHERE movie_id = ?
            """,
            (movie_id,),
        )
