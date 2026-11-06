CREATE TABLE users (id TEXT PRIMARY KEY, username TEXT NOT NULL UNIQUE, name TEXT NOT NULL, role TEXT NOT NULL, salt TEXT NOT NULL, password_hash TEXT NOT NULL, teacher_id TEXT, class_code TEXT UNIQUE, created_at TEXT NOT NULL);
--> statement-breakpoint
CREATE TABLE sessions (token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id), expires_at INTEGER NOT NULL);
--> statement-breakpoint
CREATE TABLE work (user_id TEXT PRIMARY KEY REFERENCES users(id), body TEXT NOT NULL, revision INTEGER NOT NULL DEFAULT 0, updated_at TEXT NOT NULL);
--> statement-breakpoint
CREATE TABLE feedback (id TEXT PRIMARY KEY, student_id TEXT NOT NULL REFERENCES users(id), author_id TEXT NOT NULL REFERENCES users(id), author_role TEXT NOT NULL, body TEXT NOT NULL, rubric TEXT, created_at TEXT NOT NULL);
--> statement-breakpoint
CREATE TABLE login_limits (key TEXT PRIMARY KEY, count INTEGER NOT NULL, reset_at INTEGER NOT NULL);
--> statement-breakpoint
CREATE INDEX sessions_expiry ON sessions(expires_at);
--> statement-breakpoint
CREATE INDEX students_teacher ON users(teacher_id);
--> statement-breakpoint
CREATE INDEX feedback_student ON feedback(student_id,created_at);
