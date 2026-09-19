from configs.config import AGGREGATION_CONFIG

def aggregate_window_events(session_id, windows):
    """
    Temporal Event Aggregator:
    Merges overlapping and contiguous windows of the same stuttering class
    to prevent double-counting artifact of the 1.0s sliding step.
    
    Inputs:
    - windows: list of window dicts with start_time, end_time, predicted_class, confidence
    Returns:
    - events: list of aggregated event dicts
    """
    conf_threshold = AGGREGATION_CONFIG.get('confidence_threshold', 0.50)
    min_support = AGGREGATION_CONFIG.get('min_support_windows', 1)
    merge_gap = AGGREGATION_CONFIG.get('merge_gap_sec', 1.5)

    # Filter for disfluent windows with sufficient confidence
    disfluent_windows = []
    for w in windows:
        if w['predicted_class'] in ['Repetition', 'Prolongation', 'Block']:
            if w['confidence'] >= conf_threshold:
                disfluent_windows.append(w)

    if not disfluent_windows:
        return []

    # Group adjacent windows of identical class
    aggregated_events = []
    current_cluster = [disfluent_windows[0]]

    for i in range(1, len(disfluent_windows)):
        w_prev = current_cluster[-1]
        w_curr = disfluent_windows[i]

        same_class = (w_curr['predicted_class'] == w_prev['predicted_class'])
        gap = w_curr['start_time'] - w_prev['end_time']
        is_overlapping_or_adjacent = (w_curr['start_time'] <= w_prev['end_time'] + merge_gap)

        if same_class and is_overlapping_or_adjacent:
            current_cluster.append(w_curr)
        else:
            # Finalize current cluster
            if len(current_cluster) >= min_support:
                event_type = current_cluster[0]['predicted_class']
                start_t = current_cluster[0]['start_time']
                end_t = max(w['end_time'] for w in current_cluster)
                mean_conf = sum(w['confidence'] for w in current_cluster) / len(current_cluster)
                aggregated_events.append({
                    "session_id": session_id,
                    "event_type": event_type,
                    "start_time": round(start_t, 2),
                    "end_time": round(end_t, 2),
                    "confidence": round(mean_conf, 4),
                    "supporting_window_count": len(current_cluster)
                })
            current_cluster = [w_curr]

    # Flush final cluster
    if len(current_cluster) >= min_support:
        event_type = current_cluster[0]['predicted_class']
        start_t = current_cluster[0]['start_time']
        end_t = max(w['end_time'] for w in current_cluster)
        mean_conf = sum(w['confidence'] for w in current_cluster) / len(current_cluster)
        aggregated_events.append({
            "session_id": session_id,
            "event_type": event_type,
            "start_time": round(start_t, 2),
            "end_time": round(end_t, 2),
            "confidence": round(mean_conf, 4),
            "supporting_window_count": len(current_cluster)
        })

    return aggregated_events
