# ستايل عادل مفتاح (Mokawala.ma): Reel عمودي 9:16

المرجع ديال الستايل. الكود فـ `src/` و `scripts/` كيطبقو هاد القواعد. ما يتبدل غير المحتوى ديال كل فيديو.

## الإخراج
1080×1920 · 30fps · H.264 CRF 16 · AAC 320k · −14 LUFS · True Peak ≤ −1 dBFS
الملف: `out/<id>-Reel-9x16.mp4`

## 1) النص والترجمة (`scripts/transcribe.py`)
- faster-whisper large-v3-turbo، `language=ar`، `word_timestamps=True`، initial_prompt على المقاولة والتمويل بالدارجة.
- تصحيح الدارجة يدوياً. الأمثلة كاينين فـ `darija/corrections.json`: كثير←كنتي، تفعل←تدير، كيف←شنو/كيفاش، الدم←الدعم، اماغ←MRE، في الخاص←فالخاص، تستفيد←تستافد.
- الكلمات اللي ما متأكدينش منها كتتقال للمستعمل. ممنوع نخترعو محتوى.
- ترجمة إنجليزية طبيعية وقصيرة، بحروف UPPERCASE، والكلمة المفتاحية بين «».

## 2) قطع التنفس (`scripts/prep.py`)
RMS على 20ms، smoothing على 3 frames، threshold −36 dB، والوقفات ≥ 0.15s كتتقطع. padding ديال 0.04s، القطع على الـ frame grid (1/30s)، fade ديال 10ms، والبداية والنهاية الخاويين كيتحيدو.

## 3) Crop عمودي
Crop 9:16 native (1214×2160 من 4K)، متمركز على الوجه (MediaPipe face detector، median)، بلا upscale.

## 4) الصوت الإذاعي
```
highpass=f=65, afftdn=nr=8:nf=-48:tn=1, rubberband=pitch=0.965:formant=shifted:pitchq=quality,
acompressor=threshold=-24dB:ratio=3:attack=12:release=160:makeup=3:knee=6, bass=g=4.5:f=110:w=0.8,
equalizer=f=400:t=q:w=1.2:g=-1.5, equalizer=f=4200:t=q:w=1.2:g=-2, deesser=i=0.45:m=0.5:f=0.5,
treble=g=-4.5:f=7000:w=0.6, alimiter=limit=0.89:attack=4:release=80
```
من بعد loudnorm على جوج pass (I=−14, TP=−1.5, LRA=9, linear). الـ Check: 60–200Hz تقريباً +5dB، و 5–12kHz تقريباً −5dB.

## 5) فصل الشخص (`scripts/segment.py`)
MediaPipe selfie_multiclass_256x256، mask = 1 − background، تحليل على 540×960، guidedFilter (r=8, eps=1e-4)، tighten ×1.6.
الميكروفون: البكسلات الكحلين (max<70) فالمنطقة التحتانية الوسطى كيتحسبو foreground. temporal smoothing من 0.35 (فوق) حتى 0.1 (تحت).
→ `person_alpha.webm` (VP9 · yuva420p · CRF 16).

## 6) المشاهد: تغيير كل ~4s على حدود الجمل
| المشهد | الخلفية |
|---|---|
| original | الخلفية الأصلية ديال الكاميرا |
| orange | gradient #FF8A4C → #F25A24 → #A93309، مربعات زجاجية، keyword ضخمة (Inter 900، أبيض 13%) |
| dark | #0E0D0C، glow برتقالي مورا الراس، grid كيتحرك، مربعات زجاجية فيها أيقونات 💰📄🏦📈🤝 مع blur (DOF) |
| light | #F4EFE6، dotted grid، مسار برتقالي كيترسم مع labels زجاجية |
| image | صورة توضيحية مورا الشخص (Ken Burns + vignette برتقالي + label) |

فالخلفيات المبدلة: الشخص scale 0.9، translateY 110px، drop-shadow 0 30px 50px rgba(0,0,0,.35).
الانتقال: circle reveal فـ7 frames من 50% 42%، scale 1.08→1، flash أبيض 40%، و whoosh كيبدا 0.2s قبل.

## 7) الكاميرا
- Jump cuts: punch-in بالتناوب 1.0 / 1.14 / 1.03 / 1.0 / 1.10، وداخل كل مقطع push +3.5%. الـ base هو 1.08 فالمشهد الأصلي و 0.9 فالمبدل، والـ origin هو 50% 38%.
- Persuasion push: فالجمل ≥5 كلمات و ≥2s (ولا اللي مقسومة على بزاف ديال المقاطع)، التقريب كيوصل حتى ×1.22 (inOut cubic) بلا تناوب، والتبعيد فآخر 0.4s (out cubic). مع swell 0.13 و air 0.16.
- الـ zoom كيدور على خط الفم (transformOrigin 50% 52%)، باش التقريب ما يهبطش الفم للترجمة. الفم ديما فوق y≈1200.
- فالخلفيات المبدلة translateY كيولي 110px (بلاصة 170)، باش الفم يبقى فوق الترجمة.

## 8) الترجمة الكرستالية
- البلاصة من y=1250 حتى ~1480: تحت الفم وفوق الـ UI ديال Instagram (الاسم والوصف). عرض الترجمة ≤ 870px باش ما تجيش تحت الأزرار ديال اليمين.
- 3 كلمات كحد أقصى. الخط Thmanyah Sans Bold (والـ fallback هو Cairo)، والحجم `min(92, 800/(chars×0.5+gaps×0.25))`. ومن بعد كيتقاس العرض الحقيقي بعد ما يتحمل الخط العربي، وإلا فات 800px كيتصغر الحجم باش يبقى داخل (الحروف العراض بحال ف ك ش).
- الكلمات العادية بالأبيض مع bevel #C9D6E8. الكلمة النشيطة ذهبية #FFD447 مع bevel #E0A106 و glow و bump +10%. والكلمات اللي مازال ما تنطقاتش opacity 55%.
- اللوح: rgba(12,12,12,.42)، blur(22px) saturate(170%)، border أبيض 42%، radius 40، sheen، و pop 0.82→1.
- السطر الإنجليزي: Inter 800 34px UPPERCASE، فلوح radius 24، و «keyword» بالأصفر #FFC629.

## 9) التوضيحات (y≈200–420)
chip · chips2 · comment (كتابة حرف بحرف + ❤️) · dm (شعار + «رسالة جديدة 📩» + «🔗 هاهو الرابط») · checklist (✓ كل 0.25s) · tiles · cta (pill برتقالي مع border ذهبي كينبض) · card (صورة ولا emoji + عنوان).
زجاج أبيض rgba(255,255,255,.16)، pop بـ spring 0.6→1، وخروج فـ5 frames. كل توضيح مربوط بالكلمة اللي كتنطق.

## 10) الأصوات
| الحدث | SFX | Volume |
|---|---|---|
| انتقال بين المشاهد | whoosh (0.2s قبل) | 0.32 |
| Jump cut | swipe (0.06s قبل) | 0.16 |
| Chip / Tile | pop | 0.24–0.28 |
| Checklist | check | 0.23 |
| كارت كبير / مسار / صورة | shimmer | 0.20 |
| كتابة التعليق | typing | 0.34 |
| DM | notif | 0.30 |
| CTA | impact | 0.40 |
| Push | swell | 0.13 |
| Pull-back | air | 0.16 |
| موسيقى 95 BPM | music | 0.075 + fade |

## 11) البراند
برتقالي #F25A24 (#FF8A4C، #A93309) · أبيض #FFFFFF · داكن #0E0D0C · كريمي #F4EFE6 · ذهبي #FFD447 / #FFC629 · أخضر #2BD576 (غير للـ ✓).
الشعار: مربع برتقالي فيه حرف «م» أبيض.

## 12) Safe zones (Instagram Reels)
| المنطقة | y (px) |
|---|---|
| UI ديال Instagram الفوقاني | 0–200 (ممنوع الكتابة) |
| التوضيحات | 200–420 |
| الوجه (الفم ≤ 1200) | 420–1200 |
| الترجمة | 1250–1480 |
| الاسم + الوصف + الصوت ديال Instagram | 1500–1920 (ممنوع الكتابة) |
| الأزرار (❤️ 💬 ↗) | x ≥ 960، y 1000–1800 (ممنوع الكتابة) |

فالمشهد الكريمي (light)، اللوحات ديال التوضيحات كيوليو زجاج داكن باش الكتابة تبان.
الـ contact sheet ديال `render.py` كيرسم هاد المناطق بالحمر، وخط الفم بالأصفر.
