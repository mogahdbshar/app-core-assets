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

# قائمة الكلمات المفتاحية للقنوات العربية + الرياضية المهمة
ARABIC_KEYWORDS = [
    # القنوات الرياضية المهمة (أضفتها في البداية عشان الأولوية)
    'ssc', 'ssc1', 'ssc2', 'ssc3', 'ssc4', 'ssc5', 'ssc sport', 'ssc sports', 'الرياضية السعودية',
    'beIN', 'be in', 'bein', 'بي ان', 'بي إن', 'beIN Sports', 'bein sport',
    'الكاس', 'alkass', 'al cass', 'الكأس',
    'admiral', 'أدميرال',
    'koora', 'كورة',
    'رياضة', 'sports',
    
    # القنوات العربية العامة
    'ال', 'العربية', 'مصر', 'السعودية', 'الإمارات', 'الكويت', 'قطر', 'البحرين', 'عمان', 'الاردن', 
    'فلسطين', 'لبنان', 'سوريا', 'العراق', 'المغرب', 'الجزائر', 'تونس', 'ليبيا', 'السودان', 'اليمن',
    'mbc', 'mbc1', 'mbc2', 'mbc3', 'mbc4', 'mbc5', 'mbc action', 'mbc max', 'mbc drama',
    'روتانا', 'art', 'الجزيرة', 'الحدث', 'سكاي نيوز', 'العربية الحدث', 'cnn عربية',
    'فرانس', 'بي بي سي', 'bbc عربية', 'العاصمة', 'الحرة', 'الغد', 'الميادين', 'المنار',
    'دبي', 'أبو ظبي', 'الشارقة', 'عجمان', 'رأس الخيمة', 'الفجيرة', 'بينونة', 
    'النيل', 'الحياة', 'on', 'dmc', 'ten', 'المحور', 'القاهرة', 'النهار',
    'lbc', 'mtv', 'otv', 'nbn', 'تلفزيون لبنان',
    'العراقية', 'الرشيد', 'الموصلية', 'العراق حر',
    'الراي', 'روتانا خليجية', 'روتانا موسيقى', 'روتانا طرب', 'روتانا كلاسيك',
    'سبيس تون', 'كرتون نتورك عربية', 'mbc3', 'بسمة', 'نور', 'طيور الجنة',
    # إضافات مهمة
    'فورملا', ' formula', 'مونديال', 'world cup', 'كأس', 'دوري', 'champions', 'champions league',
    'النصر', 'الهلال', 'الاتحاد', 'الأهلي', 'الشباب', 'الاتفاق', 'الوحدة', 'الفيحاء',
    'الزمالك', 'الأهلي مصر', 'بيراميدز', 'الوداد', 'الرجاء', 'الترجي', 'الصفاقسي'
]

def is_arabic_or_sports_channel(channel_name):
    """تفحص إذا كانت القناة عربية أو رياضية مهمة"""
    if not channel_name:
        return False
    name_lower = channel_name.lower()
    
    # البحث عن الكلمات المفتاحية
    for keyword in ARABIC_KEYWORDS:
        if keyword.lower() in name_lower:
            return True
    
    # التحقق من وجود حروف عربية
    for char in channel_name:
        if '\u0600' <= char <= '\u06FF':
            return True
    
    # التحقق من أرقام SSC أو beIN (مثل SSC1, SSC2, beIN1, beIN2...)
    if 'ssc' in name_lower or 'bein' in name_lower:
        return True
    
    return False

def fetch_live_channels():
    api_url = f"{HOST}/player_api.php?username={USERNAME}&password={PASSWORD}&action=get_live_streams"
    headers = {'User-Agent': 'Mozilla/5.0 (Android 10; Mobile; rv:91.0) Gecko/91.0 Firefox/91.0'}
    
    print("جاري الاتصال بسيرفر الأكستريم...")
    print("🎯 البحث عن: SSC, beIN Sports, Alkass, والقنوات العربية...")
    
    try:
        response = requests.get(api_url, headers=headers, timeout=60)
        if response.status_code != 200:
            print(f"فشل الاتصال: {response.status_code}")
            return None
            
        raw_data = response.json()
        if isinstance(raw_data, list):
            channels = []
            arabic_count = 0
            total_count = 0
            sports_count = 0
            
            for ch in raw_data:
                total_count += 1
                channel_name = ch.get('name', '')
                
                if is_arabic_or_sports_channel(channel_name):
                    stream_url = f"{HOST}/live/{USERNAME}/{PASSWORD}/{ch.get('stream_id')}.m3u8"
                    
                    # تحديد فئة القناة
                    category = 'قنوات رياضية'
                    name_lower = channel_name.lower()
                    if 'ssc' in name_lower:
                        category = 'SSC - الرياضية السعودية'
                    elif 'bein' in name_lower:
                        category = 'beIN Sports'
                    elif 'الكاس' in channel_name or 'alkass' in name_lower:
                        category = 'قنوات الكاس'
                    elif any(x in name_lower for x in ['sport', 'رياضة', 'koora', 'كورة']):
                        category = 'رياضة عامة'
                    elif any(x in name_lower for x in ['news', 'اخبار', 'الجزيرة', 'العربية', 'سكاي']):
                        category = 'قنوات إخبارية'
                    else:
                        category = 'قنوات عربية'
                    
                    channels.append({
                        'name': channel_name,
                        'logo': ch.get('stream_icon', ''),
                        'category': category,
                        'url': stream_url
                    })
                    arabic_count += 1
                    
                    # إحصاء القنوات الرياضية تحديداً
                    if 'رياض' in category or 'SSC' in category or 'beIN' in category or 'الكاس' in category:
                        sports_count += 1
                    
                    # طباعة تقدم للقنوات الرياضية المهمة
                    if 'ssc' in name_lower or 'bein' in name_lower or 'الكاس' in name_lower:
                        print(f"⭐ تم العثور على قناة رياضية مهمة: {channel_name}")
            
            print(f"\n📊 إحصائيات:")
            print(f"   - إجمالي القنوات في السيرفر: {total_count}")
            print(f"   - قنوات عربية تم فلترتها: {arabic_count}")
            print(f"   - منها قنوات رياضية: {sports_count}")
            return channels
        return None
    except Exception as e:
        print(f"خطأ: {e}")
        return None

def encrypt_and_compress_data(data):
    json_bytes = json.dumps(data, ensure_ascii=False).encode('utf-8')
    compressed_bytes = gzip.compress(json_bytes)
    cipher = AES.new(SECRET_KEY, AES.MODE_CBC, IV)
    encrypted_bytes = cipher.encrypt(pad(compressed_bytes, AES.block_size))
    return base64.b64encode(encrypted_bytes).decode('utf-8')

# تنفيذ العملية
print("🚀 بدء تشغيل سكريبت جلب القنوات العربية والرياضية...")
print("=" * 50)

channels_list = fetch_live_channels()
if channels_list:
    print(f"\n✅ تم جلب {len(channels_list)} قناة عربية ورياضية.")
    print("🔄 جاري التشفير والضغط...")
    
    final_text = encrypt_and_compress_data(channels_list)
    
    # إعدادات الرفع إلى GitHub
    url = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"
    gh_headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    
    res = requests.get(url, headers=gh_headers)
    sha = res.json().get('sha') if res.status_code == 200 else None
    
    payload = {
        "message": "Update: SSC, beIN Sports, Alkass & Arabic Channels",
        "content": base64.b64encode(final_text.encode('utf-8')).decode('utf-8')
    }
    if sha: payload["sha"] = sha
        
    print("📤 جاري الرفع إلى GitHub...")
    upload_res = requests.put(url, json=payload, headers=gh_headers)
    if upload_res.status_code in [200, 201]:
        print("✅ تم تحديث ملف القنوات بنجاح!")
        print("🎯 القنوات المضمنة: SSC, beIN Sports, Alkass, وجميع القنوات العربية")
    else:
        print(f"❌ فشل الرفع: {upload_res.text}")
else:
    print("❌ تعذر جلب البيانات أو لا توجد قنوات عربية.")
