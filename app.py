import streamlit as st
import pdfplumber
import re
import urllib.parse

# --- 1. תיקון עברית ועיצוב RTL ---
st.markdown("""
    <style>
    .main, .stMarkdown, div[data-testid="stExpander"] {
        direction: rtl;
        text-align: right;
    }
    div[data-testid="stSidebar"] { direction: rtl; }
    </style>
    """, unsafe_allow_html=True)

SHOP_INFO = "פודלס - נחום שריג 33, שכונת רמות, באר שבע | 08-6655443"

# --- 2. דאטה-בייס מורחב וטווחים מדויקים ---
blood_db = {
    "GLU": {"name": "גלוקוז", "min": 74, "max": 143, "unit": "mg/dL", "desc": "בודק רמת סוכר בדם.", "cause": "סוכרת או סטרס."},
    "CREA": {"name": "קריאטינין", "min": 0.5, "max": 1.8, "unit": "mg/dL", "desc": "מדד תפקוד כליות.", "cause": "עומס כלייתי."},
    "BUN": {"name": "אוריאה", "min": 7, "max": 27, "unit": "mg/dL", "desc": "פינוי פסולת חלבון.", "cause": "תפקוד כליות ירוד."},
    "TP": {"name": "חלבון כללי", "min": 5.2, "max": 8.2, "unit": "g/dL", "desc": "סך החלבונים בדם.", "cause": "דלקת כרונית."},
    "ALB": {"name": "אלבומין", "min": 2.3, "max": 4.0, "unit": "g/dL", "desc": "חלבון המיוצר בכבד.", "cause": "בעיות כבד."},
    "ALT": {"name": "אנזימי כבד (ALT)", "min": 10, "max": 125, "unit": "U/L", "desc": "נזק לתאי כבד.", "cause": "דלקת כבד."},
    "ALKP": {"name": "פוספטאזה בסיסית", "min": 23, "max": 212, "unit": "U/L", "desc": "דרכי מרה ועצמות.", "cause": "בעיות כבד."}
}

hebrew_mapping = {"GLU": "GLU", "CREA": "CREA", "BUN": "BUN", "TP": "TP", "ALB": "ALB", "GLOB": "GLOB", "ALT": "ALT", "ALKP": "ALKP"}

# --- 3. מנוע סריקה משופר V41 ---
def extract_v41(pdf_file):
    extracted = {"data": {}, "meta": {}}
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            lines = text.split('\n')
            for line in lines:
                # זיהוי מטא-דאטה
                if "Patient Name:" in line: extracted["meta"]["name"] = line.split("Name:")[1].split()[0]
                if "Weight:" in line: 
                    w = re.search(r"Weight:\s*(\d+\.?\d*)", line)
                    if w: extracted["meta"]["weight"] = w.group(1)
                
                # זיהוי מדדים - חיפוש המספר הראשון אחרי שם המדד
                for key_word, eng_key in hebrew_mapping.items():
                    if key_word in line.upper():
                        nums = re.findall(r"(\d+\.?\d*)", line)
                        if nums: extracted["data"][eng_key] = float(nums[0])
    return extracted

# --- 4. ממשק המשתמש ---
st.title(f"🩺 המומחה המדויק של פודלס")
uploaded_file = st.file_uploader("העלה בדיקת PDF", type=["pdf"])

if uploaded_file:
    res = extract_v41(uploaded_file)
    data = res["data"]
    # ... (המשך קוד הממשק והצלבות המומחה מגרסה V40)
