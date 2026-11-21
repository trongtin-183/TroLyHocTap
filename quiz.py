import json
from retriever import retrieve_chunks
from llm_service import ask_gemini


def generate_quiz(topic, chunks, num_questions=5):
    relevant_chunks = retrieve_chunks(topic, chunks, top_k=5)

    if not relevant_chunks:
        return []

    context = "\n\n".join(
        f"[Trang {chunk['page']}]\n{chunk['text']}"
        for chunk in relevant_chunks
    )

    available_pages = sorted({
        chunk["page"] for chunk in relevant_chunks
    })

    prompt = f"""
Tạo tối đa {num_questions} câu hỏi trắc nghiệm về chủ đề: {topic}.

Chỉ sử dụng thông tin trong tài liệu bên dưới.
Mỗi câu có 4 lựa chọn A, B, C, D và chỉ có một đáp án đúng.
source_page phải là số trang có trong danh sách này: {available_pages}.
Nếu tài liệu không đủ thông tin, hãy tạo ít câu hơn.
Chỉ trả về JSON hợp lệ, không thêm dấu ``` hoặc lời dẫn.

Mẫu JSON:
[
  {{
    "question": "Nội dung câu hỏi",
    "choices": {{
      "A": "Lựa chọn A",
      "B": "Lựa chọn B",
      "C": "Lựa chọn C",
      "D": "Lựa chọn D"
    }},
    "correct_answer": "A",
    "explanation": "Giải thích đáp án dựa trên tài liệu",
    "source_page": 3
  }}
]

Tài liệu:
{context}
"""

    response_text = ask_gemini(prompt).strip()

    if response_text.startswith("```"):
        response_text = response_text.replace("```json", "", 1)
        response_text = response_text.replace("```", "").strip()

    try:
        questions = json.loads(response_text)
    except json.JSONDecodeError as error:
        raise ValueError("Gemini chưa trả quiz theo đúng định dạng JSON.") from error

    for question in questions:
        question["topic"] = topic

        if question.get("source_page") not in available_pages:
            question["source_page"] = available_pages[0]

    return questions[:num_questions]