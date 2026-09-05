import os
import sys
import time
import json
import re
import datetime
import requests
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_FILE = os.path.join(BASE_DIR, '.env')
TOKEN_FILE = os.path.join(BASE_DIR, 'token.json')
CREDENTIALS_FILE = os.path.join(BASE_DIR, 'credentials.json')

def log(msg):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}")

def get_valid_access_token():
    if not os.path.exists(TOKEN_FILE):
        raise FileNotFoundError("Chưa tìm thấy token.json. Vui lòng cấp quyền trước.")
    
    with open(TOKEN_FILE, 'r', encoding='utf-8') as f:
        token_data = json.load(f)

    # Test token
    test_res = requests.get(
        'https://www.googleapis.com/calendar/v3/calendars/primary',
        headers={'Authorization': f"Bearer {token_data['access_token']}"}
    )
    if test_res.status_code == 200:
        return token_data['access_token']

    # Expired, refresh
    log("Token đã hết hạn, đang tự động làm mới...")
    with open(CREDENTIALS_FILE, 'r', encoding='utf-8') as f:
        creds = json.load(f)
    info = creds.get('installed') or creds.get('web')
    
    refresh_res = requests.post('https://oauth2.googleapis.com/token', data={
        'client_id': info['client_id'],
        'client_secret': info['client_secret'],
        'refresh_token': token_data['refresh_token'],
        'grant_type': 'refresh_token'
    })
    
    if refresh_res.status_code == 200:
        new_token = refresh_res.json()
        token_data['access_token'] = new_token['access_token']
        with open(TOKEN_FILE, 'w', encoding='utf-8') as f:
            json.dump(token_data, f, indent=2)
        log("Làm mới Token thành công!")
        return token_data['access_token']
    else:
        raise Exception(f"Không thể làm mới token: {refresh_res.text}")

def parse_schedule_from_html(html_source):
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html_source, 'html.parser')

    week_text = ""
    for elem in soup.find_all(string=re.compile(r'từ ngày \d{2}/\d{2}/\d{4}')):
        week_text = elem
        break

    year = datetime.datetime.now().year
    if week_text:
        match = re.search(r'(\d{2})/(\d{2})/(\d{4})', week_text)
        if match:
            year = int(match.group(3))

    tables = soup.find_all('table')
    schedule_table = None
    for tbl in tables:
        if 'Thứ 2' in tbl.text and 'Tiết 1' in tbl.text:
            schedule_table = tbl
            break

    if not schedule_table:
        return []

    headers = []
    thead = schedule_table.find('thead')
    if thead:
        for th in thead.find_all('th'):
            headers.append(th.get_text(separator=' ').strip())
    else:
        for td in schedule_table.find('tr').find_all(['td', 'th']):
            headers.append(td.get_text(separator=' ').strip())

    rows = schedule_table.find('tbody').find_all('tr') if schedule_table.find('tbody') else schedule_table.find_all('tr')[1:]
    grid = {}
    events = []

    for r_idx, row in enumerate(rows):
        cells = row.find_all(['td', 'th'])
        c_idx = 0
        for cell in cells:
            while grid.get((r_idx, c_idx)):
                c_idx += 1

            rowspan = int(cell.get('rowspan', 1))
            colspan = int(cell.get('colspan', 1))

            for i in range(rowspan):
                for j in range(colspan):
                    grid[(r_idx + i, c_idx + j)] = True

            text = cell.get_text(separator='\n').strip()
            if 'Phòng:' in text:
                course_tag = cell.find('p', class_=re.compile(r'font-weight-bold'))
                course_name = course_tag.get_text(separator=' ').strip() if course_tag else "Môn học"
                course_name = re.sub(r'\s+', ' ', course_name)

                # Makeup detection
                is_makeup = (
                    'tkb-daybu' in cell.get('class', [])
                    or 'dạy bù' in course_name.lower()
                    or 'học bù' in course_name.lower()
                )

                room = ""
                teacher = ""
                group = ""
                start_time = ""
                end_time = ""

                for p in cell.find_all('p'):
                    p_text = p.get_text(separator=' ').strip()
                    if 'Phòng:' in p_text:
                        room = p_text.replace('Phòng:', '').strip()
                    elif 'GV:' in p_text:
                        teacher = p_text.replace('GV:', '').strip()
                    elif 'Nhóm:' in p_text:
                        group = p_text.replace('Nhóm:', '').strip()

                    time_match = re.search(r'(\d{1,2}:\d{2})\s*->\s*(\d{1,2}:\d{2})', p_text)
                    if time_match:
                        start_time = time_match.group(1).zfill(5)
                        end_time = time_match.group(2).zfill(5)

                day_header = headers[c_idx] if c_idx < len(headers) else ""
                date_match = re.search(r'(\d{1,2})/(\d{1,2})', day_header)
                if date_match:
                    day = int(date_match.group(1))
                    month = int(date_match.group(2))
                    date_str = f"{year:04d}-{month:02d}-{day:02d}"
                else:
                    date_str = ""

                events.append({
                    'course': course_name,
                    'group': group,
                    'room': room,
                    'teacher': teacher,
                    'is_makeup': is_makeup,
                    'date': date_str,
                    'start_time': start_time,
                    'end_time': end_time,
                    'day_header': day_header
                })

            c_idx += colspan

    return events

def fetch_multi_week_schedule(num_weeks=8):
    load_dotenv(ENV_FILE)
    student_id = os.environ.get('STUDENT_ID', '').strip().strip('\'"')
    student_pass = os.environ.get('STUDENT_PASS', '').strip().strip('\'"')

    if not student_id or not student_pass:
        raise ValueError("Chưa thiết lập STUDENT_ID hoặc STUDENT_PASS trong .env!")

    options = Options()
    options.add_argument('--headless')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--log-level=3')

    log("Đang khởi động trình duyệt ngầm...")
    try:
        driver = webdriver.Chrome(options=options)
    except Exception:
        from selenium.webdriver.edge.options import Options as EdgeOptions
        edge_options = EdgeOptions()
        edge_options.add_argument('--headless')
        edge_options.add_argument('--window-size=1920,1080')
        driver = webdriver.Edge(options=edge_options)

    all_events = []

    try:
        log("Đang truy cập Cổng đào tạo FTU...")
        driver.get('https://qldt.hcmc.ftu.edu.vn/#/home')
        time.sleep(4)

        log("Đang tự động đăng nhập...")
        inputs = driver.find_elements(By.TAG_NAME, 'input')
        user_input = pass_input = None
        for inp in inputs:
            if inp.get_attribute('type') == 'text' and not user_input:
                user_input = inp
            elif inp.get_attribute('type') == 'password' and not pass_input:
                pass_input = inp

        if not user_input or not pass_input:
            raise Exception("Không tìm thấy ô đăng nhập.")

        user_input.click()
        user_input.clear()
        for char in student_id:
            user_input.send_keys(char)
            time.sleep(0.02)

        pass_input.click()
        pass_input.clear()
        for char in student_pass:
            pass_input.send_keys(char)
            time.sleep(0.02)

        time.sleep(0.5)
        for btn in driver.find_elements(By.TAG_NAME, 'button'):
            if 'Đăng nhập' in btn.text:
                driver.execute_script("arguments[0].click();", btn)
                break

        time.sleep(6)

        log("Đang chuyển đến Thời khóa biểu dạng tuần...")
        elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Thời khóa biểu dạng tuần')]")
        if not elements:
            raise Exception("Không tìm thấy mục Thời khóa biểu.")

        for el in elements:
            try:
                driver.execute_script("arguments[0].click();", el)
                break
            except Exception:
                pass

        time.sleep(6)

        log(f"Bắt đầu quét thời khóa biểu {num_weeks} tuần tới...")
        for w in range(num_weeks):
            html = driver.page_source
            events = parse_schedule_from_html(html)
            log(f"- Tuần {w+1}: Thu thập được {len(events)} buổi học.")
            all_events.extend(events)

            if w < num_weeks - 1:
                next_arrows = driver.find_elements(By.CSS_SELECTOR, "i.fa-long-arrow-alt-right")
                if next_arrows:
                    driver.execute_script("arguments[0].click();", next_arrows[0])
                    time.sleep(2.5)
                else:
                    log("Không tìm thấy nút chuyển sang tuần tiếp theo nữa.")
                    break

        log(f"Tổng cộng đã thu thập {len(all_events)} buổi học qua {num_weeks} tuần!")
        return all_events

    finally:
        driver.quit()

def sync_to_google_calendar(events):
    access_token = get_valid_access_token()
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    log(f"Đang đồng bộ {len(events)} buổi học lên Google Calendar...")
    added_count = 0
    skipped_count = 0

    for e in events:
        if not e['date'] or not e['start_time'] or not e['end_time']:
            continue

        summary = f"[HỌC BÙ] {e['course']}" if e['is_makeup'] else e['course']
        start_iso = f"{e['date']}T{e['start_time']}:00+07:00"
        end_iso = f"{e['date']}T{e['end_time']}:00+07:00"

        # Check existing events to prevent duplicates
        check_res = requests.get(
            'https://www.googleapis.com/calendar/v3/calendars/primary/events',
            headers=headers,
            params={
                'timeMin': start_iso,
                'timeMax': end_iso,
                'singleEvents': True
            }
        )

        already_exists = False
        if check_res.status_code == 200:
            for item in check_res.json().get('items', []):
                if summary in item.get('summary', ''):
                    already_exists = True
                    break

        if already_exists:
            skipped_count += 1
            continue

        color_id = '3' if e['is_makeup'] else '9'

        event_body = {
            'summary': summary,
            'location': e['room'],
            'description': (
                f"Môn học: {e['course']}\n"
                f"Nhóm: {e['group']}\n"
                f"Phòng: {e['room']}\n"
                f"Giảng viên: {e['teacher']}\n"
                f"{'*** ĐÂY LÀ LỊCH HỌC BÙ ***' if e['is_makeup'] else ''}\n"
                f"Tự động đồng bộ từ Cổng Đào Tạo FTU HCMC"
            ),
            'start': {'dateTime': start_iso, 'timeZone': 'Asia/Ho_Chi_Minh'},
            'end': {'dateTime': end_iso, 'timeZone': 'Asia/Ho_Chi_Minh'},
            'colorId': color_id,
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': 30},
                    {'method': 'popup', 'minutes': 120}
                ]
            }
        }

        res = requests.post(
            'https://www.googleapis.com/calendar/v3/calendars/primary/events',
            headers=headers,
            json=event_body
        )

        if res.status_code in [200, 201]:
            log(f"-> Thêm mới: {summary} ({e['date']} {e['start_time']}-{e['end_time']})")
            added_count += 1
        else:
            log(f"Lỗi thêm sự kiện: {res.text}")

    log(f"Xong! Đã thêm mới: {added_count} buổi | Đã có sẵn: {skipped_count} buổi.")

def main():
    try:
        log("=== BẮT ĐẦU CHU TRÌNH TỰ ĐỘNG ĐỒNG BỘ LỊCH ===")
        # Quét trước 6 tuần tới (có thể tăng thêm trong cấu hình)
        events = fetch_multi_week_schedule(num_weeks=6)
        sync_to_google_calendar(events)
        log("=== ĐỒNG BỘ HOÀN TẤT THÀNH CÔNG ===")
    except Exception as ex:
        log(f"LỖI: {ex}")

if __name__ == '__main__':
    main()
