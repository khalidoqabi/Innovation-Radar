import streamlit as st
import requests
import json
import re

# --- 1. إعدادات الهوية البصرية واللغة ---
st.set_page_config(page_title="رادار الابتكار الشامل", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;900&display=swap');
    
    html, body, [data-testid="stSidebar"], .stApp {
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Tajawal', sans-serif !important;
    }
    
    .main-header {
        background: linear-gradient(45deg, #0d47a1, #10b981);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5em;
        font-weight: 900;
        text-align: center;
    }
    
    .report-box {
        background-color: #f8fafc;
        border-right: 5px solid #10b981;
        padding: 20px;
        border-radius: 10px;
        line-height: 1.8;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. إدارة الحالة (Session State) لمنع تكرار الاتصال ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "gate_passed" not in st.session_state:
    st.session_state.gate_passed = False
if "full_report" not in st.session_state:
    st.session_state.full_report = None
if "final_idea" not in st.session_state:
    st.session_state.final_idea = ""

# --- 3. محرك الاتصال المباشر بـ Gemini ---
def call_gemini_direct(prompt):
    """مناداة API جوجل مباشرة لمحاكاة أمر curl وضمان العمل في منطقتك"""
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent"
        
        headers = {'Content-Type': 'application/json'}
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }
        
        response = requests.post(f"{url}?key={api_key}", json=payload, headers=headers)
        
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"خطأ في الاتصال: {response.status_code}"
    except Exception as e:
        return f"حدث خطأ تقني: {str(e)}"

# --- 4. منطق المحقق والتقرير ---
def gatekeeper_logic(user_input):
    sys_prompt = f"""
    أنت مُحقق براءات اختراع. حلل النص التالي: "{user_input}"
    تأكد من وجود فكرة واضحة وآلية عمل.
    رد بصيغة JSON فقط: {{"status": "accept"}} أو {{"status": "reject", "message": "سؤالك هنا"}}
    """
    res_text = call_gemini_direct(sys_prompt)
    try:
        match = re.search(r'\{.*\}', res_text, re.DOTALL)
        return json.loads(match.group(0))
    except:
        return {"status": "accept"}

def generate_strategic_report(idea):
    report_prompt = f"""
    صغ تقريراً استراتيجياً نافياً للجهالة للفكرة: "{idea}"
    قسم التقرير بوضوح باستخدام العناوين:
    [===LEVEL1===] التشخيص الاستراتيجي والمنافسين
    [===LEVEL2===] الفحص التقني والمطالبات القانونية
    [===LEVEL3===] الجدوى الاقتصادية وخارطة الطريق
    """
    return call_gemini_direct(report_prompt)

# --- 5. واجهة المستخدم ---
st.markdown("<h1 class='main-header'>🛡️ رادار الابتكار الشامل</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;'>المختبر الذكي لتقييم وهندسة الابتكارات</p>", unsafe_allow_html=True)

# المرحلة الأولى: التحقيق
if not st.session_state.gate_passed:
    st.info("أهلاً بك. يرجى البدء بوصف ابتكارك ليقوم المحقق الذكي بتقييمه.")
    
    # عرض سجل الحوار
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    if prompt := st.chat_input("اكتب تفاصيل ابتكارك هنا..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # دمج كل ما قاله المستخدم لفهم السياق كاملاً
        full_context = " ".join([m["content"] for m in st.session_state.messages if m["role"] == "user"])
        
        with st.spinner("جاري فحص البيانات..."):
            result = gatekeeper_logic(full_context)
            
            if result.get("status") == "accept":
                st.session_state.gate_passed = True
                st.session_state.final_idea = full_context
                st.rerun()
            else:
                st.session_state.messages.append({"role": "assistant", "content": result.get("message")})
                st.rerun()

# المرحلة الثانية: التقرير
else:
    if st.session_state.full_report is None:
        with st.spinner("جاري توليد التقرير الاستراتيجي..."):
            st.session_state.full_report = generate_strategic_report(st.session_state.final_idea)
    
    st.success("تم الانتهاء من الفحص النافي للجهالة.")
    
    # --- البديل المستقر لزر النسخ ---
    st.markdown("### 📋 التقرير الكامل (للمعاينة والنسخ)")
    st.text_area("انسخ التقرير من هنا:", value=st.session_state.full_report, height=200)
    st.info("💡 يمكنك الضغط على أيقونة النسخ في الزاوية العلوية اليمنى لصندوق النص أعلاه.")

    # --- تنسيق الـ RTL المحدث ---
    st.markdown("""
        <style>
        /* فرض التنسيق من اليمين لليسار للنصوص والنقاط */
        [data-testid="stMarkdownContainer"] p, 
        [data-testid="stMarkdownContainer"] li,
        [data-testid="stMarkdownContainer"] div {
            direction: rtl !important;
            text-align: right !important;
        }
        /* تنسيق صندوق النص ليكون RTL أيضاً */
        textarea {
            direction: rtl !important;
            text-align: right !important;
        }
        </style>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["التشخيص الاستراتيجي", "المطالبات التقنية", "خارطة الطريق"])
    
    # باقي الكود الخاص بـ report_parts و Tabs كما هو دون تغيير
    report_parts = re.split(r'\[===LEVEL[1-3]===\]', st.session_state.full_report)
    
    with tab1:
        st.markdown("<div class='report-box'>", unsafe_allow_html=True)
        st.write(report_parts[1] if len(report_parts) > 1 else st.session_state.full_report)
        st.markdown("</div>", unsafe_allow_html=True)

    with tab2:
        st.write(report_parts[2] if len(report_parts) > 2 else "لا توجد تفاصيل تقنية إضافية.")

    with tab3:
        st.write(report_parts[3] if len(report_parts) > 3 else "خارطة الطريق قيد المراجعة.")

    if st.button("فحص ابتكار جديد 🔄"):
        for key in st.session_state.keys():
            del st.session_state[key]
        st.rerun()
