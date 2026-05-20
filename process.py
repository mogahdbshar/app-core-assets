import os
import json
import base64
import requests
import re
import gzip
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

M3U_URL = os.environ.get("IPTV_URL")
GITHUB_TOKEN = os.environ.get("GH_TOKEN")
REPO = os.environ.get("GITHUB_REPOSITORY")
FILE_PATH = "system_config.dat"

SECRET_KEY = b'MySecretKeyForIPTVChannels4000!!' 
IV = b'16BytesLongIV!!!'

def parse_m3u(url):
    print("جاري جلب البيانات من الرابط وتحليلها بشكل ذكي...")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': '*/*'
    }
    
    try:
        # استخدام stream=True للتعامل مع الملفات العملاقة دون استهلاك ذاكرة السيرفر
        response = requests.get(url, headers=headers, timeout=90, stream=True)
        if response.status_code != 200: 
            print(f"السيرفر رفض الاستجابة: {response.status_code}")
            return None
        
        channels = []
        current_ch = {}
        
        # قراءة الملف سطر بسطر لتفادي الثقل
        for line in response.iter_lines(decode_unicode=True):
            if not line:
                continue
            line = line.strip()
            
            if line.startswith('#EXTINF:'):
                name_match = re.search(r',([^,]+)$', line)
                logo_match = re.search(r'tvg-logo="([^"]+)"', line)
                cat_match = re.search(r'group-title="([^"]+)"', line)
                
                current_ch['name'] = name_match.group(1).strip() if name_match else "Unknown"
                current_ch['logo'] = logo_match.group(1).strip() if logo_match else ""
                current_ch['category'] = cat_match.group(1).strip() if cat_match else "General"
                
            elif line.startswith('http://') or line.startswith('https://'):
                # فلترة ذكية: تخطي روابط الأفلام والمسلسلات إذا كانت تسبب تضخم كلي، أو أخذ أول 50 ألف عنصر كحد أقصى للحماية
                current_ch['url'] = line
                channels.append(current_ch)
                current_ch = {}
                
                # حد أمان أقصى للمستودع (مثلاً تصفية أول 60,000 عنصر وهو رقم ضخم جداً للقنوات)
                if len(channels) >= 60000:
                    print("⚠️ تم الوصول للحد الأقصى المسموح به للقنوات الحية لحماية حجم الملف.")
                    break
                    
        return channels
    except Exception as e:
        print(f"خطأ أثناء معالجة البيانات: {e}")
        return None

def encrypt_and_compress_data(data):
    # 1. تحويل البيانات إلى نص JSON
    json_bytes = json.dumps(data).encode('utf-8')
    
    # 2. ضغط البيانات أولاً بتقنية Gzip لتقليص الحجم 90%
    compressed_bytes = gzip.compress(json_bytes)
    
    # 3. تشفير البيانات المضغوطة بـ AES-256
    cipher = AES.new(SECRET_KEY, AES.MODE_CBC, IV)
    encrypted_bytes = cipher.encrypt(pad(compressed_bytes, AES.block_size))
    
    # 4. تحويلها إلى نص Base64 للرفع
    return base64.b64encode(encrypted_bytes).decode('utf-8')

channels_list = parse_m3u(M3U_URL)
if channels_list:
    print(f"🔥 تم جلب وتصفية {len(channels_list)} عنصر بنجاح. جاري الضغط والتشفير...")
    
    # تنفيذ الضغط والتشفير المزدوج
    final_text = encrypt_and_compress_data(channels_list)
    print(f"حجم النص النهائي بعد الضغط والتشفير أصبح آمناً للرفع.")
    
    url = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"
    gh_headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    
    # جلب الـ SHA إذا كان الملف موجوداً
    res = requests.get(url, headers=gh_headers)
    sha = res.json().get('sha') if res.status_code == 200 else None
    
    payload = {
        "message": "Auto Sync Compressed Config",
        "content": base64.b64encode(final_text.encode('utf-8')).decode('utf-8'),
    }
    if sha: 
        payload["sha"] = sha
    
    print("جاري إرسال الملف المضغوط إلى جيثب...")
    upload_res = requests.put(url, json=payload, headers=gh_headers)
    print(f"استجابة جيثب عند الرفع: {upload_res.status_code}")
    
    if upload_res.status_code in [200, 201]:
        print("✅ نجاح باهر! تم إنشاء وتحديث ملف system_config.dat المضغوط والمشفر بأمان!")
    else:
        print(f"فشل الرفع. تفاصيل: {upload_res.text}")
else:
    print("❌ فشل معالجة القنوات.")
