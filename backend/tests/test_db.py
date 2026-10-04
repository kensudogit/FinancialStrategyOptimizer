from app import db


class TestDb:
    def test_init_sqlite_and_insert(self):
        db.init_db("sqlite+pysqlite:///:memory:")
        assert db.SessionLocal is not None
        session = db.SessionLocal()
        try:
            row = db.StrategyRun(
                asset_class="stock",
                symbol="7203.T",
                optimized=False,
                payload={"ok": True},
                report_markdown="x",
            )
            session.add(row)
            session.commit()
            session.refresh(row)
            assert row.id >= 1
        finally:
            session.close()
