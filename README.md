# 🎓 FTU HCMC Schedule to Google Calendar Auto-Sync

> **Tự động hóa đồng bộ Thời khóa biểu từ Cổng Quản Lý Đào Tạo (QLĐT) FTU CS2 sang Google Calendar, hỗ trợ phát hiện lịch học bù và chạy ngầm 24/7 trên Cloud (GitHub Actions).**

---

## ✨ Tính Năng Nổi Bật

- 🔄 **Tự động hóa hoàn toàn 100%:** Tự động đăng nhập ngầm vào hệ thống quản lý đào tạo của trường, thu thập lịch học mà không cần can thiệp thủ công.
- 🟣 **Nhận diện thông minh Lịch Học Bù:** Tự động phát hiện các buổi học bù (`tkb-daybu`), gắn nhãn `[HỌC BÙ]` và đổi sang **màu Tím (Grape)** nổi bật trên Google Calendar.
- 📅 **Quét đa tuần (Multi-week Ahead):** Tự động chuyển tuần và quét trước 6–8 tuần tiếp theo của học kỳ, đảm bảo bạn không bao giờ bỏ lỡ lịch học sắp tới.
- ⏰ **Cài đặt nhắc nhở tự động:** Tự động thiết lập chuông thông báo trên điện thoại trước giờ học **30 phút** và **2 tiếng**.
- 🛡️ **Cơ chế chống trùng lịch:** Kiểm tra sự kiện đã tồn tại trước khi thêm mới, tránh bị lặp sự kiện rác khi chạy nhiều lần.
- ☁️ **Chạy ngầm 24/7 trên Cloud (GitHub Actions):** Tự động chạy mỗi ngày lúc **07:00 sáng** và **18:00 chiều** ngay cả khi bạn tắt máy tính.
- 🔒 **Bảo mật tuyệt đối:** Mã sinh viên, mật khẩu và token Google được mã hóa an toàn qua **GitHub Secrets**, không lưu trực tiếp trong mã nguồn.

---

## 🚀 Hướng Dẫn Cài Đặt (Cho người dùng mới)

### 1. Fork hoặc Clone dự án
Tải mã nguồn về máy hoặc bấm nút **Fork** ở góc trên bên phải để sao chép dự án về tài khoản của bạn.

### 2. Chuẩn bị Google Calendar API
1. Truy cập [Google Cloud Console](https://console.cloud.google.com/) và tạo một dự án mới (ví dụ: `FTU-Calendar`).
2. Vào thư viện API, tìm kiếm **Google Calendar API** và nhấn **Enable** (Bật).
3. Vào mục **Google Auth Platform / OAuth consent screen**:
   - Chọn loại ứng dụng: **External**.
   - Điền tên ứng dụng và email của bạn.
   - Thêm email của bạn vào danh sách **Test Users**.
4. Vào mục **Clients / Credentials** -> Bấm **Create Credentials** -> Chọn **OAuth client ID** -> Loại: **Desktop app**.
5. Tải file JSON về máy và đổi tên thành `credentials.json`.

### 3. Cấp quyền lần đầu trên máy tính
1. Cài đặt các thư viện cần thiết:
   ```bash
   pip install -r requirements.txt
   ```
2. Tạo file `.env` từ `.env.example` và điền tài khoản sinh viên:
   ```env
   STUDENT_ID=ma_sinh_vien_cua_ban
   STUDENT_PASS=mat_khau_cua_ban
   ```
3. Đặt file `credentials.json` vào chung thư mục với `main_sync.py`.
4. Chạy script để cấp quyền và đồng bộ lần đầu:
   ```bash
   python main_sync.py
   ```
   Trình duyệt sẽ mở ra để bạn xác thực tài khoản Google. Sau khi cấp quyền xong, file `token.json` sẽ tự động được tạo.

---

## ☁️ Thiết Lập Chạy Tự Động 24/7 Trên GitHub Actions

1. Trên kho lưu trữ GitHub của bạn, vào **Settings** -> **Secrets and variables** -> **Actions**.
2. Thêm 4 Secret sau:
   - `STUDENT_ID`: Mã sinh viên của bạn.
   - `STUDENT_PASS`: Mật khẩu tài khoản sinh viên.
   - `CREDENTIALS_JSON`: Toàn bộ nội dung trong file `credentials.json`.
   - `TOKEN_JSON`: Toàn bộ nội dung trong file `token.json`.
3. Vào tab **Actions** -> Chọn workflow **Auto Sync FTU Schedule to Google Calendar** -> Bấm **Run workflow** để kiểm tra chạy thử nghiệm!

---

## ⚠️ Lưu Ý Bảo Mật
- Tuyệt đối **KHÔNG** đưa các file `.env`, `credentials.json`, `token.json` hay ảnh chụp màn hình chứa thông tin cá nhân lên GitHub.
- Các file nhạy cảm đã được cấu hình trong `.gitignore` để tránh bị đẩy nhầm.

---

## 📄 Bản Quyền
Dự án được xây dựng phục vụ mục đích học tập và hỗ trợ sinh viên quản lý thời gian học tập hiệu quả.
