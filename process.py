import os
import json
import base64
import requests
import gzip
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

# إعدادات الروابط المستخرجة تلقائياً من اشتراكك
HOST = "http://12k-service.org"
USERNAME = "uiuj63jbc8"
PASSWORD = "0n5iejexqg"

GITHUB_TOKEN = os.environ.get("GH_TOKEN")
REPO = os.environ.get("GITHUB_REPOSITORY")
FILE_PATH = "system_config.dat"

SECRET_KEY = b'MySecretKeyForIPTVChannels4000!!' 
IV = b'16BytesLongIV!!!'

def fetch_live_channels():
    # الاتصال عبر الـ API لجلب القنوات الحية فقط وتجاهل الأفلام والمسلسلات تماماً لتفادي الـ Timeout
    api_url = f"{HOST}/player_api.php?username={USERNAME}&password={PASSWORD}&action=get_live_streams"
    print("جاري الاتصال بسيرفر الاكستريم عبر الـ API السريع لإحضار القنوات الحية فقط...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(api_url, headers=headers, timeout=60)
        if response.status_code != 200:
            print(f"فشل الاتصال بالسيرفر: {response.status_code}")
            return None
            
        raw_data = response.json()
        # إذا كان السيرفر يعود بمصفوفة قنوات
        if isinstance(raw_data, list):
            channels = []
            print(f"نجاح! تم جلب القنوات الحية الحقيقية فقط.")
            
            for ch in raw_data:
                # استخراج البيانات الهامة والأساسية فقط لضمان الخفة التامة وعدم التعليق
                # روابط البث في الاكستريم تبنى بهذا المسار الثابت
                stream_url = f"{HOST}/{USERNAME}/{PASSWORD}/{ch.get('stream_id')}"
                
                channels.append({
                    'name': ch.get('name', 'Unknown'),
                    'logo': ch.get('stream_icon', ''),
                    'category': str(ch.get('category_id', 'General')),
                    'url': stream_url
                })
            return channels
        else:
            print("استجابة غير متوقعة من السيرفر.")
            return None
            
    except Exception as e:
        print(f"حدث خطأ أثناء جلب البيانات عبر الـ API: {e}")
        return None

def encrypt_and_compress_data(data):
    json_bytes = json.dumps(data).encode('utf-8')
    compressed_bytes = gzip.compress(json_bytes)
    cipher = AES.new(SECRET_KEY, AES.MODE_CBC, IV)
    encrypted_bytes = cipher.encrypt(pad(compressed_bytes, AES.block_size))
    return base64.b64encode(encrypted_bytes).decode('utf-8')

# تشغيل النظام
channels_list = fetch_live_channels()
if channels_list:
    print(f"🔥 تم استخلاص {len(channels_list)} قناة حية مشفرة ومفتوحة بنجاح عالي وبدون تايم أوت!")
    print("جاري التشفير والضغط الفائق للحماية...")
    
    final_text = encrypt_and_compress_data(channels_list)
    
    url = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"
    gh_headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    
    res = requests.get(url, headers=gh_headers)
    sha = res.json().get('sha') if res.status_code == 200 else None
    
    payload = {
        "message": "Auto Sync Via Xtream API",
        "content": base64.b64encode(final_text.encode('utf-8')).decode('utf-8'),
    }
    if sha: 
        payload["sha"] = sha
        
    print("جاري رفع الملف النهائي إلى جيثب...")
    upload_res = requests.put(url, json=payload, headers=gh_headers)
    if upload_res.status_code in [200, 201]:
        print("✅ نجاح باهر وعالمي! تم إنشاء ملف system_config.dat الصغير والخفيف جداً والمستحيل يعلق!")
    else:
        print(f"فشل الرفع لجيثب. تفاصيل: {upload_res.text}")
else:
    print("❌ فشل النظام في جلب القنوات.")
    
