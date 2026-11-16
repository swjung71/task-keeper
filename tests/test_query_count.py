from sqlalchemy import event


def _count_queries(db_session, fn):
    """fn 실행 중 DB에 보낸 SQL 쿼리 수를 셉니다."""
    count = 0

    def _on_execute(*_args, **_kwargs):
        nonlocal count
        count += 1

    engine = db_session.get_bind()
    event.listen(engine, "before_cursor_execute", _on_execute)
    try:
        fn()
    finally:
        event.remove(engine, "before_cursor_execute", _on_execute)
    return count


def test_list_tasks_query_count_is_constant(client, db_session):
    # 태그를 즉시 로딩하지 않으면 할 일 개수만큼 태그 조회 쿼리가 늘어납니다(N+1).
    for i in range(20):
        client.post("/tasks", json={"title": f"할 일 {i}", "tags": [f"tag{i % 3}"]})
    db_session.expire_all()

    count = _count_queries(db_session, lambda: client.get("/tasks"))

    # 할 일 조회 1번 + 태그 조회 1번
    assert count == 2
