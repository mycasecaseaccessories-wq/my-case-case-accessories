from apps.telegram.webhook import UpdateDeduplicator


def test_webhook_update_deduplicator_accepts_once_and_rejects_replay() -> None:
    deduplicator = UpdateDeduplicator(max_size=2)
    assert deduplicator.accept(100)
    assert not deduplicator.accept(100)
    assert deduplicator.accept(101)
    assert deduplicator.accept(102)


def test_webhook_update_deduplicator_rejects_malformed_update_ids() -> None:
    deduplicator = UpdateDeduplicator()
    assert not deduplicator.accept(None)
    assert not deduplicator.accept("100")
