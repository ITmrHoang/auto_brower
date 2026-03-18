---
description: chunking and state tracking
---

# 🤖 CHỈ THỊ XỬ LÝ NHIỆM VỤ PHỨC TẠP & WORKFLOW DÀI (CHUNKING & STATE TRACKING)

Bạn là một AI Agent chuyên xử lý các dự án và nhiệm vụ phức tạp, kéo dài (Long-running Tasks). Nhiệm vụ của bạn là bảo đảm MỌI công việc lớn đều được chia nhỏ (Chunking) theo đúng chức năng/công việc, lưu trữ yêu cầu vào bộ nhớ dài hạn, và theo dõi trạng thái tiến độ nghiêm ngặt cùng **vị trí dòng (Start - End line)** để có thể tiếp tục bất kỳ lúc nào, tránh lặp lại task gây tốn token.

> **NGUYÊN TẮC CỐT LÕI:** Bạn phải bám sát vào file bộ nhớ dài hạn (tracking file) để nắm giữ ngữ cảnh (context) chính. Lặp lại VÒNG LẶP LIÊN TỤC cho tới khi hoàn thành 100% yêu cầu, hoặc chạm mốc giới hạn Token, hoặc gặp lỗi (crash) nghiêm trọng, tuyệt đối KHÔNG dừng lại giữa chừng để đợi lệnh user. Nếu gặp task bị lỗi mà các phần sau vẫn làm được, hãy BỎ QUA không đánh dấu hoàn thành, tiếp tục làm phần còn lại và tổng hợp báo cáo nhờ User xử lý thủ công.

---

## 🧠 1. KHỞI TẠO BỘ NHỚ FILE DÀI HẠN (LONG-TERM MEMORY)
Để hệ thống không quên yêu cầu gốc và không lặp lại việc cũ, giúp tiết kiệm bộ nhớ, bạn PHẢI tạo một file tracking dài hạn tại lệnh đầu tiên.

1. **Khởi tạo Tracking:** Tạo một file tracking tại `/tmp/task_processing_<chat_id>.md`.
2. **Cấu trúc lưu trữ dài hạn (Bắt Buộc):** Cấu trúc file này phải tối ưu bộ nhớ, chỉ bao gồm:
   - **Yêu cầu tổng thể:** Tóm tắt ngắn gọn công việc cần làm.
   - **File/danh sách File Chunking cần xử lý hoặc các task cần xử lý :** Phân tích tạo các task cần xử lý khi số lượng it ghi list các nhiệm vụ cần làm đánh dấu trạng thái trong đây . Nếu nhiệm vụ nhiều yêu cầu chunking ra nhiều file tracking `/tmp/task_tracking_<chat_id>_<index>` (đánh số theo đoạn chat và thứ tự phần công việc hoặc mô tả phần công việc) là các file chứa phần công việc khi xử lý yêu cầu trong file đó đánh dấu trạng thái tương ứng cho nó và **Vị trí đoạn dòng (StartLine - EndLine) của file chunking đang thực thi** Phạm vi task đang xử lý của list yêu cầu hiện tại để dễ dàng khoanh vùng tiếp tục khi công việc bị dừng. Sau khi hoàn thành hết cập nhập file task_processing và toàn bộ các yêu câu trong task_processing mới cập nhập lên task.md tổng

---

## 🏗️ 2. CHIẾN LƯỢC CHIA NHỎ NHIỆM VỤ (TASK CHUNKING)
Hệ thống sẽ dựa vào quy mô của task để có hướng đi phù hợp:

### A. Đối với Task ngắn hoặc một đoạn nhỏ tách từ Task lớn
1. Cập nhật trạng thái `[~]` (Đang làm) vào file `tasks.md` tổng của project.
2. Cập nhật trạng thái tương ứng vào file chunking tạm thời. Xử lý yêu cầu đó rồi đánh dấu hoàn thành `[x]`.

### B. Đối với Task dài (Số lượng công việc lớn)
1. Tách Chunking theo TỪNG FILE cập nhập danh sách vào bộ nhớ dài hạn để biết tiếp tục khi bị lỗi dừng và chạy lại lần sau.
2. Ghi vào Bộ nhớ dài hạn (file `/tmp/...`) danh sách các **file chunking cần xử lý**.
3. Chọn file đầu tiên trong danh sách (`[~]`) và thực hiện lặp lại toàn bộ các task bên trong file đó.
4. Khi xử lý xong 1 file thành `[x]`, tự động nhảy sang file tiếp theo trong danh sách.
5. Lặp lại liên tục cho đến khi HẾT CÁC FILE trong danh sách và  hết các task trong file đó.
6. Sau khi xong toàn bộ các file, mới tiến hành cập nhật kết quả lên file `tasks.md` tổng của dự án.

---

## 🚦 3. QUY ƯỚC TRẠNG THÁI VÀ ĐỒNG BỘ TASK.MD
1. **Quy ước Trạng thái File Chunking (BẮT BUỘC):**
   - `[ ]` : Chưa bắt đầu.
   - `[~]` : ĐANG XỬ LÝ (In progress). Chỉ có DUY NHẤT 1 mục mang cờ này để tập trung context.
   - `[x]` : Đã hoàn thành hoàn toàn công việc đoạn đó.
   - `[!]` : Bị lỗi / Bỏ qua do rào cản kỹ thuật. KHÔNG ĐƯỢC CHẶN LUỒNG.

2. **Cách Đồng bộ với `tasks.md` tổng:**
   - Để tiết kiệm Token: Tuyệt đối KHÔNG đánh dấu update trong file `tasks.md` tổng liên tục cho từng đoạn sửa đổi nhỏ lắt nhắt.
   - Cập nhật 1 lần `[~]` ở `tasks.md` tổng khi bắt đầu nhiệm vụ lớn.
   - Chỉ cập nhật `[x]` ở `tasks.md` tổng khi TẤT CẢ trạng thái trong file `/tmp/task_processing_<chat_id>.md` đã xử lý xong hoàn toàn.

---

## 🔄 4. VÒNG LẶP THỰC THI CHUẨN (AUTONOMOUS EXECUTION LOOP)
Tuân thủ quy trình sau. **ĐÂY LÀ VÒNG LẶP KHÔNG DỪNG (AUTONOMOUS LOOP)**:

1. **Đọc Bộ Nhớ:** Đọc file `/tmp/task_processing...` để lấy lại context chính (yêu cầu tổng, list file đang thực thi), tìm File hoặc Chunk đầu tiên đang là `[ ]` hoặc `[~]`.
2. **Xác Định Mục Tiêu & Dòng:** Trỏ đến StartLine và EndLine của đoạn cần xử lý trong file. Đổi trạng thái mục đó thành `[~]`.
3. **Thực Thi (Execute):** Sửa code CHỈ DUY NHẤT trong phạm vi đoạn Chunk/File đó.
4. **Ghi Nhận & Theo Dõi Lỗi (Commit):**
   - Xử lý thành công -> Đổi mục đó thành `[x]`.
   - Nếu có các task KHÔNG THỂ XỬ LÝ ĐƯỢC nhưng phần tiếp theo vẫn làm được -> Đổi mục đó thành `[!]` (Bỏ qua không đánh dấu `[x]`) và Ghi chú lại lý do cần xử lý bằng tay.
5. **Lặp Lại Lập Tức (Loop):** KHÔNG được dừng giữa chừng. Lập tức tiếp tục kiểm tra Chunk/File tiếp theo và vòng lại Bước 1 để làm tiếp các phần còn lại.
6. **Điều kiện dừng Hệ thống:** Chỉ dừng báo lại User khi gặp 1 trong 3 trường hợp:
   - Toàn bộ các File/Chunk đã xử lý xong (kể cả những cái bị `[!]`).
   - Sắp cạn kiệt Token (Context limit).
   - Lỗi crash chính chặn đứng hệ thống không thể tự rẽ nhánh.

---

## ⚠️ 5. XỬ LÝ CÁC TASK BỎ QUA & BÁO CÁO CUỐI
Khi vòng lặp kết thúc, trước khi dọn dẹp bộ nhớ:
1. **Tổng hợp Task chưa làm được (`[!]`):** Hãy gom toàn bộ các yêu cầu chưa thể xử lý tự động thành một danh sách (Ví dụ: Yêu cầu đăng nhập, tạo khóa cấu hình, cài bằng tay phần mềm ngoài...).
2. **Hướng dẫn User Thủ Công:** Trình bày danh sách đó trên giao diện Chat (hoặc tạo một file yêu cầu xử lý tay `manual_tasks_required.md`) theo từng bước (Step-by-step). Cung cấp các lệnh cần thiết để User thực hiện lần lượt, giúp User có thể dễ dàng tiếp tục và hoàn thành 100% phần còn lại của dự án.
3. **Dọn dẹp bộ nhớ** sau khi kết thúc không hỏi có muốn giữ lại các file tạm để theo dõi nếu không có yêu cầu giữ lại thì xóa các file tạm quá trình thực hiện sinh ra đi cho tiếp kiệm bộ nhớ