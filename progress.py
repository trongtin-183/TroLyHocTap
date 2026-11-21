import json
from datetime import datetime
from pathlib import Path


PROGRESS_FILE = Path("data") / "progress.json"


def load_progress():
    if not PROGRESS_FILE.exists():
        return {"topics": {}, "history": []}

    with PROGRESS_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def record_answer(topic, is_correct, source_page):
    progress = load_progress()
    topic_key = topic.strip().casefold()

    stats = progress["topics"].setdefault(
        topic_key,
        {
            "attempts": 0,
            "correct": 0,
            "wrong": 0,
            "wrong_pages": [],
        },
    )

    stats["attempts"] += 1

    if is_correct:
        stats["correct"] += 1
    else:
        stats["wrong"] += 1
        if source_page not in stats["wrong_pages"]:
            stats["wrong_pages"].append(source_page)

    progress["history"].append({
        "time": datetime.now().isoformat(timespec="seconds"),
        "topic": topic.strip(),
        "is_correct": is_correct,
        "source_page": source_page,
    })

    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)

    with PROGRESS_FILE.open("w", encoding="utf-8") as file:
        json.dump(progress, file, ensure_ascii=False, indent=2)


def get_weak_topics(min_attempts=2, threshold=0.6):
    progress = load_progress()
    weak_topics = []

    for topic, stats in progress["topics"].items():
        accuracy = stats["correct"] / stats["attempts"]

        if stats["attempts"] >= min_attempts and accuracy < threshold:
            weak_topics.append({
                "topic": topic,
                "accuracy": accuracy,
                "attempts": stats["attempts"],
                "wrong_pages": stats["wrong_pages"],
            })

    return weak_topics


def record_session(topic, question_count, correct_count, duration_seconds):
    progress = load_progress()
    progress.setdefault("sessions", [])

    if question_count > 0:
        accuracy = correct_count / question_count * 100
    else:
        accuracy = 0

    session = {
        "time": datetime.now().isoformat(timespec="seconds"),
        "topic": topic.strip(),
        "question_count": question_count,
        "correct_count": correct_count,
        "wrong_count": question_count - correct_count,
        "accuracy": round(accuracy, 1),
        "duration_seconds": round(duration_seconds, 1),
    }

    progress["sessions"].append(session)

    with PROGRESS_FILE.open("w", encoding="utf-8") as file:
        json.dump(progress, file, ensure_ascii=False, indent=2)

    return session