CREATE TABLE IF NOT EXISTS movies ( -- create a new table
    id              INTEGER PRIMARY KEY, -- primery key (match tmdb key ?)
    title           TEXT NOT NULL, -- NOT NULL = the column cannot be missing
    overview        TEXT NOT NULL DEFAULT '', --- DEFAULT = value SQLite supplies column omitted.
    release_date    TEXT,
    fetched_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS genres (
    id   INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS movie_genres (
    movie_id INTEGER NOT NULL,
    genre_id INTEGER NOT NULL,

    PRIMARY KEY (movie_id, genre_id),

    FOREIGN KEY (movie_id)
        REFERENCES movies(id)
        ON DELETE CASCADE,

    FOREIGN KEY (genre_id)
        REFERENCES genres(id)
);

CREATE TABLE IF NOT EXISTS keywords (
    id   INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS people ( -- actors and directors share the same TMDB person IDs
    id   INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS movie_credits (
    movie_id INTEGER NOT NULL,
    person_id INTEGER NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('cast', 'director', 'composer')),
    character TEXT,
    billing_order INTEGER,

    PRIMARY KEY (movie_id, person_id, role),

    FOREIGN KEY (movie_id)
        REFERENCES movies(id)
        ON DELETE CASCADE,

    FOREIGN KEY (person_id)
        REFERENCES people(id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS movie_keywords (
    movie_id INTEGER NOT NULL,
    keyword_id INTEGER NOT NULL,

    PRIMARY KEY (movie_id, keyword_id),

    FOREIGN KEY (movie_id)
        REFERENCES movies(id)
        ON DELETE CASCADE,

    FOREIGN KEY (keyword_id)
        REFERENCES keywords(id)
);



CREATE TABLE IF NOT EXISTS library_entries (
    movie_id    INTEGER PRIMARY KEY
                REFERENCES movies(id)
                ON DELETE RESTRICT,
    status      TEXT NOT NULL
                CHECK (status IN ('watchlist', 'watched', 'dismissed')),
    liked       BOOLEAN NULL
                CHECK (liked IN (0, 1) OR liked IS NULL),
    rejected    BOOLEAN NULL
                CHECK (rejected IN (0, 1) OR rejected IS NULL),
    rating      INTEGER NULL
                CHECK (rating BETWEEN 1 AND 10 OR rating IS NULL),
    created_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (liked IS NOT TRUE OR rejected IS NOT TRUE), -- movie can't be both rejected and liked
    CHECK (status != 'dismissed' OR rejected IS TRUE), -- a dismissed movie must be rejected
    CHECK (rating IS NULL OR status = 'watched') -- can't rate a movie not watched
);
