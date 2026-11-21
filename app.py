from pdf_reader import read_pdf, split_into_chunks
from retriever import retrieve_chunks
from llm_service import answer_question
from quiz import generate_quiz
from time import perf_counter
from progress import record_answer, record_session, load_progress, get_weak_topics
pages = read_pdf("data/sample.pdf")

print(f"Đã đọc {len(pages)} trang")

for page in pages[:2]:
    print(f"\n--- Trang {page['page']} ---")
    print(page["text"][:500])

chunks = split_into_chunks(pages)

question = input("Nhập câu hỏi: ")
results = retrieve_chunks(question, chunks)
print(f"Tìm được {len(results)} đoạn phù hợp")
for result in results:
    print(f"\n--- Trang {result['page']} | Điểm {result['score']} ---")
    print(result["text"][:300])
    answer = answer_question(question, results)
    print("\n--- Câu trả lời ---")
    print(answer)

print(f"Đã tạo {len(chunks)} đoạn")

for chunk in chunks[:3]:
    print(f"\n--- Trang {chunk['page']} ---")
    print(chunk["text"][:200])

#Tạo quiz
topic = input("\nNhập chủ đề để tạo quiz (Enter để bỏ qua): ").strip()

if topic:
    questions = generate_quiz(topic, chunks)

    if not questions:
        print("Không tìm thấy nội dung phù hợp để tạo quiz.")
    else:
        for number, quiz_question in enumerate(questions, start=1):
            quiz_start = perf_counter()
            correct_count = 0
            print(f"\nCâu {number}: {quiz_question['question']}")
            print(f"Chủ đề: {quiz_question['topic']}")
            print(f"Nguồn: Trang {quiz_question['source_page']}")

            for letter, choice in quiz_question["choices"].items():
                print(f"{letter}. {choice}")

            user_answer = input("Đáp án của bạn (A/B/C/D): ").strip().upper()

            is_correct = user_answer == quiz_question["correct_answer"]

            if is_correct:
                print("Chính xác!")
                correct_count += 1
            else:
                print(f"Chưa đúng. Đáp án là {quiz_question['correct_answer']}.")

            record_answer(
                quiz_question["topic"],
                is_correct,
                quiz_question["source_page"],
            )

            print(f"Giải thích: {quiz_question['explanation']}")

            duration_seconds = perf_counter() - quiz_start

        record_session(
            topic,
            len(questions),
            correct_count,
            duration_seconds,
        )

        print(
            f"\nĐiểm lượt này: {correct_count}/{len(questions)} câu đúng "
            f"({correct_count / len(questions):.0%})"
        )
        print(f"Thời gian làm quiz: {duration_seconds:.0f} giây")


        progress = load_progress()
        sessions_for_topic = [
            session
            for session in progress.get("sessions", [])
            if session["topic"].casefold() == topic.strip().casefold()
        ]

        print("\n--- Lịch sử quiz chủ đề này ---")

        for number, session in enumerate(sessions_for_topic, start=1):
            print(
                f"Lượt {number}: {session['correct_count']}/"
                f"{session['question_count']} đúng, "
                f"{session['accuracy']:.1f}%, "
                f"{session['duration_seconds']:.0f} giây"
            )

        if len(sessions_for_topic) >= 2:
            previous = sessions_for_topic[-2]["accuracy"]
            latest = sessions_for_topic[-1]["accuracy"]
            difference = latest - previous

            if difference > 0:
                print(f"Tiến bộ: tỷ lệ đúng tăng {difference:.1f} điểm phần trăm.")
            elif difference < 0:
                print(f"Tỷ lệ đúng giảm {abs(difference):.1f} điểm phần trăm.")
            else:
                print("Tỷ lệ đúng bằng lượt trước.")
        
        print("\n--- Tiến độ theo chủ đề ---")
        for topic, stats in progress["topics"].items():
            accuracy = stats["correct"] / stats["attempts"] * 100
            print(
                f"{topic}: đúng {stats['correct']}/{stats['attempts']} "
                f"({accuracy:.0f}%)"
            )
            if stats["wrong_pages"]:
                print(f"  Trang nên xem lại: {stats['wrong_pages']}")
        weak_topics = get_weak_topics()
        if weak_topics:
            print("\nCác chủ đề nên ôn thêm:")
            for item in weak_topics:
                print(
                    f"- {item['topic']}: đúng {item['accuracy']:.0%}, "
                    f"đã làm {item['attempts']} câu"
                )
        else:
            print("\nChưa có chủ đề nào đủ dữ liệu để đánh dấu cần ôn.")