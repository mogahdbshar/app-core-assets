import os
import json
import base64
import requests
import re
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

M3U_URL = os.environ.get("IPTV_URL")
GITHUB_TOKEN = os.environ.get("GH_TOKEN")
REPO = os.environ.get("GITHUB_REPOSITORY")
FILE_PATH = "system_config.dat"

SECRET_KEY = b'MySecretKeyForIPTVChannels4000!!' 
IV = b'16BytesLongIV!!!'

def parse_m3u(url):
    print("جاري محاولة جلب القنوات من الرابط...")
    try:
        response = requests.get(url, timeout=60)
        print(f"استجابة سيرفر القنوات: {response.status_code}")
        if response.status_code != 200: return None
        
        lines = response.text.split('\n')
        channels = []
        current_ch = {}
        for line in lines:
            line = line.strip()
            if line.startswith('#EXTINF:'):
                name_match = re.search(r',([^,]+)$', line)
                logo_match = re.search(r'tvg-logo="([^"]+)"', line)
                cat_match = re.search(r'group-title="([^"]+)"', line)
                current_ch['name'] = name_match.group(1).strip() if name_match else "Unknown"
                current_ch['logo'] = logo_match.group(1).strip() if logo_match else ""
                current_ch['category'] = cat_match.group(1).strip() if cat_match else "General"
            elif line.startswith('http://') or line.startswith('https://'):
                current_ch['url'] = line
                channels.append(current_ch)
                current_ch = {}
        return channels
    except Exception as e:
        print(f"خطأ في قراءة الرابط: {e}")
        return None

def encrypt_data(data):
    json_str = json.dumps(data).encode('utf-8')
    cipher = AES.new(SECRET_KEY, AES.MODE_CBC, IV)
    return base64.b64encode(cipher.encrypt(pad(json_str, AES.block_size))).decode('utf-8')

channels_list = parse_m3u(M3U_URL)
if channels_list:
    print(f"تم العثور على {len(channels_list)} قناة. جاري التشفير والرفع...")
    encrypted_text = encrypt_data(channels_list)
    url = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    
    res = requests.get(url, headers=headers)
    sha = res.json().get('sha') if res.status_code == 200 else None
    
    payload = {
        "message": "Auto Sync Config",
        "content": base64.b64encode(encrypted_text.encode('utf-8')).decode('utf-8'),
    }
    if sha: payload["sha"] = sha
    
    upload_res = requests.put(url, json=payload, headers=headers)
    print(f"استجابة جيثب عند الرفع: {upload_res.status_code}")
    if upload_res.status_code not in [200, 201]:
        print(f"تفاصيل الخطأ من جيثب: {upload_res.text}")
else:
    print("❌ لم يتم العثور على أي قنوات داخل الرابط! تأكد من أن الرابط يعمل حالياً.")
