CREATE TABLE IF NOT EXISTS players (
    name        TEXT PRIMARY KEY,
    cliche      TEXT NOT NULL DEFAULT '',
    dice        INTEGER,
    lost_dice   INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS locks (
    player_name TEXT PRIMARY KEY REFERENCES players(name) ON DELETE CASCADE,
    locked_by   TEXT NOT NULL,
    acquired_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS saves (
    save_name   TEXT NOT NULL,
    saved_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    data        JSONB NOT NULL,
    PRIMARY KEY (save_name)
);
