"""Print the SQL that builds every CORE table on an empty database.

    cd backend
    python dump_core_schema.py > /tmp/core.sql

It prints exactly what the backend's start-up `create_all` would run (made from
the models in app/models), without connecting to any database. Use it to refresh
migrations/001_core_schema.sql after a model changes: keep that file's header and
BEGIN/COMMIT, replace the SQL in between, and add the RLS "lock" line for any new
table. Needs the normal settings (a filled .env, or the .env.example values).
"""

import warnings

from sqlalchemy import create_mock_engine

warnings.filterwarnings("ignore")

import app.domain_model_registry  # noqa: E402,F401  (registers every model)
from app.core.database import Base  # noqa: E402

statements: list[str] = []


def _collect(sql, *args, **kwargs) -> None:
    statements.append(str(sql.compile(dialect=engine.dialect)).strip() + ";")


engine = create_mock_engine("postgresql+psycopg2://", _collect)
Base.metadata.create_all(engine, checkfirst=False)

print("\n\n".join(statements))
print()
for table in Base.metadata.sorted_tables:
    print(f"ALTER TABLE public.{table.name} ENABLE ROW LEVEL SECURITY;")
