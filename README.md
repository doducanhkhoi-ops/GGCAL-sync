# FTU HCMC Schedule to Google Calendar

Công cụ tự động cào thời khóa biểu từ cổng đào tạo FTU Cơ sở 2 và đồng bộ trực tiếp vào Google Calendar, chạy tự động qua GitHub Actions hoặc chạy thủ công trên máy.

## Tính năng

- Tự động đăng nhập cổng QLĐT bằng Selenium và lấy thời khóa biểu tuần.
- Quét liên tục 6 tuần tiếp theo để cập nhật lịch học mới.
- Tự phát hiện ca học bù (dựa trên class `tkb-daybu` hoặc tên môn) để gắn tiền tố `[HỌC BÙ]` và đổi màu sang tím.
- Kiểm tra trùng lặp trước khi thêm, tránh tạo nhiều sự kiện cùng giờ.
- Hẹn sẵn 2 mốc thông báo trước giờ học: 120 phút và 30 phút.
- Tích hợp GitHub Actions chạy định kỳ 2 lần mỗi ngày (07:00 và 18:00 giờ Việt Nam).

## Cấu trúc thư mục

```text
├── .github/workflows/
│   └── sync_calendar.yml    # Workflow chạy định kỳ trên GitHub Actions
├── main_sync.py             # Script chính quét thời khóa biểu và đẩy vào lịch
├── auth.py                  # Script xác thực tài khoản Google lần đầu
├── requirements.txt         # Danh sách thư viện cần cài đặt
├── .env.example             # File mẫu chứa thông tin tài khoản sinh viên
└── README.md
```

## Yêu cầu môi trường

- Python 3.10 trở lên
- Google Chrome và ChromeDriver (Selenium 4 tự động quản lý driver)

## Hướng dẫn cài đặt

### 1. Cài đặt thư viện

```bash
pip install -r requirements.txt
```

### 2. Cấu hình Google Cloud API

1. Truy cập [Google Cloud Console](https://console.cloud.google.com/) và tạo một dự án mới (ví dụ `FTU-Calendar`).
2. Vào **APIs & Services** > **Library**, tìm **Google Calendar API** và bấm **Enable**.
3. Vào **Google Auth Platform** > **Audience** (hoặc **OAuth consent screen**):
   - Chọn loại ứng dụng: **External**.
   - Vào **Branding**, điền tên app, email liên hệ, và thêm domain `github.com` vào mục **Authorized domains**.
   - Chuyển trạng thái **Publishing status** sang **In production** (bấm **Publish app**). Bước này bắt buộc để refresh token không bị Google thu hồi sau 7 ngày.
4. Vào **Clients** (hoặc **Credentials**):
   - Bấm **Create Credentials** > chọn **OAuth client ID**.
   - Application type: chọn **Desktop app**.
   - Tải file JSON về, đổi tên thành `credentials.json` và lưu vào thư mục gốc của dự án.

### 3. Cấu hình tài khoản sinh viên và lấy token

1. Tạo file `.env` từ file mẫu:
   ```bash
   cp .env.example .env
   ```
2. Mở file `.env` và nhập thông tin:
   ```env
   STUDENT_ID=ma_sinh_vien
   STUDENT_PASS=mat_khau
   ```
3. Chạy file xác thực Google:
   ```bash
   python auth.py
   ```
   Trình duyệt sẽ mở ra trang đăng nhập Google. Chọn tài khoản của bạn, bấm Cho phép để cấp quyền truy cập Calendar. Khi hoàn tất, file `token.json` sẽ được tạo trong thư mục dự án.

4. Chạy thử đồng bộ lịch trên máy:
   ```bash
   python main_sync.py
   ```

## Thiết lập tự động qua GitHub Actions

Để script tự chạy mà không cần bật máy tính, bạn thiết lập trên kho mã nguồn GitHub:

1. Vào **Settings** > **Secrets and variables** > **Actions** trong repository.
2. Thêm 4 secret tương ứng:
   - `STUDENT_ID`: Mã sinh viên.
   - `STUDENT_PASS`: Mật khẩu tài khoản sinh viên.
   - `CREDENTIALS_JSON`: Toàn bộ nội dung file `credentials.json`.
   - `TOKEN_JSON`: Toàn bộ nội dung file `token.json`.
3. Chuyển sang tab **Actions**, chọn workflow **Auto Sync FTU Schedule to Google Calendar** và bấm **Run workflow** để kiểm tra lần chạy đầu tiên.

Từ các ngày tiếp theo, hệ thống sẽ tự động chạy vào lúc 07:00 sáng và 18:00 chiều mỗi ngày.

## Lưu ý

- Không commit các file chứa thông tin nhạy cảm (`.env`, `credentials.json`, `token.json`) lên kho lưu trữ công khai. File `.gitignore` đã có sẵn các mẫu để loại trừ những file này.
- Nếu bạn đổi mật khẩu cổng trường hoặc mật khẩu Google, hãy cập nhật lại các secret tương ứng trên GitHub.
