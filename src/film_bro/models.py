from dataclasses import dataclass
from typing import Optional, Literal

MovieStatus = Literal["watchlist", "watched", "dismissed"]


@dataclass(frozen=True)
class MovieGenre:
    id: int
    name: str


@dataclass(frozen=True)
class Actor:
    id: int
    name: str


@dataclass(frozen=True)
class Director:
    id: int
    name: str


@dataclass(frozen=True)
class MovieKeyword:
    id: int
    name: str


@dataclass
class Movie:
    id: int
    title: str
    overview: str
    release_date: str
    genres: list[MovieGenre]
    keywords: list[MovieKeyword]
    cast: list[Actor]
    director: Director

    @classmethod
    def from_json(cls, data: dict):
        director_data = next(
            crew_member
            for crew_member in data["credits"]["crew"]
            if crew_member["job"] == "Director"
        )

        return cls(
            id=data["id"],
            title=data["title"],
            overview=data["overview"],
            release_date=data["release_date"],
            genres=[
                MovieGenre(id=genre["id"], name=genre["name"])
                for genre in data["genres"]
            ],
            keywords=[
                MovieKeyword(id=keyword["id"], name=keyword["name"])
                for keyword in data["keywords"]["keywords"]
            ],
            cast=[
                Actor(id=actor["id"], name=actor["name"])
                for actor in data["credits"]["cast"]
            ],
            director=Director(
                id=director_data["id"],
                name=director_data["name"],
            ),
        )


@dataclass
class LibraryEntry:
    movie_id: int
    status: MovieStatus
    liked: Optional[bool]
    rejected: Optional[bool]
    rating: Optional[int]

    @classmethod
    def from_flags(
        cls,
        movie_id: int,
        watched: bool,
        watchlist: bool,
        liked: Optional[bool] = None,
        rejected: Optional[bool] = None,
        rating: Optional[int] = None,
    ) -> "LibraryEntry":
        match watched, watchlist, rejected is True:
            case True, True, _:
                raise ValueError("A movie cannot be watched and on the watchlist")
            case False, True, True:
                raise ValueError("A movie cannot be on the watchlist and dismissed")
            case True, False, _:
                status: MovieStatus = "watched"
            case False, True, False:
                status: MovieStatus = "watchlist"
            case False, False, True:
                status: MovieStatus = "dismissed"
            case False, False, False:
                raise ValueError("Choose one state: watched, watchlist, or dismissed")

        if liked is True and rejected is True:
            raise ValueError("A movie cannot be both liked and rejected")

        if rating is not None:
            if status != "watched":
                raise ValueError("Only watched movies can be rated")
            if not 1 <= rating <= 10:
                raise ValueError("Rating must be between 1 and 10")

        return cls(
            movie_id=movie_id,
            status=status,
            liked=liked,
            rejected=rejected,
            rating=rating,
        )

    def like(self):
        if self.rejected is True:
            raise ValueError("A rejected movie cannot also be liked")
        self.liked = True


@dataclass
class LibraryItem:
    movie: Movie
    entry: LibraryEntry

    @classmethod
    def from_movie(
        cls,
        movie: Movie,
        watched: bool,
        watchlist: bool,
        liked: Optional[bool],
        rejected: Optional[bool],
        rating: Optional[int],
    ) -> "LibraryItem":
        entry = LibraryEntry.from_flags(
            movie_id=movie.id,
            watched=watched,
            watchlist=watchlist,
            liked=liked,
            rejected=rejected,
            rating=rating,
        )

        return cls(
            entry=entry,
            movie=movie,
        )


# def create_entry(
#     movie: Movie,
#     watched: bool,
#     watchlist: bool,
#     liked: Optional[bool],
#     rejected: Optional[bool],
#     rating: Optional[int],
# ) -> LibraryEntry:
#     if watched and watchlist:
#         raise ValueError("either you watch it or you want to watch broski")

#     status: MovieStatus = "watched" if (watched and (not watchlist)) else "watchlist"
#     if rating is not None:
#         assert rating in range(10)
#     return LibraryEntry(
#         movie_id=movie.id, status=status, liked=liked, rejected=rejected, rating=rating
#     )
