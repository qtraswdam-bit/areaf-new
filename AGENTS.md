# AGENTS.md

متجر «مزرعتي» — موقع عربي RTL لتوصيل منتجات طازجة في قطر.

## البنية

- **الكتالوج** في Firestore (مشروع `kuwait-me`، مجموعة `products`) — المصدر الموثّق الوحيد.
  حقول الوثيقة: `name`, `desc`, `price` (نص بثلاث خانات عشرية مثل `"26.500"`), `img`, `order` (رقم).
- **الصفحات**: `index.html` (المتجر) و`creatprogect.html` (لوحة الإدارة) تحملان نسخة مدمجة
  `defaultProducts` للعرض الفوري، ثم تُزامَنان من Firestore. لا تحرّر هذه الكتلة يدوياً —
  شغّل `python3 tools/sync_default_products.py`.
- **الصور**: محلية في `assets/images/products/*.webp`، والمسارات في `img` تبدأ بـ `/`.
- **السلة** (`assets/js/cart.js`): تعرّف المنتج **بالاسم فقط** (`p.name === name`).
  لذلك يجب أن تكون أسماء المنتجات فريدة، وإلا اندمج منتجان في سطر واحد بأسعار مختلطة.
- **صفحة المنتج**: `/product/<id>/<slug>` تُخدم كلها بصفحة واحدة `product/index.html`
  (ديناميكية — تقرأ المعرّف من المسار وتجلب من Firestore). لا تنشئ صفحات ثابتة لكل منتج،
  فهي تصبح قديمة بعد أي تعديل. أعد البناء بـ `python3 tools/build_product_page.py`.

## الأوامر

```bash
python3 tools/sync_default_products.py    # مزامنة defaultProducts في index.html و creatprogect.html
python3 tools/build_product_page.py       # إعادة بناء product/index.html
python3 tools/preview_server.py 12000     # معاينة تحاكي توجيهات Netlify (لأن http.server يرجّع 404)
```

## أدوات Firestore (`tools/`)

`add_products_to_firestore.py` يوفر `BASE`, `panel_credentials`, `sign_in`, `get/patch/post`,
`firestore_get`, `update_doc` (يحوّل `int` → `integerValue` و `str` → `stringValue`).
استخدم `update_doc(doc_id, {...}, token)` لتعديل حقول محددة دون مسح الباقي.

سكربتات الإدخال الجماعي (`arabize_chicken.py`, `dedupe_product_names.py`) تعتمد على
`firestore-import-result.json` لربط صفوف المصدر بمعرّفات الوثائق.

## التوجيه (Netlify)

`netlify.toml`: `/product/*` → `/product/index.html`، ثم كل ما تبقى → `/index.html`.
Netlify يخدم الملفات الحقيقية قبل تطبيق الـ redirects.

## تحذير أمني مفتوح

`assets/js/firebase-client.js` يحتوي على `PANEL_EMAIL` و`PANEL_PASSWORD` مكتوبين صريح
(حساب الإدارة). أي زائر يستطيع قراءتهما من المتصفح ويملك صلاحية الكتابة على `products`.
يجب نقل الكتابة إلى خادم/Cloud Function مع قواعد أمان تمنع الكتابة المجهولة.
