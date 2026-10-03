/* بيانات المنتج - عدّلها هنا */
/* مسار الصورة يُحسب من موقع هذا الملف ليعمل من أي صفحة (الرئيسية/السلة/الدفع) */
const _assetScript = document.currentScript && document.currentScript.src;
const _img = (p) => _assetScript ? new URL(p, _assetScript).href : p;
const PRODUCT = {id:'saving-pack',name:'باقة التوفير الكبرى',price:5.000,
  desc:'باقة تشمل: بوكس دجاج 10 حبات (كل حبة 900 غرام) + 5 صحون صدور دجاج (كل صحن 500 غرام) + كيس أرز بسمتي فاخر 10 كيلو.',
  image:_img('../images/product.jpg')};
const KEY='areef_cart', fmt=n=>n.toFixed(3);
const store={
  get(){try{return JSON.parse(localStorage.getItem(KEY))||{qty:0}}catch(e){return{qty:0}}},
  set(c){try{localStorage.setItem(KEY,JSON.stringify(c))}catch(e){}}
};
function totals(){const q=store.get().qty;return{qty:q,total:q*PRODUCT.price}}
function renderTotals(){
  const t=totals();
  document.querySelectorAll('[data-total]').forEach(e=>e.textContent=fmt(t.total));
  document.querySelectorAll('[data-count]').forEach(e=>e.textContent=t.qty);
}
/* عدّاد تنازلي: 3 ساعات و21 دقيقة، يستمر حتى لو أُعيد تحميل الصفحة */
function startTimer(el){
  if(!el)return;let end=+localStorage.getItem('areef_end2');
  if(!end||end<Date.now()){end=Date.now()+(3*3600+44*60+3)*1000;try{localStorage.setItem('areef_end2',end)}catch(e){}}
  const p=n=>String(n).padStart(2,'0');
  (function tick(){const s=Math.max(0,Math.floor((end-Date.now())/1000));
    el.textContent=p(Math.floor(s/3600))+':'+p(Math.floor(s%3600/60))+':'+p(s%60);
    if(s>0)setTimeout(tick,1000)})();
}
/* تحميل الصورة إن وُجدت وإلا إظهار بديل */
function loadImg(box,emoji){
  const im=new Image();im.alt=PRODUCT.name;im.onload=()=>{const ph=box.querySelector('.ph');if(ph)ph.remove();box.prepend(im)};
  im.src=PRODUCT.image;
}
