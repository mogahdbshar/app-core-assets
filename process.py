import os
import json
import base64
import requests
import gzip
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

# الإعدادات
HOST = "http://12k-service.org"
USERNAME = "uiuj63jbc8"
PASSWORD = "0n5iejexqg"
GITHUB_TOKEN = os.environ.get("GH_TOKEN")
REPO = os.environ.get("GITHUB_REPOSITORY")
FILE_PATH = "system_config.dat"
SECRET_KEY = b'MySecretKeyForIPTVChannels4000!!' 
IV = b'16BytesLongIV!!!'

def fetch_live_channels():
    # إضافة مسار الـ API الصحيح لجلب القنوات
    api_url = f"{HOST}/player_api.php?username={USERNAME}&password={PASSWORD}&action=get_live_streams"
    headers = {'User-Agent': 'Mozilla/5.0 (Android 10; Mobile; rv:91.0) Gecko/91.0 Firefox/91.0'}
    
    print("جاري الاتصال بسيرفر الأكستريم...")
    try:
        response = requests.get(api_url, headers=headers, timeout=60)
        if response.status_code != 200:
            print(f"فشل الاتصال: {response.status_code}")
            return None
            
        raw_data = response.json()
        if isinstance(raw_data, list):
            channels = []
            for ch in raw_data:
                # التعديل المطلوب: تنسيق الرابط ليصبح رابط بث مباشر قياسي
                stream_url = f"{HOST}/live/{USERNAME}/{PASSWORD}/{ch.get('stream_id')}.m3u8"
                
                channels.append({
                    'name': ch.get('name', 'Unknown'),
                    'logo': ch.get('stream_icon', ''),
                    'category': str(ch.get('category_id', 'General')),
                    'url': stream_url
                })
            return channels
        return None
    except Exception as e:
        print(f"خطأ: {e}")
        return None

def encrypt_and_compress_data(data):
    json_bytes = json.dumps(data).encode('utf-8')
    compressed_bytes = gzip.compress(json_bytes)
    # استخدام التشفير كما هو معتمد في تطبيقك
    cipher = AES.new(SECRET_KEY, AES.MODE_CBC, IV)
    encrypted_bytes = cipher.encrypt(pad(compressed_bytes, AES.block_size))
    return base64.b64encode(encrypted_bytes).decode('utf-8')

# تنفيذ العملية
channels_list = fetch_live_channels()
if channels_list:
    print(f"تم جلب {len(channels_list)} قناة. جاري المعالجة والرفع...")
    
    final_text = encrypt_and_compress_data(channels_list)
    
    # إعدادات الرفع إلى GitHub
    url = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"
    gh_headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    
    res = requests.get(url, headers=gh_headers)
    sha = res.json().get('sha') if res.status_code == 200 else None
    
    payload = {
        "message": "Update Channels With M3U8 Format",
        "content": base64.b64encode(final_text.encode('utf-8')).decode('utf-8')
    }
    if sha: payload["sha"] = sha
        
    upload_res = requests.put(url, json=payload, headers=gh_headers)
    if upload_res.status_code in [200, 201]:
        print("✅ تم تحديث ملف القنوات بنجاح مع الروابط الجديدة.")
    else:
        print(f"فشل الرفع: {upload_res.text}")
else:
    print("❌ تعذر جلب البيانات.")
