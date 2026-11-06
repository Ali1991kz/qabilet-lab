CREATE TABLE profiles (user_id TEXT PRIMARY KEY REFERENCES users(id), body TEXT NOT NULL, updated_at TEXT NOT NULL);
