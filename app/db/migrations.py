from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


def migrate_firebase_auth_schema(engine: Engine) -> None:
    inspector = inspect(engine)
    if not inspector.has_table("users"):
        raise RuntimeError("The users table must exist before applying auth migrations.")

    columns = {column["name"]: column for column in inspector.get_columns("users")}

    with engine.begin() as connection:
        if "firebaseUid" not in columns:
            connection.execute(
                text('ALTER TABLE users ADD COLUMN "firebaseUid" VARCHAR')
            )

        if "hashed_password" in columns and not columns["hashed_password"]["nullable"]:
            connection.execute(
                text("ALTER TABLE users ALTER COLUMN hashed_password DROP NOT NULL")
            )

        connection.execute(
            text(
                'CREATE UNIQUE INDEX IF NOT EXISTS "ix_users_firebaseUid" '
                'ON users ("firebaseUid")'
            )
        )
