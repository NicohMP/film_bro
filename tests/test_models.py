import pytest

from src.film_bro.models import (
    Actor,
    Director,
    LibraryEntry,
    LibraryItem,
    Movie,
    MovieGenre,
    MovieKeyword,
)


def test_watched_movie_can_have_a_rating():
    entry = LibraryEntry.from_flags(
        movie_id=123,
        watched=True,
        watchlist=False,
        rating=8,
    )

    assert entry.status == "watched"
    assert entry.rating == 8


def test_watchlist_flags_create_watchlist_entry():
    entry = LibraryEntry.from_flags(
        movie_id=123,
        watched=False,
        watchlist=True,
    )

    assert entry.status == "watchlist"
    assert entry.movie_id == 123


def test_rejected_movie_creates_dismissed_entry():
    entry = LibraryEntry.from_flags(
        movie_id=123,
        watched=False,
        watchlist=False,
        rejected=True,
    )

    assert entry.status == "dismissed"
    assert entry.rejected is True


def test_watchlist_movie_cannot_have_a_rating():
    with pytest.raises(ValueError, match="Only watched movies can be rated"):
        LibraryEntry.from_flags(
            movie_id=123,
            watched=False,
            watchlist=True,
            rating=8,
        )


@pytest.mark.parametrize("rating", [0, 11])
def test_rating_outside_valid_range_is_rejected(rating: int):
    with pytest.raises(ValueError, match="Rating must be between 1 and 10"):
        LibraryEntry.from_flags(
            movie_id=123,
            watched=True,
            watchlist=False,
            rating=rating,
        )


@pytest.mark.parametrize("rating", [1, 10])
def test_rating_at_valid_boundary_is_accepted(rating: int):
    entry = LibraryEntry.from_flags(
        movie_id=123,
        watched=True,
        watchlist=False,
        rating=rating,
    )

    assert entry.rating == rating


def test_movie_cannot_be_liked_and_rejected():
    with pytest.raises(ValueError, match="both liked and rejected"):
        LibraryEntry.from_flags(
            movie_id=123,
            watched=True,
            watchlist=False,
            liked=True,
            rejected=True,
        )


def test_movie_cannot_be_watched_and_on_watchlist():
    with pytest.raises(ValueError, match="watched and on the watchlist"):
        LibraryEntry.from_flags(
            movie_id=123,
            watched=True,
            watchlist=True,
        )


def test_watchlist_movie_cannot_be_rejected():
    with pytest.raises(ValueError, match="watchlist and dismissed"):
        LibraryEntry.from_flags(
            movie_id=123,
            watched=False,
            watchlist=True,
            rejected=True,
        )


def test_entry_requires_one_status():
    with pytest.raises(ValueError, match="Choose one state"):
        LibraryEntry.from_flags(
            movie_id=123,
            watched=False,
            watchlist=False,
        )


def test_like_sets_liked_to_true():
    entry = LibraryEntry.from_flags(
        movie_id=123,
        watched=True,
        watchlist=False,
    )

    entry.like()

    assert entry.liked is True


def test_rejected_entry_cannot_be_liked():
    entry = LibraryEntry.from_flags(
        movie_id=123,
        watched=False,
        watchlist=False,
        rejected=True,
    )

    with pytest.raises(ValueError, match="cannot also be liked"):
        entry.like()


def test_library_item_contains_movie_and_matching_entry():
    movie = _sample_movie()

    item = LibraryItem.from_movie(
        movie=movie,
        watched=True,
        watchlist=False,
        liked=True,
        rejected=False,
        rating=9,
    )

    assert item.movie is movie
    assert item.entry.movie_id == movie.id
    assert item.entry.status == "watched"
    assert item.entry.liked is True
    assert item.entry.rating == 9


def test_movie_from_json_parses_all_metadata():
    data = {
        "id": 123,
        "title": "Test Movie",
        "overview": "A test overview.",
        "release_date": "2025-01-02",
        "genres": [{"id": 18, "name": "Drama"}],
        "keywords": {
            "keywords": [{"id": 42, "name": "friendship"}],
        },
        "credits": {
            "cast": [{"id": 7, "name": "Test Actor"}],
            "crew": [
                {"id": 8, "name": "Test Writer", "job": "Writer"},
                {"id": 9, "name": "Test Director", "job": "Director"},
            ],
        },
    }

    movie = Movie.from_json(data)

    assert movie.id == 123
    assert movie.title == "Test Movie"
    assert movie.overview == "A test overview."
    assert movie.release_date == "2025-01-02"
    assert movie.genres == [MovieGenre(id=18, name="Drama")]
    assert movie.keywords == [MovieKeyword(id=42, name="friendship")]
    assert movie.cast == [Actor(id=7, name="Test Actor")]
    assert movie.director == Director(id=9, name="Test Director")


def _sample_movie() -> Movie:
    return Movie(
        id=123,
        title="Test Movie",
        overview="A test overview.",
        release_date="2025-01-02",
        genres=[MovieGenre(id=18, name="Drama")],
        keywords=[MovieKeyword(id=42, name="friendship")],
        cast=[Actor(id=7, name="Test Actor")],
        director=Director(id=9, name="Test Director"),
    )
