import streamlit as st
import google.generativeai as genai
from googlesearch import search
import json
import re

# --- 1. إعدادات الصفحة والهوية البصرية ---
st.set_page_config(page_title="رادار الابتكار الشامل", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;900&display=swap');
    
    .stApp, .block-container, header, [data-testid="stMarkdownContainer"] * {
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Tajawal', sans-serif !important;
    }
    
    .main-header {
        background: linear-gradient(45deg, #0d47a1, #10b981);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3em;
        font-weight: 900;
        text-align: center;
        margin-bottom: 5px;
    }
    
    .sub-header {
        color: #5f6368;
        text-align: center;
        font-weight: 400;
        margin-bottom: 30px;
    }

    [data-testid="stCodeBlock"] {
        direction: ltr !important; 
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. إعدادات API والذاكرة المؤقتة ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
except Exception as e:
    st.error("خطأ في مفتاح الـ API. تأكد من إعداده في الـ Secrets.")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "gate_passed" not in st.session_state:
    st.session_state.gate_passed = False
if "full_report" not in st.session_state:
    st.session_state.full_report = None
if "final_idea" not in st.session_state:
    st.session_state.final_idea = ""

# --- 3. دوال الذكاء الاصطناعي ---

def gatekeeper_check(user_input):
    sys_prompt = f"""
    أنت مُحقق تقني صارم. مهمتك قراءة الفكرة والتأكد من وجود 4 معايير:
    1. الاحتياج الجوهري (المشكلة).
    2. الآلية التقنية الدقيقة (كيف يعمل).
    3. نقطة التفرد.
    4. حالة النضج.
    
    النص: "{user_input}"
    إما أن تقبل (accept) أو تطلب سؤالاً جراحياً (reject).
    يجب أن يكون ردك بصيغة JSON فقط كالتالي:
    {{"status": "accept", "message": "اكتملت"}} أو {{"status": "reject", "message": "سؤالك هنا"}}
    """
    try:
        response = model.generate_content(sys_prompt).text
        match = re.search(r'\{.*\}', response, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        return {"status": "accept", "message": "تم التمرير"}
    except:
        return {"status": "accept", "message": "تم التمرير تلقائياً"}

def generate_strategic_report(idea):
    # استخراج كلمات بحث
    kw_prompt = f"Extract 3 English keywords for searching patents about: {idea}"
    keywords = model.generate_content(kw_prompt).text.strip()
    
    flat_links = []
    try:
        # البحث باستخدام المكتبة الصحيحة
        for url in search(f"{keywords} patent 2026", num_results=3):
            flat_links.append(url)
    except: pass
    
    links_context = "\n".join(flat_links) if flat_links else "لا توجد روابط مباشرة حالياً."

    report_prompt = f"""
    أنت خبير فحص نافي للجهالة. صغ تقريراً احترافياً للفكرة: "{idea}"
    استخدم الفواصل: [===LEVEL1===] ، [===LEVEL2===] ، [===LEVEL3===]
    
    [===LEVEL1===] (التشخيص والمنافسين: {links_context})
    [===LEVEL2===] (الفحص التقني والمطالبة القانونية بالعربي والإنجليزي)
    [===LEVEL3===] (الجدوى الاستثمارية والتموضع الاستراتيجي)
    """
    return model.generate_content(report_prompt).text

# --- 4. الواجهة ---
st.markdown("<h1 class='main-header'>🛡️ رادار الابتكار الشامل</h1>", unsafe_allow_html=True)
st.markdown("<h3 class='sub-header'>منصة الفحص الاستراتيجي والتقييم النافي للجهالة</h3>", unsafe_allow_html=True)

if not st.session_state.gate_passed:
    if prompt := st.chat_input("صف ابتكارك بدقة هنا..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        full_context = " ".join([m["content"] for m in st.session_state.messages if m["role"] == "user"])
        
        with st.spinner("جاري الفحص..."):
            gate_result = gatekeeper_check(full_context)
            if gate_result.get("status") == "reject":
                st.session_state.messages.append({"role": "assistant", "content": gate_result.get("message")})
                st.rerun()
            else:
                st.session_state.gate_passed = True
                st.session_state.final_idea = full_context
                st.rerun()

    # عرض الرسائل
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

if st.session_state.gate_passed:
    if st.session_state.full_report is None:
        with st.spinner("جاري توليد التقرير الاستراتيجي..."):
            st.session_state.full_report = generate_strategic_report(st.session_state.final_idea)
            st.rerun()

    report = st.session_state.full_report
    st.markdown("### 📋 نتائج الفحص الاستراتيجي")
    st.write(report)
    
    if st.button("فحص ابتكار جديد 🔄"):
        for key in st.session_state.keys(): del st.session_state[key]
        st.rerun()
