import streamlit as st

from pdf_reader import read_pdf_bytes, split_into_chunks
from retriever import retrieve_chunks
from llm_service import answer_question

from time import perf_counter
from quiz import generate_quiz
from progress import record_answer, record_session

from progress import record_answer, record_session, load_progress, get_weak_topics

st.set_page_config(
    page_title="Trợ lý học tập",
    page_icon="📚",
    layout="wide",
)


@st.cache_data
def process_pdf(pdf_bytes):
    pages = read_pdf_bytes(pdf_bytes)
    chunks = split_into_chunks(pages)
    return pages, chunks


st.title("📚 Trợ lý học tập theo tài liệu")

uploaded_file = st.file_uploader(
    "Tải lên giáo trình hoặc slide PDF",
    type=["pdf"],
)

tab_qa, tab_quiz, tab_progress = st.tabs(
    ["Hỏi đáp", "Tạo quiz", "Tiến độ"]
)

if uploaded_file is None:
    st.info("Tải một file PDF lên để bắt đầu.")
else:
    pdf_bytes = uploaded_file.getvalue()
    pages, chunks = process_pdf(pdf_bytes)

    st.success(
        f"Đã đọc {len(pages)} trang và tạo {len(chunks)} đoạn "
        f"từ file {uploaded_file.name}."
    )

    with tab_qa:
        st.subheader("Hỏi đáp theo tài liệu")
        question = st.text_input("Bạn muốn hỏi điều gì?")

        if st.button("Gửi câu hỏi", key="ask_button"):
            if not question.strip():
                st.warning("Nhập câu hỏi trước nhé.")
            else:
                results = retrieve_chunks(question, chunks)

                if not results:
                    st.info("Chưa tìm thấy đoạn phù hợp trong tài liệu.")
                else:
                    with st.spinner("Đang tìm câu trả lời..."):
                        answer = answer_question(question, results)

                    st.markdown(answer)

                    with st.expander("Xem các đoạn tài liệu được dùng"):
                        for result in results:
                            st.markdown(f"**Trang {result['page']}**")
                            st.write(result["text"])

    with tab_quiz:
        st.subheader("Ôn tập bằng quiz")

        weak_topics = get_weak_topics()
        suggested_topic = ""

        if weak_topics:
            weakest_topic = min(
                weak_topics,
                key=lambda item: item["accuracy"],
            )
            suggested_topic = weakest_topic["topic"]

            st.info(
                f"Gợi ý ôn tập: {suggested_topic} "
                f"(tỷ lệ đúng {weakest_topic['accuracy']:.0%})."
            )

        quiz_topic = st.text_input(
            "Nhập chủ đề muốn ôn",
            value=suggested_topic,
            key="quiz_topic_input",
        )

        question_count = st.slider(
            "Số câu hỏi",
            min_value=1,
            max_value=10,
            value=5,
        )

        if st.button("Tạo quiz", key="generate_quiz_button"):
            if not quiz_topic.strip():
                st.warning("Nhập chủ đề trước nhé.")
            else:
                try:
                    with st.spinner("Đang tạo quiz..."):
                        questions = generate_quiz(
                            quiz_topic,
                            chunks,
                            num_questions=question_count,
                        )

                    if questions:
                        st.session_state["quiz_questions"] = questions
                        st.session_state["quiz_topic_current"] = quiz_topic.strip()
                        st.session_state["quiz_started_at"] = perf_counter()
                        st.session_state["quiz_submitted"] = False
                        st.session_state["quiz_run_id"] = (
                            st.session_state.get("quiz_run_id", 0) + 1
                        )
                    else:
                        st.warning("Không tìm thấy nội dung phù hợp để tạo quiz.")

                except Exception as error:
                    st.error(f"Chưa tạo được quiz: {error}")

        questions = st.session_state.get("quiz_questions", [])

        if questions and not st.session_state.get("quiz_submitted", False):
            with st.form("quiz_form"):
                answers = []

                for number, quiz_question in enumerate(questions, start=1):
                    st.markdown(
                        f"**Câu {number}: {quiz_question['question']}**"
                    )
                    st.caption(
                        f"Chủ đề: {quiz_question['topic']} · "
                        f"Nguồn: trang {quiz_question['source_page']}"
                    )

                    choices = quiz_question["choices"]
                    answer = st.radio(
                        "Chọn một đáp án",
                        options=list(choices.keys()),
                        format_func=lambda letter, choices=choices:
                            f"{letter}. {choices[letter]}",
                        index=None,
                        key=(
                            f"quiz_answer_"
                            f"{st.session_state['quiz_run_id']}_{number}"
                        ),
                    )
                    answers.append(answer)

                submitted = st.form_submit_button("Nộp bài")

            if submitted:
                if any(answer is None for answer in answers):
                    st.warning("Hãy chọn đáp án cho tất cả câu hỏi trước khi nộp.")
                else:
                    correct_count = 0
                    quiz_results = []

                    for quiz_question, user_answer in zip(questions, answers):
                        is_correct = (
                            user_answer == quiz_question["correct_answer"]
                        )

                        if is_correct:
                            correct_count += 1

                        record_answer(
                            quiz_question["topic"],
                            is_correct,
                            quiz_question["source_page"],
                        )

                        quiz_results.append({
                            "question": quiz_question,
                            "user_answer": user_answer,
                            "is_correct": is_correct,
                        })

                    duration_seconds = (
                        perf_counter()
                        - st.session_state["quiz_started_at"]
                    )

                    record_session(
                        st.session_state["quiz_topic_current"],
                        len(questions),
                        correct_count,
                        duration_seconds,
                    )

                    st.session_state["quiz_results"] = quiz_results
                    st.session_state["quiz_correct_count"] = correct_count
                    st.session_state["quiz_submitted"] = True

        if st.session_state.get("quiz_submitted", False):
            quiz_results = st.session_state["quiz_results"]
            correct_count = st.session_state["quiz_correct_count"]

            st.metric(
                "Kết quả",
                f"{correct_count}/{len(quiz_results)} câu đúng",
            )

            for result in quiz_results:
                question = result["question"]

                if result["is_correct"]:
                    st.success(f"Đúng: {question['question']}")
                else:
                    st.error(
                        f"Sai: {question['question']}. "
                        f"Đáp án đúng là {question['correct_answer']}."
                    )

                st.write(f"Giải thích: {question['explanation']}")
                st.caption(f"Nguồn: trang {question['source_page']}")

    with tab_progress:
        st.subheader("Tiến độ học tập")

        progress = load_progress()
        topics = progress.get("topics", {})
        sessions = progress.get("sessions", [])

        total_questions = sum(
            stats["attempts"] for stats in topics.values()
        )
        total_correct = sum(
            stats["correct"] for stats in topics.values()
        )
        overall_accuracy = (
            total_correct / total_questions
            if total_questions
            else 0
        )
        total_minutes = sum(
            session["duration_seconds"] for session in sessions
        ) / 60

        column1, column2, column3 = st.columns(3)
        column1.metric("Câu đã làm", total_questions)
        column2.metric("Tỷ lệ đúng", f"{overall_accuracy:.0%}")
        column3.metric("Thời gian làm quiz", f"{total_minutes:.1f} phút")

        if not topics:
            st.info("Chưa có kết quả quiz để hiển thị.")
        else:
            st.markdown("### Kết quả theo chủ đề")

            for topic, stats in topics.items():
                accuracy = stats["correct"] / stats["attempts"]

                st.write(
                    f"**{topic}** — đúng {stats['correct']}/"
                    f"{stats['attempts']} câu ({accuracy:.0%})"
                )
                st.progress(accuracy)

                if stats["wrong_pages"]:
                    st.caption(
                        f"Trang nên xem lại: {stats['wrong_pages']}"
                    )

        weak_topics = get_weak_topics()

        st.markdown("### Chủ đề nên ôn")

        if weak_topics:
            for item in weak_topics:
                st.warning(
                    f"{item['topic']}: đúng {item['accuracy']:.0%} "
                    f"sau {item['attempts']} câu. "
                    f"Trang nên xem lại: {item['wrong_pages']}"
                )
        else:
            st.info(
                "Chưa có chủ đề nào đủ dữ liệu để đánh dấu cần ôn."
            )

        st.markdown("### Lịch sử các lượt quiz")

        if not sessions:
            st.info("Chưa có lượt quiz nào được lưu.")
        else:
            for session in reversed(sessions[-10:]):
                with st.expander(
                    f"{session['time']} — {session['topic']}"
                ):
                    st.write(
                        f"Điểm: {session['correct_count']}/"
                        f"{session['question_count']} câu đúng"
                    )
                    st.write(f"Tỷ lệ đúng: {session['accuracy']:.1f}%")
                    st.write(
                        f"Thời gian: "
                        f"{session['duration_seconds']:.0f} giây"
                    )

            st.markdown("### So với lượt trước cùng chủ đề")

            for topic in topics:
                topic_sessions = [
                    session
                    for session in sessions
                    if session["topic"].casefold() == topic.casefold()
                ]

                if len(topic_sessions) >= 2:
                    previous_accuracy = topic_sessions[-2]["accuracy"]
                    latest_accuracy = topic_sessions[-1]["accuracy"]
                    change = latest_accuracy - previous_accuracy

                    st.metric(
                        topic,
                        f"{latest_accuracy:.1f}%",
                        delta=f"{change:+.1f} điểm phần trăm",
                    )