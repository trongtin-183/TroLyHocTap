# Trợ lý học tập theo tài liệu môn học

Ứng dụng hỗ trợ sinh viên học và ôn tập dựa trên nội dung trong tài liệu PDF.

## Chức năng

- Tải tài liệu PDF lên và hỏi đáp theo nội dung tài liệu.
- Hiển thị câu trả lời cùng các đoạn trích và số trang nguồn.
- Tạo câu hỏi trắc nghiệm theo chủ đề.
- Chấm đáp án và giải thích câu trả lời.
- Lưu điểm, thời lượng làm quiz và lịch sử theo chủ đề.
- Gợi ý chủ đề cần ôn dựa trên kết quả quiz.

## Công nghệ

- Python
- Streamlit
- PyMuPDF
- Gemini API

## Cài đặt

Cần có Python và một API key của Gemini.

Mở Terminal trong thư mục dự án, tạo môi trường Python riêng:

```powershell
python -m venv .venv


- Lệnh cài thư viện: python -m pip install -r requirements.txt
- Hướng dẫn tạo .env và dòng mẫu GEMINI_API_KEY=your_api_key_here — không ghi key thật
- Lệnh chạy app: python -m streamlit run web_app.py