def calculate_session_summary(session_id, duration_sec, windows, events, model_version):
    """
    Computes deterministic VoxFlow session summary:
    - valid speech windows
    - fluent windows
    - repetition events count
    - prolongation events count
    - block events count
    - fluency ratio = fluent_windows / valid_windows
    - event timeline
    """
    total_windows = len(windows)
    valid_windows = total_windows
    fluent_windows = sum(1 for w in windows if w['predicted_class'] == 'Fluent')

    rep_events = sum(1 for e in events if e['event_type'] == 'Repetition')
    prolong_events = sum(1 for e in events if e['event_type'] == 'Prolongation')
    block_events = sum(1 for e in events if e['event_type'] == 'Block')

    fluency_ratio = (fluent_windows / valid_windows) if valid_windows > 0 else 1.0

    return {
        "session_id": session_id,
        "duration_sec": round(duration_sec, 2),
        "total_windows": total_windows,
        "valid_windows": valid_windows,
        "fluent_windows": fluent_windows,
        "repetition_events": rep_events,
        "prolongation_events": prolong_events,
        "block_events": block_events,
        "fluency_ratio": round(fluency_ratio, 4),
        "model_version": model_version,
        "events": events
    }
