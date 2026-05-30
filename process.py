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

def detect_quality(name):
    """تحديد جودة القناة بناءً على الاسم"""
    name_upper = name.upper()
    if '4K' in name_upper or 'UHD' in name_upper:
        return '4K'
    elif 'FHD' in name_upper or 'FULL HD' in name_upper:
        return 'FHD'
    elif 'HD' in name_upper:
        return 'HD'
    elif 'SD' in name_upper:
        return 'SD'
    else:
        return 'SD'  # الافتراضي

def is_arabic_channel(channel_data):
    """التحقق إذا كانت القناة عربية (بوجود AR أو أحرف عربية)"""
    # البحث عن AR في جميع قيم القناة (كحقل منفصل أو داخل الاسم)
    for key, value in channel_data.items():
        if isinstance(value, str) and 'AR' in value.upper():
            return True
    
    # البحث عن أحرف عربية في الاسم
    name = channel_data.get('name', '')
    arabic_chars = set('ابتثجحخدذرزسشصضطظعغفقكلمنهويءآأؤإة')
    if any(char in name for char in arabic_chars):
        return True
    
    return False

def get_channel_category(channel_data):
    """تحديد فئة القناة بناءً على العربية والجودة"""
    name = channel_data.get('name', '')
    quality = detect_quality(name)
    is_arabic = is_arabic_channel(channel_data)
    
    if is_arabic:
        if quality in ['4K', 'FHD', 'HD']:
            return 'قنوات عربية - HD'
        else:
            return 'قنوات عربية - SD'
    else:
        if quality in ['4K', 'FHD', 'HD']:
            return 'قنوات عالمية - HD'
        else:
            return 'قنوات عالمية - SD'

def fetch_and_categorize_channels():
    api_url = f"{HOST}/player_api.php?username={USERNAME}&password={PASSWORD}&action=get_live_streams"
    headers = {'User-Agent': 'Mozilla/5.0 (Android 10; Mobile; rv:91.0) Gecko/91.0 Firefox/91.0'}
    
    print("جاري الاتصال بسيرفر الأكستريم...")
    try:
        response = requests.get(api_url, headers=headers, timeout=60)
        if response.status_code != 200:
            print(f"فشل الاتصال: {response.status_code}")
            return None
            
        raw_data = response.json()
        if not isinstance(raw_data, list):
            return None
            
        print(f"تم جلب {len(raw_data)} قناة خام. جاري التصنيف...")
        
        # تجميع القنوات حسب الفئات
        categories = {}
        arabic_count = 0
        world_count = 0
        
        for ch in raw_data:
            channel_data = {
                'name': ch.get('name', 'Unknown'),
                'logo': ch.get('stream_icon', ''),
                'url': f"{HOST}/live/{USERNAME}/{PASSWORD}/{ch.get('stream_id')}.m3u8"
            }
            
            category_name = get_channel_category(channel_data)
            
            if category_name not in categories:
                categories[category_name] = []
            categories[category_name].append(channel_data)
            
            if 'عربية' in category_name:
                arabic_count += 1
            else:
                world_count += 1
        
        # ترتيب الباقات (العربية أولاً)
        final_packages = []
        
        # ترتيب محدد للأولوية
        priority_order = ['قنوات عربية - HD', 'قنوات عربية - SD', 'قنوات عالمية - HD', 'قنوات عالمية - SD']
        
        for cat_name in priority_order:
            if cat_name in categories:
                # ترتيب القنوات داخل الباقة أبجدياً
                categories[cat_name].sort(key=lambda x: x['name'])
                final_packages.append({
                    'id': cat_name.replace(' ', '_').replace('-', ''),
                    'name': cat_name,
                    'channels': categories[cat_name]
                })
                print(f"- {cat_name}: {len(categories[cat_name])} قناة")
                del categories[cat_name]
        
        # إضافة أي باقات أخرى (لن يحدث عادة)
        for cat_name, channels in categories.items():
            channels.sort(key=lambda x: x['name'])
            final_packages.append({
                'id': cat_name.replace(' ', '_').replace('-', ''),
                'name': cat_name,
                'channels': channels
            })
            print(f"- {cat_name}: {len(channels)} قناة (إضافية)")
        
        print(f"\nملخص: {arabic_count} قناة عربية, {world_count} قناة عالمية")
        return final_packages
        
    except Exception as e:
        print(f"خطأ: {e}")
        return None

def encrypt_and_compress_data(packages):
    json_bytes = json.dumps(packages, ensure_ascii=False).encode('utf-8')
    compressed_bytes = gzip.compress(json_bytes)
    cipher = AES.new(SECRET_KEY, AES.MODE_CBC, IV)
    encrypted_bytes = cipher.encrypt(pad(compressed_bytes, AES.block_size))
    return base64.b64encode(encrypted_bytes).decode('utf-8')

# تنفيذ العملية
print("بدء عملية جلب وتصنيف القنوات...")
packages_list = fetch_and_categorize_channels()

if packages_list:
    print(f"\nجاري التشفير والرفع...")
    
    final_text = encrypt_and_compress_data(packages_list)
    
    url = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"
    gh_headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    
    res = requests.get(url, headers=gh_headers)
    sha = res.json().get('sha') if res.status_code == 200 else None
    
    payload = {
        "message": "تصنيف القنوات حسب AR وجودة (HD/SD/4K/FHD) مع الأولوية للعربية",
        "content": base64.b64encode(final_text.encode('utf-8')).decode('utf-8')
    }
    if sha:
        payload["sha"] = sha
        
    upload_res = requests.put(url, json=payload, headers=gh_headers)
    if upload_res.status_code in [200, 201]:
        print("✅ تم تحديث ملف القنوات بنجاح.")
        print("   - قنوات عربية - HD: تظهر أولاً")
        print("   - قنوات عربية - SD: تظهر ثانياً")
        print("   - ثم القنوات العالمية")
    else:
        print(f"❌ فشل الرفع: {upload_res.text}")
else:
    print("❌ تعذر جلب البيانات.")
