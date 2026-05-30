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

# قائمة الأولويات للقنوات العربية (من الأعلى إلى الأسفل)
def get_channel_category(name):
    name_lower = name.lower()
    
    # 1. بي إن سبورت (beIN)
    if 'bein' in name_lower or 'be in' in name_lower:
        if 'hd' in name_lower or '1080' in name_lower or '720' in name_lower:
            return 'بي إن سبورت - HD'
        else:
            return 'بي إن سبورت - SD'
    
    # 2. SSC
    if 'ssc' in name_lower:
        if 'hd' in name_lower or '1080' in name_lower or '720' in name_lower:
            return 'SSC - HD'
        else:
            return 'SSC - SD'
    
    # 3. MBC
    if 'mbc' in name_lower:
        if 'hd' in name_lower or '1080' in name_lower or '720' in name_lower:
            return 'MBC - HD'
        else:
            return 'MBC - SD'
    
    # 4. شاهد (Shahid)
    if 'shahid' in name_lower:
        if 'hd' in name_lower or '1080' in name_lower or '720' in name_lower:
            return 'شاهد - HD'
        else:
            return 'شاهد - SD'
    
    # 5. نتفلكس (Netflix)
    if 'netflix' in name_lower:
        if 'hd' in name_lower or '1080' in name_lower or '720' in name_lower:
            return 'نتفلكس - HD'
        else:
            return 'نتفلكس - SD'
    
    # 6. قنوات عربية مهمة (روتانا، ART، قنوات دراما، إلخ)
    important_keywords = ['rotana', 'art', 'دراما', 'drama', 'مسلسلات', 'افلام', 'cinema', 
                          'mbc masr', 'mbc egypt', 'mbc iraq', 'mbc plus', 'mbc action',
                          'mbc max', 'mbc drama', 'mbc 1', 'mbc 2', 'mbc 3', 'mbc 4',
                          'al jazeera', 'al arabiya', 'sky news arabia', 'cnbc arabia',
                          'التلفزيون العربي', 'سورية', 'العراقية', 'المصرية', 'السعودية',
                          'الجزيرة', 'العربية', 'العلم', 'الإخبارية']
    
    for keyword in important_keywords:
        if keyword in name_lower:
            if 'hd' in name_lower or '1080' in name_lower or '720' in name_lower:
                return 'قنوات عربية مهمة - HD'
            else:
                return 'قنوات عربية مهمة - SD'
    
    # 7. باقي القنوات العربية
    # نفحص إذا كان الاسم يحتوي على أحرف عربية
    arabic_chars = set('ابتثجحخدذرزسشصضطظعغفقكلمنهويءآأؤإة')
    has_arabic = any(char in name for char in arabic_chars)
    
    if has_arabic:
        if 'hd' in name_lower or '1080' in name_lower or '720' in name_lower:
            return 'قنوات عربية متنوعة - HD'
        else:
            return 'قنوات عربية متنوعة - SD'
    
    # 8. القنوات الأجنبية
    if 'hd' in name_lower or '1080' in name_lower or '720' in name_lower:
        return 'قنوات أجنبية - HD'
    else:
        return 'قنوات أجنبية - SD'

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
        
        for ch in raw_data:
            name = ch.get('name', 'Unknown')
            category_name = get_channel_category(name)
            
            channel_data = {
                'name': name,
                'logo': ch.get('stream_icon', ''),
                'url': f"{HOST}/live/{USERNAME}/{PASSWORD}/{ch.get('stream_id')}.m3u8"
            }
            
            if category_name not in categories:
                categories[category_name] = []
            categories[category_name].append(channel_data)
        
        # بناء قائمة الباقات النهائية (مرتبة حسب الأهمية)
        final_packages = []
        
        # ترتيب الباقات المطلوب ظهورها في التطبيق
        order = [
            'بي إن سبورت - HD',
            'بي إن سبورت - SD',
            'SSC - HD',
            'SSC - SD',
            'MBC - HD',
            'MBC - SD',
            'شاهد - HD',
            'شاهد - SD',
            'نتفلكس - HD',
            'نتفلكس - SD',
            'قنوات عربية مهمة - HD',
            'قنوات عربية مهمة - SD',
            'قنوات عربية متنوعة - HD',
            'قنوات عربية متنوعة - SD',
            'قنوات أجنبية - HD',
            'قنوات أجنبية - SD'
        ]
        
        for cat_name in order:
            if cat_name in categories:
                final_packages.append({
                    'id': cat_name.replace(' ', '_').replace('-', '').replace('__', '_'),
                    'name': cat_name,
                    'channels': categories[cat_name]
                })
                print(f"- {cat_name}: {len(categories[cat_name])} قناة")
        
        # إضافة أي باقات أخرى لم يتم ترتيبها
        for cat_name, channels in categories.items():
            if cat_name not in order:
                final_packages.append({
                    'id': cat_name.replace(' ', '_').replace('-', '').replace('__', '_'),
                    'name': cat_name,
                    'channels': channels
                })
                print(f"- {cat_name}: {len(channels)} قناة (إضافية)")
        
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
        "message": "تصنيف القنوات: beIN, SSC, MBC, Shahid, Netflix, مهمة, متنوعة - مع فصل HD/SD",
        "content": base64.b64encode(final_text.encode('utf-8')).decode('utf-8')
    }
    if sha:
        payload["sha"] = sha
        
    upload_res = requests.put(url, json=payload, headers=gh_headers)
    if upload_res.status_code in [200, 201]:
        print("✅ تم تحديث ملف القنوات بنجاح.")
    else:
        print(f"❌ فشل الرفع: {upload_res.text}")
else:
    print("❌ تعذر جلب البيانات.")
