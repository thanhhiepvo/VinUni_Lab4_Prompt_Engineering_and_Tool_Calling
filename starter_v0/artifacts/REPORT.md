# Day 04 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. **Xong trước 16:30** để làm tài liệu phụ trợ khi demo. Có thể làm thành poster HTML/SVG (`artifacts/poster.html` / `poster.svg`) để show cho team cùng zone.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v3, failure, eval, chat) dựa trên log thật. **Có thể hoàn thiện sau buổi debate để nộp bài.**

## Team

- Team: 5
- Members: Võ Thanh Hiệp - 2A202600836, Nguyễn Công Tuấn Anh - 2A202600836
- Provider/model: OpenAI / gpt-4o-mini

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

Research agent: hỗ trợ tìm kiếm tin tức thời sự/công nghệ, tra cứu thảo luận/tweet trên Twitter, đọc hiểu và tóm tắt bài viết từ URL cụ thể, tra cứu chính sách công ty, tìm kiếm tài liệu khoa học trên arXiv và xuất bản bản tin lên kênh Telegram sau khi có xác nhận từ người dùng.

**Link dùng thử (deploy):**

URL: `http://localhost:8501` (chạy trên Streamlit local dashboard)

## A2. Tool agent có

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| clarify | hỏi lại người dùng khi thiếu thông tin (handle, URL, confirmation) | không |
| lookup | tìm kiếm bài viết, tin tức trên web | không |
| social_search | tìm kiếm các bài tweet/thảo luận trên Twitter theo từ khóa | không |
| timeline | lấy các tweet mới nhất từ tài khoản cụ thể bằng screenname | không |
| fetch | đọc nội dung bài viết từ URL cụ thể | không |
| policy | tra cứu các quy định, chính sách nội bộ của công ty | không |
| papers | tìm kiếm bài báo khoa học học thuật trên arXiv | có (nhóm thêm) |
| paper_text | lấy và trích xuất nội dung từ bài báo arXiv cụ thể | có (nhóm thêm) |
| resolve_twitter_handle | phân giải tên người nổi tiếng sang Twitter handle chính xác | có (nhóm thêm) |
| send | xuất bản bản tin lên Telegram | không |

## A3. Câu hỏi mẫu để thử

1. "Tin tức AI hôm nay có gì nổi bật không?"
2. "Tìm kiếm các bài báo trên arXiv về kỹ thuật Prompt Engineering của LLM."
3. "Đăng bản tin này lên Telegram giúp mình nhé." (Sẽ kích hoạt luồng xác nhận qua clarify yes_no)
4. "Cho mình xem 5 tweet mới nhất của Andrej Karpathy." (Sẽ tự động ánh xạ sang handle @karpathy)

---

# PHẦN B — Chi tiết / Bằng chứng

## B1. Version Evidence

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
|---|---|---|---|---|---|
| v0 | baseline | No optimization yet | 0.00 (base) | 0.70 (base) | `v0_B_base_openai_20260602T142654960548.json` |
| v1 | `system_prompt.md` | Add routing guidelines and Vietnamese templates | 0.70 (base) | 0.75 (base) | `v1_B_base_openai_20260602T150208816195.json` |
| v2 | `system_prompt.md` | Add out of scope guidelines and boundary check constraints | 0.75 (base) | 0.80 (base) | `v2_B_base_openai_20260602T150405372914.json` |
| v3 | `tools.yaml` | Add resolve_twitter_handle tool and mapping dictionary | 0.80 (base) | 0.60 (base) | `v3_B_base_openai_20260602T152244417195.json` |
| v4.1 | `system_prompt.md` | Enforce name-to-handle conversion & multi-turn drop constraints | 0.60 (base) | 1.00 (base) | `v4.1_B_base_openai_20260602T152834874233.json` |
| v4.2 | `system_prompt.md` | Handle confirmation response types explicitly in multi-turn | 0.90 (group) | 1.00 (group) | `v4.2_B_group_openai_20260602T153238616169.json` |

## B2. Failure Analysis

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| M06_switch_tool | `wrong_tool` | `lookup` + `social_search` | Model gọi `social_search` mặc dù người dùng đã yêu cầu bỏ Twitter | Cập nhật system prompt yêu cầu tôn trọng triệt để lệnh bỏ/ngưng sử dụng một nền tảng hoặc công cụ |
| G08_multi_clarify_telegram_confirm | `wrong_boundary` | `clarify` (với `yes_no`) | Model tiếp tục hỏi xác nhận thay vì gọi `send` trực tiếp khi người dùng đã đồng ý gửi | Bổ sung hướng dẫn chuyển tiếp các cụm từ đồng ý (như "Xác nhận gửi đi") thành cuộc gọi `send(confirmed=true)` trực tiếp |

## B3. Team Eval Cases

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
| G01_single_timeline_karpathy | Ánh xạ Karpathy -> karpathy và gọi timeline | `timeline(screenname="karpathy")` | PASS |
| G02_single_policy_data_privacy | Kiểm tra chính sách bảo mật dữ liệu/khóa API | `policy(policy_area="data_privacy")` | PASS |
| G03_single_papers_agent | Tìm kiếm các bài báo arXiv về AI agents | `papers(query="AI agents")` | PASS |
| G04_single_clarify_no_url | Yêu cầu URL khi người dùng nói tóm tắt chung chung | `clarify(response_type="text")` | PASS |
| G05_single_parallel_fetch_policy | Đọc URL đồng thời kiểm tra quy định viết báo | `fetch` + `policy(policy_area="ai_research")` | PASS |
| G06_multi_carryover_karpathy | Giữ handle của Karpathy qua turn sau, đổi limit | `timeline(screenname="karpathy", limit=10)` | PASS |
| G07_multi_switch_web_to_arxiv | Bỏ tìm web và chuyển hẳn sang arXiv | `papers(query="LLM")` | PASS |
| G08_multi_clarify_telegram_confirm | Thực hiện gửi khi nhận xác nhận ở turn 2 | `send(confirmed=true)` | PASS |
| G09_multi_carryover_policy | Giữ nguyên area policy, đổi câu hỏi chi tiết | `policy(policy_area="data_privacy", query="...")` | PASS |
| G10_multi_carryover_fetch_url | Giữ nguyên URL phân giải được từ lượt trước để fetch | `fetch(url="https://openai.com/blog/gpt-4o")` | PASS |

## B4. Live Chat Evidence

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
| 1 | "Tin tức AI nổi bật hôm nay là gì?" | `lookup` với topic: `news`, timeframe: `day` | `v4.2` | Trả về tổng hợp 5 tin tức AI hàng đầu hôm nay và lưu file transcript log. |

## B5. Bonus Evidence

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| send (Telegram) | `starter_v0/artifacts/system_prompt.md` | Luồng xác nhận trước khi gửi hoạt động ổn định nhờ `clarify` response_type và logic `confirmed=True`. | Model có thể nhầm lẫn giữa việc viết nháp bản tin với gửi thật nếu không phân biệt kỹ turn xác nhận. Cần chặn chặt chẽ. |
| arXiv/company policy | `starter_v0/tools/` | Tích hợp thành công 3 tool mới (`papers`, `paper_text`, `policy`) vào yaml/code và phân loại chính xác các policy area. | Model cần phân biệt rõ ranh giới giữa việc tra cứu ngoài web (`lookup`) và tra cứu policy nội bộ để tránh gọi nhầm. |
| UI | `starter_v0/app.py` | Dashboard Streamlit tích hợp Live Chat và Analytics với biểu đồ tiến độ lịch sử và inspector trực quan từng case. | Rerung trong Streamlit có thể làm mất một phần state nếu không thiết kế session_state cẩn thận. |

## B6. Reflection

- **Which fixes belonged in `system_prompt.md`?**
  Các quy tắc về ranh giới xác nhận gửi đi, xử lý lệnh drop/bỏ nguồn tin từ người dùng, các quy chuẩn template tiếng Việt, và bảng ánh xạ tên sang Twitter handle.
- **Which fixes belonged in `tools.yaml`?**
  Cải tiến mô tả tham số cho các công cụ (như yêu cầu screenname không chứa `@` của tool `timeline`) và danh sách các lựa chọn cụ thể của `policy_area`.
- **Which failure needed manual review instead of automatic grading?**
  Các câu trả lời mang tính chất từ chối câu hỏi ngoài phạm vi hoặc giải thích trực tiếp (như tính toán toán học, trả lời metadata về bản thân), do cấu trúc so khớp tự động chỉ chấm trên tool calls dự kiến.
- **What would you improve next?**
  Xây dựng cơ chế phân giải tên người dùng linh hoạt hơn bằng cách cho phép model tự động gọi `resolve_twitter_handle` trước khi lấy timeline thay vì chỉ dựa vào hardcoded prompt mappings.
