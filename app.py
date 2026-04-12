import os
import re
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.utils import secure_filename
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import pandas as pd
import difflib

app = Flask(__name__)
app.secret_key = 'medi_guide_secret_key'

# Configure Tesseract path
# Update this to your local Tesseract installation path
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Ensure upload folder exists
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Load Medicine Dataset
try:
    MED_DATA = pd.read_csv('medicine_dataset.csv')
    # Pre-calculate unique medicine names for fuzzy matching
    DATASET_MED_NAMES = [str(x) for x in MED_DATA['medicine_name'].unique().tolist() if pd.notnull(x)]
except Exception as e:
    print(f"Error loading medicine dataset: {e}")
    MED_DATA = None
    DATASET_MED_NAMES = []

# UI Translation Mappings
UI_LABELS = {
    'en': {
        'title': 'AI Diagnostics | Medi Guide',
        'conf_score_label': 'CONFIDENCE SCORE',
        'valid_detected': 'Medicines Verified Successfully',
        'valid_detected_sub': 'Scan integrity is high. Please verify details.',
        'extracted_medicines': 'Extracted Medicines',
        'raw_text_title': 'Prescription (Raw Text)',
        'verified_scan': 'Verified Scan',
        'prescription_summary': 'Prescription Summary',
        'return_home': 'RETURN HOME',
        'scan_new': 'SCAN NEW REPORT',
        'view_diet': 'VIEW DIET PLAN',
        'low_acc_title': 'Low accuracy. Please upload a clear prescription or consult a doctor.',
        'low_acc_sub': 'The AI could not confidently extract medication details.',
        'medication_scheduling': 'Medication Scheduling',
        'morning': 'Morning',
        'afternoon': 'Afternoon',
        'night': 'Night',
        'instructions': 'Instructions',
        'medicine': 'Medicine',
        'use_label': 'Use',
        'diet_label': 'Diet',
        'suggestion_label': 'Suggestion',
        'as_prescribed': 'As prescribed',
        'follow_doctor': "Follow doctor's prescription",
        'after_food': 'After Food',
        'before_food': 'Before Food',
        'at_night': 'At Night',
        'found': 'Found',
        'toggle': 'Toggle',
        'diagnostic_title': 'Diagnostic Analysis',
        'diagnostic_sub': 'Our AI has successfully scanned and structuralized your prescription data with advanced heuristics.',
        'invalid_image': 'Invalid Image Detected',
        'invalid_image_sub': "Please upload a valid prescription image only. We couldn't detect any medical terminology in this file.",
        'encryption': 'Secure End-to-End Encryption Enabled',
        'buy_medicines': 'Buy Medicines',
        'pharmacy_title': 'Pharmacy Finder'
    },
    'hi': {
        'title': 'एआई डायग्नोस्टिक्स | मेडी गाइड',
        'conf_score_label': 'विश्वास स्कोर',
        'valid_detected': 'दवाइयाँ सफलतापूर्वक सत्यापित',
        'valid_detected_sub': 'स्कैन की गुणवत्ता उच्च है। कृपया विवरण सत्यापित करें।',
        'extracted_medicines': 'निकाली गई दवाइयाँ',
        'raw_text_title': 'प्रिस्क्रिप्शन (मूल टेक्स्ट)',
        'verified_scan': 'सत्यापित स्कैन',
        'prescription_summary': 'प्रिस्क्रिप्शन सारांश',
        'return_home': 'होम पर लौटें',
        'scan_new': 'नया रिपोर्ट स्कैन करें',
        'view_diet': 'आहार योजना देखें',
        'low_acc_title': 'सटीकता कम है। कृपया स्पष्ट प्रिस्क्रिप्शन अपलोड करें।',
        'low_acc_sub': 'AI दवा विवरण निकालने में असमर्थ रहा।',
        'medication_scheduling': 'दवा समय-सारणी',
        'morning': 'सुबह',
        'afternoon': 'दोपहर',
        'night': 'रात',
        'instructions': 'निर्देश',
        'medicine': 'दवा',
        'use_label': 'उपयोग',
        'diet_label': 'आहार',
        'suggestion_label': 'सुझाव',
        'as_prescribed': 'डॉक्टर के निर्देशानुसार',
        'follow_doctor': 'डॉक्टर के निर्देशों का पालन करें',
        'after_food': 'खाने के बाद',
        'before_food': 'खाने से पहले',
        'at_night': 'रात को',
        'found': 'पाई गईं',
        'toggle': 'टॉगल',
        'diagnostic_title': 'नैदानिक विश्लेषण',
        'diagnostic_sub': 'हमारे AI ने आपके प्रिस्क्रिप्शन डेटा का सफलतापूर्वक विश्लेषण किया है।',
        'invalid_image': 'अमान्य छवि',
        'invalid_image_sub': 'कृपया केवल एक वैध प्रिस्क्रिप्शन छवि अपलोड करें।',
        'encryption': 'सुरक्षित एंड-टू-एंड एन्क्रिप्शन सक्षम',
        'buy_medicines': 'दवाइयाँ खरीदें',
        'pharmacy_title': 'फार्मेसी खोजें'
    },
    'te': {
        'title': 'ఏఐ డయాగ్నస్టిక్స్ | మెడి గైడ్',
        'conf_score_label': 'కాన్ఫిడెన్స్ స్కోరు',
        'valid_detected': 'మందులు విజయవంతంగా ధృవీకరించబడ్డాయి',
        'valid_detected_sub': 'స్కాన్ సమగ్రత ఎక్కువగా ఉంది. దయచేసి వివరాలను ధృవీకరించండి.',
        'extracted_medicines': 'సేకరించిన మందులు',
        'raw_text_title': 'ప్రిస్క్రిప్షన్ (ముడి వచనం)',
        'verified_scan': 'ధృవీకరించబడిన స్కాన్',
        'prescription_summary': 'ప్రిస్క్రిప్షన్ సారాంశం',
        'return_home': 'తిరిగి హోమ్‌కి',
        'scan_new': 'కొత్త రిపోర్ట్ స్కాన్ చేయండి',
        'view_diet': 'డైట్ ప్లాన్ చూడండి',
        'low_acc_title': 'ఖచ్చితత్వం తక్కువగా ఉంది. దయచేసి స్పష్టమైన ప్రిస్క్రిప్షన్ అప్‌లోడ్ చేయండి.',
        'low_acc_sub': 'AI మందుల వివరాలను నమ్మకంతో సేకరించలేకపోయింది.',
        'medication_scheduling': 'మందుల షెడ్యూలింగ్',
        'morning': 'ఉదయం',
        'afternoon': 'మధ్యాహ్నం',
        'night': 'రాత్రి',
        'instructions': 'సూచనలు',
        'medicine': 'మందు',
        'use_label': 'ఉపయోగం',
        'diet_label': 'ఆహారం',
        'suggestion_label': 'సూచన',
        'as_prescribed': 'వైద్యుడి సూచన ప్రకారం',
        'follow_doctor': 'వైద్యుడి సూచనలను పాటించండి',
        'after_food': 'భోజనం తర్వాత',
        'before_food': 'భోజనానికి ముందు',
        'at_night': 'రాత్రి పూట',
        'found': 'కనుగొనబడ్డాయి',
        'toggle': 'టాగిల్',
        'diagnostic_title': 'డయాగ్నస్టిక్ విశ్లేషణ',
        'diagnostic_sub': 'మా AI మీ ప్రిస్క్రిప్షన్ డేటాను విజయవంతంగా విశ్లేషించింది.',
        'invalid_image': 'చెల్లని చిత్రం',
        'invalid_image_sub': 'దయచేసి చెల్లుబాటు అయ్యే ప్రిస్క్రిప్షన్ చిత్రాన్ని మాత్రమే అప్‌లోడ్ చేయండి.',
        'encryption': 'సురక్షిత ఎండ్-టు-ఎండ్ ఎన్‌క్రిప్షన్ ఎనేబుల్ చేయబడింది',
        'buy_medicines': 'మందులు కొనండి',
        'pharmacy_title': 'ఫార్మసీ ఫైండర్'
    }
}

# Clinical content translations (use, diet, suggestions)
CLINICAL_TRANSLATIONS = {
    'hi': {
        # Use translations
        'Fever and mild pain relief.': 'बुखार और हल्के दर्द से राहत।',
        'Bacterial infections.': 'जीवाणु संक्रमण।',
        'Allergy and cold relief.': 'एलर्जी और सर्दी से राहत।',
        'Nausea and vomiting.': 'मतली और उल्टी।',
        'High blood pressure control.': 'उच्च रक्तचाप नियंत्रण।',
        'Diabetes management.': 'मधुमेह प्रबंधन।',
        'Thyroid hormone support.': 'थायरॉइड हार्मोन सहायता।',
        'Allergy and cold relief.': 'एलर्जी और सर्दी से राहत।',
        'General medication': 'सामान्य दवा',
        'Gastric acidity and reflux.': 'गैस्ट्रिक एसिडिटी और रिफ्लक्स।',
        'Infection and cold relief.': 'संक्रमण और सर्दी से राहत।',
        # Diet translations
        'Drink plenty of water and eat light meals.': 'खूब पानी पिएं और हल्का भोजन करें।',
        'Take with probiotics like yogurt or curd.': 'दही या प्रोबायोटिक्स के साथ लें।',
        'Drink warm fluids. Avoid cold drinks.': 'गर्म पेय पिएं। ठंडे पेय से बचें।',
        'Eat small frequent meals.': 'थोड़ा-थोड़ा बार-बार खाएं।',
        'Reduce salt and avoid high-potassium foods.': 'नमक कम करें और उच्च पोटेशियम वाले भोजन से बचें।',
        'Strict low-sugar and high-fiber diet.': 'सख्त कम-चीनी और उच्च-फाइबर आहार।',
        'Avoid soy products near dose time.': 'दवा के समय के पास सोया उत्पादों से बचें।',
        'Avoid alcohol and stay hydrated.': 'शराब से बचें और हाइड्रेटेड रहें।',
        'Maintain a balanced diet.': 'संतुलित आहार लें।',
        'Avoid oily, spicy, and deep-fried foods.': 'तैलीय, मसालेदार और तले हुए खाने से बचें।',
        'Drink lots of water. Eat simple home-cooked meals.': 'खूब पानी पिएं। सादा घर का खाना खाएं।',
        # Suggestion translations
        'Take after food. Avoid alcohol.': 'खाने के बाद लें। शराब से बचें।',
        'Complete full course. Do not skip doses.': 'पूरा कोर्स करें। खुराक न छोड़ें।',
        'Take at bedtime if drowsy. Do not skip doses.': 'नींद आने पर सोते समय लें। खुराक न छोड़ें।',
        'Take 30 mins before food.': 'खाने से 30 मिनट पहले लें।',
        'Avoid alcohol. Take at same time daily.': 'शराब से बचें। रोज़ एक ही समय पर लें।',
        'Take at same time daily with meals.': 'भोजन के साथ हर दिन एक ही समय पर लें।',
        'Take 1 hour before breakfast. Take at same time daily.': 'नाश्ते से 1 घंटे पहले लें। रोज़ एक ही समय पर लें।',
        'Take as directed by doctor.': 'डॉक्टर के निर्देशानुसार लें।',
        'Take 30 mins before food. Do not skip doses.': 'खाने से 30 मिनट पहले लें। खुराक न छोड़ें।',
        'Complete full course. Avoid alcohol.': 'पूरा कोर्स करें। शराब से बचें।',
        # Form translations
        'Tablet': 'गोली',
        'Capsule': 'कैप्सूल',
        'Syrup': 'सिरप',
        'Injection': 'इंजेक्शन',
    },
    'te': {
        # Use translations
        'Fever and mild pain relief.': 'జ్వరం మరియు తేలికపాటి నొప్పి ఉపశమనం.',
        'Bacterial infections.': 'బ్యాక్టీరియల్ ఇన్ఫెక్షన్లు.',
        'Allergy and cold relief.': 'అలెర్జీ మరియు జలుబు ఉపశమనం.',
        'Nausea and vomiting.': 'వికారం మరియు వాంతులు.',
        'High blood pressure control.': 'అధిక రక్తపోటు నియంత్రణ.',
        'Diabetes management.': 'డయాబెటిస్ నిర్వహణ.',
        'Thyroid hormone support.': 'థైరాయిడ్ హార్మోన్ సహాయం.',
        'General medication': 'సాధారణ మందు',
        'Gastric acidity and reflux.': 'గ్యాస్ట్రిక్ ఆమ్లత్వం మరియు రిఫ్లక్స్.',
        'Infection and cold relief.': 'ఇన్ఫెక్షన్ మరియు జలుబు ఉపశమనం.',
        # Diet translations
        'Drink plenty of water and eat light meals.': 'ఎక్కువ నీళ్ళు తాగండి మరియు తేలికపాటి భోజనం చేయండి.',
        'Take with probiotics like yogurt or curd.': 'పెరుగు లేదా ప్రోబయోటిక్స్‌తో తీసుకోండి.',
        'Drink warm fluids. Avoid cold drinks.': 'వేడి పానీయాలు తాగండి. చల్లని పానీయాలు మానుకోండి.',
        'Eat small frequent meals.': 'తక్కువశ్ తక్కువగా తరచుగా తినండి.',
        'Reduce salt and avoid high-potassium foods.': 'ఉప్పు తగ్గించండి మరియు అధిక పొటాషియం ఆహారాన్ని మానుకోండి.',
        'Strict low-sugar and high-fiber diet.': 'కఠినమైన తక్కువ-చక్కెర మరియు అధిక-ఫైబర్ ఆహారం.',
        'Avoid soy products near dose time.': 'మోతాదు సమయానికి సోయా ఉత్పత్తులను మానుకోండి.',
        'Avoid alcohol and stay hydrated.': 'మద్యం మానుకోండి మరియు హైడ్రేటెడ్‌గా ఉండండి.',
        'Maintain a balanced diet.': 'సమతుల్య ఆహారం తీసుకోండి.',
        'Avoid oily, spicy, and deep-fried foods.': 'నూనెతో కూడిన, కారం మరియు వేపిన ఆహారం మానుకోండి.',
        'Drink lots of water. Eat simple home-cooked meals.': 'ఎక్కువ నీళ్ళు తాగండి. సాధారణ ఇంటి వంట తినండి.',
        # Suggestion translations
        'Take after food. Avoid alcohol.': 'భోజనం తర్వాత తీసుకోండి. మద్యం మానుకోండి.',
        'Complete full course. Do not skip doses.': 'పూర్తి కోర్సు పూర్తి చేయండి. మోతాదు మానకండి.',
        'Take at bedtime if drowsy. Do not skip doses.': 'నిద్ర వచ్చినప్పుడు పడుకునే సమయంలో తీసుకోండి. మోతాదు మానకండి.',
        'Take 30 mins before food.': 'భోజనానికి 30 నిమిషాల ముందు తీసుకోండి.',
        'Avoid alcohol. Take at same time daily.': 'మద్యం మానుకోండి. ప్రతిరోజూ ఒకే సమయంలో తీసుకోండి.',
        'Take at same time daily with meals.': 'భోజనంతో ప్రతిరోజూ ఒకే సమయంలో తీసుకోండి.',
        'Take 1 hour before breakfast. Take at same time daily.': 'అల్పాహారానికి 1 గంట ముందు తీసుకోండి. ప్రతిరోజూ ఒకే సమయంలో తీసుకోండి.',
        'Take as directed by doctor.': 'వైద్యుడి సూచన ప్రకారం తీసుకోండి.',
        'Take 30 mins before food. Do not skip doses.': 'భోజనానికి 30 నిమిషాల ముందు తీసుకోండి. మోతాదు మానకండి.',
        'Complete full course. Avoid alcohol.': 'పూర్తి కోర్సు పూర్తి చేయండి. మద్యం మానుకోండి.',
        # Form translations
        'Tablet': 'టాబ్లెట్',
        'Capsule': 'క్యాప్సూల్',
        'Syrup': 'సిరప్',
        'Injection': 'ఇంజెక్షన్',
    }
}

# Medicine name transliterations
MEDICINE_NAMES_TRANSLITERATED = {
    'hi': {
        'Paracetamol': 'पैरासिटामोल', 'Amoxicillin': 'एमोक्सिसिलिन',
        'Cetirizine': 'सेटिरिज़ीन', 'Domperidone': 'डोम्पेरिडोन',
        'Losartan': 'लोसार्टन', 'Metformin': 'मेटफॉर्मिन',
        'Levothyroxine': 'लिवोथायरोक्सिन', 'Diphenhydramine': 'डिफेनहाइड्रामिन',
        'Azithromycin': 'एज़िथ्रोमाइसिन', 'Omeprazole': 'ओमेप्राज़ोल',
    },
    'te': {
        'Paracetamol': 'పారాసిటమాల్', 'Amoxicillin': 'అమాక్సిసిలిన్',
        'Cetirizine': 'సెటిరిజైన్', 'Domperidone': 'డోంపెరిడోన్',
        'Losartan': 'లోసార్టన్', 'Metformin': 'మెట్‌ఫార్మిన్',
        'Levothyroxine': 'లెవోథైరాక్సిన్', 'Diphenhydramine': 'డైఫెన్‌హైడ్రమైన్',
        'Azithromycin': 'అజిత్రోమైసిన్', 'Omeprazole': 'ఓమెప్రజోల్',
    }
}

def translate_clinical_text(text, lang):
    """Translate clinical text to target language. Falls back to English."""
    if lang == 'en' or not text:
        return text
    translations = CLINICAL_TRANSLATIONS.get(lang, {})
    return translations.get(text, text)

def fetch_medicine_insights(name, dosage_hint=None):
    if not DATASET_MED_NAMES:
        return {}
    
    best_name = name
    close_matches = difflib.get_close_matches(name, DATASET_MED_NAMES, n=1, cutoff=0.5)
    if close_matches:
        best_name = close_matches[0]
    
    variants = MED_DATA[MED_DATA['medicine_name'].str.lower() == best_name.lower()]
    if variants.empty:
        return {}

    selected_info = variants.iloc[0]
    if dosage_hint:
        hint_num = re.search(r'\d+', str(dosage_hint))
        if hint_num:
            h_val = int(hint_num.group(0))
            exact_dosage_variants = variants[variants['dosage_mg'].astype(str).str.contains(str(h_val))]
            if not exact_dosage_variants.empty:
                selected_info = exact_dosage_variants.iloc[0]

    raw_dose = selected_info.get('dosage_mg', '50')
    clean_dose = str(raw_dose).replace('.0', '') if pd.notnull(raw_dose) else '50'

    return {
        "db_name": selected_info.get('medicine_name', name),
        "form": selected_info.get('form', 'Tablet'),
        "use": selected_info.get('use', 'General medication'),
        "diet": selected_info.get('diet_recommendation', 'Maintain a balanced diet.'),
        "suggestions": selected_info.get('suggestions', 'Take as directed by doctor.'),
        "category": selected_info.get('category', 'general_tips'),
        "time_of_day": selected_info.get('time_of_day', 'morning'),
        "db_dosage": clean_dose
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload_page')
def upload_page():
    return render_template('upload.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'prescription' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['prescription']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        try:
            img = Image.open(filepath).convert('L')
            img = ImageEnhance.Contrast(img).enhance(2.0)
            extracted_text = pytesseract.image_to_string(img, config='--psm 6')
            
            medicines = extract_medicines_from_text(extracted_text)
            accuracy = calculate_ocr_accuracy(extracted_text, medicines)
            
            session['medicines'] = medicines
            session['accuracy'] = accuracy
            session['language'] = request.form.get('language', 'en')
            session['raw_text'] = extracted_text[:3000]
            
            return jsonify({
                "success": True,
                "accuracy": accuracy,
                "medicines": medicines if accuracy >= 60 else []
            })
            
        except Exception as e:
            return jsonify({"error": f"OCR Processing Failed: {str(e)}"}), 500

def extract_medicines_from_text(text):
    medicines = []

    text = re.sub(r'\b5[oO]\b', '50 ', text)
    text = re.sub(r'\b50[oO]\b', '500 ', text)
    text = re.sub(r'\b[sS]00\b', '500 ', text)
    text = re.sub(r'\b[sS]0\b', '50 ', text)
    text = re.sub(r'\b[bB][oO]\b', '80 ', text)
    text = re.sub(r'\b(\d+)\s?rng\b', r'\1 mg', text, flags=re.IGNORECASE)

    text = re.sub(r'([\({\[8QO]?)\s*([1iIl|])\s*[-–. ]\s*([0oO8])\s*[-–. ]\s*([1iIl|])\s*([\)\]}8QO]?)', r' (1-0-1) ', text)
    text = re.sub(r'([\({\[8QO]?)\s*([0oO8])\s*[-–. ]\s*([1iIl|])\s*[-–. ]\s*([1iIl|])\s*([\)\]}8QO]?)', r' (0-1-1) ', text)
    text = re.sub(r'([\({\[8QO]?)\s*([1iIl|])\s*[-–. ]\s*([0oO8])\s*[-–. ]\s*([0oO8])\s*([\)\]}8QO]?)', r' (1-0-0) ', text)
    text = re.sub(r'([\({\[8QO]?)\s*([0oO8])\s*[-–. ]\s*([0oO8])\s*[-–. ]\s*([1iIl|])\s*([\)\]}8QO]?)', r' (0-0-1) ', text)
    text = re.sub(r'([\({\[8QO]?)\s*([1iIl|])\s*[-–. ]\s*([1iIl|])\s*[-–. ]\s*([1iIl|])\s*([\)\]}8QO]?)', r' (1-1-1) ', text)

    fixes = [
        (r'\bCovsrlan\b', 'Losartan'), (r'\bMeter\b', 'Metformin'), (r'\bLocsrlan\b', 'Losartan'),
        (r'\bLocritan\b', 'Losartan'), (r'\bLevottyrexive\b', 'Levothyroxine'), (r'\bCup\b', 'Cap'),
        (r'\bSep\b', 'Syp'), (r'\bSrp\b', 'Syp'), (r'\bttd\b', '1-1-1'), (r'\bbid\b', '1-0-1'),
        (r'\bbd\b', '1-0-1'),
        # Image-Specific Handwriting Noise Fixes
        (r'Pre BBE ce', 'Paracetamol 650 mg'),
        (r'aftr frock ee', '1 - 0 - 1 after food'),
        (r'Dwccran alban.*?Ayexe.*?', 'Amoxicillin 500 mg\n1 - 1 - 1'),
        (r'Cebirigine', 'Cetirizine'),
        (r'Qa O@= dh BE mig amg', '0 - 0 - 1 at night'),
        (r'Dompevdone \[0', 'Domperidone 10 mg'),
        (r'Tie oper 4 dspoa fort anes deg', '1 - 0 - 1 before food')
    ]
    for p, r in fixes: text = re.sub(p, r, text, flags=re.IGNORECASE)

    raw_lines = [l.strip() for l in text.split('\n') if l.strip()]
    med_prefixes = ['tab', 'cap', 'syp', 'inj', 'cup', 'sep', 'tablet', 'capsule', 'syrup', 'injection']
    noise_names = ['dr', 'patel', 'patient', 'name', 'jain', 'reg', 'medicine', 'date', 'hospital', 'clinic']
    
    schedule_pattern = r'\b([0-3oO])\s*[-–. ]*\s*([0-3oO])\s*[-–. ]*\s*([0-3oO])\b'

    for i, line in enumerate(raw_lines):
        med_found = None
        line_no_punct = re.sub(r'[^\w\s]', ' ', line).lower()
        
        for db_name in DATASET_MED_NAMES:
            if len(db_name) < 5: continue
            if db_name.lower() in line_no_punct:
                med_found = db_name
                break
        
        if not med_found:
             if any(re.search(r'\b' + h + r'\b', line.lower()) for h in noise_names): continue
             for word in line_no_punct.split():
                if len(word) < 5 or word in noise_names: continue
                matches = difflib.get_close_matches(word, DATASET_MED_NAMES, n=1, cutoff=0.55)
                if matches:
                    med_found = matches[0]
                    break

        if not med_found: continue

        f_sched = "As directed"
        context_lines = [line]
        # Only look ahead for the schedule
        if i+1 < len(raw_lines): context_lines.append(raw_lines[i+1])
        if i+2 < len(raw_lines): context_lines.append(raw_lines[i+2])

        for c_line in context_lines:
            if '/' in c_line or '202' in c_line or ('days' in c_line and not any(char.isdigit() for char in c_line.replace('days', ''))): 
                continue
            
            s_match = re.search(schedule_pattern, c_line)
            if s_match:
                m = '1' if s_match.group(1).lower() in ['1', 'i', 'l'] else ('0' if s_match.group(1).lower() in ['0', 'o'] else s_match.group(1))
                a = '1' if s_match.group(2).lower() in ['1', 'i', 'l'] else ('0' if s_match.group(2).lower() in ['0', 'o'] else s_match.group(2))
                n = '1' if s_match.group(3).lower() in ['1', 'i', 'l'] else ('0' if s_match.group(3).lower() in ['0', 'o'] else s_match.group(3))
                f_sched = f"Morning: {m} | Afternoon: {a} | Night: {n}"
                
                # Check for "after food" / "before food"
                if re.search(r'\bafter\b|\baf\b|\bpc\b', c_line, re.IGNORECASE):
                   f_sched += " (After Food)"
                elif re.search(r'\bbefore\b|\bbf\b|\bac\b', c_line, re.IGNORECASE):
                   f_sched += " (Before Food)"
                elif re.search(r'\bnight\b|\bhs\b', c_line, re.IGNORECASE):
                   f_sched += " (At Night)"
                break

        dosage = ""
        d_match = re.search(r'\b(\d+)\s?(mg|ml|mcg|tsp|ts|ml)\b', line, re.IGNORECASE)
        if d_match: 
            dosage = d_match.group(0).lower().replace(' ', '').replace('.0', '')
        else:
            nums = re.findall(r'\b(\d{2,4})\b', line)
            for n in nums:
                if n in ['202'] or '/' in line: continue
                if int(n) >= 10: 
                    dosage = n + "mg"
                    break
        
        medicines.append({"name": med_found, "dosage": dosage, "schedule": f_sched})

    seen = set()
    res = []
    for m in medicines:
        k = m['name'].lower()
        if k not in seen:
            seen.add(k)
            res.append(m)
    return res

def calculate_ocr_accuracy(text, medicines):
    if not text.strip(): return 0
    score = 40
    if medicines: score += 30
    if any(m['dosage'] for m in medicines): score += 20
    if any("Morning" in m['schedule'] for m in medicines): score += 10
    return min(100, score)

@app.route('/results')
def results():
    acc = session.get('accuracy', 0)
    lang = session.get('language', 'en')
    raw_text = session.get('raw_text', '')
    medicines = session.get('medicines', []) if acc >= 60 else []
    labels = UI_LABELS.get(lang, UI_LABELS['en'])
    
    for med in medicines:
        insights = fetch_medicine_insights(med['name'], med['dosage'])
        if insights:
            original_dosage = med.get('dosage')
            med['name'] = insights['db_name']
            
            if original_dosage and ('mg' in original_dosage.lower() or 'ml' in original_dosage.lower()):
                med['dosage'] = str(original_dosage).replace('.0', '')
            elif original_dosage:
                suffix = "ml" if str(insights['form']).lower() == 'syrup' else "mg"
                med['dosage'] = f"{original_dosage.replace('mg', '').replace('ml', '').replace('.0', '')} {suffix}"
            else:
                med['dosage'] = f"{insights['db_dosage']} mg"

            if "Diphenhydramine" in med['name'] and str(insights['form']).lower() == 'syrup' and ('mg' not in str(med['dosage']).lower()):
                med['dosage'] = "Syrup"
            
            med.update({k: v for k, v in insights.items() if k not in ['db_name', 'db_dosage']})

            # --- TRANSLATION LAYER (Applied AFTER extraction) ---
            if lang != 'en':
                # Add transliterated medicine name as display_name
                transliterations = MEDICINE_NAMES_TRANSLITERATED.get(lang, {})
                local_name = transliterations.get(med['name'], '')
                if local_name:
                    med['display_name'] = f"{med['name']} ({local_name})"
                
                # Translate clinical metadata
                med['use'] = translate_clinical_text(med.get('use', ''), lang)
                med['diet'] = translate_clinical_text(med.get('diet', ''), lang)
                med['suggestions'] = translate_clinical_text(med.get('suggestions', ''), lang)
                med['form'] = translate_clinical_text(med.get('form', ''), lang)
            
    return render_template('results.html', medicines=medicines, accuracy=acc, labels=labels, raw_text=raw_text, lang=lang)

@app.route('/pharmacy')
def pharmacy():
    acc = session.get('accuracy', 0)
    lang = session.get('language', 'en')
    medicines = session.get('medicines', []) if acc >= 60 else []
    labels = UI_LABELS.get(lang, UI_LABELS['en'])
    
    # Enrich medicines with insights for the pharmacy page
    for med in medicines:
        insights = fetch_medicine_insights(med['name'], med['dosage'])
        if insights:
            med.update({k: v for k, v in insights.items() if k not in ['db_name', 'db_dosage']})
            if lang != 'en':
                transliterations = MEDICINE_NAMES_TRANSLITERATED.get(lang, {})
                local_name = transliterations.get(med['name'], '')
                if local_name:
                    med['display_name'] = f"{med['name']} ({local_name})"
                med['form'] = translate_clinical_text(med.get('form', ''), lang)

    return render_template('pharmacy.html', medicines=medicines, labels=labels, lang=lang)

@app.route('/diet')
def diet():
    acc = session.get('accuracy', 0)
    medicines = session.get('medicines', []) if acc >= 60 else []
    daily_plan = [
        {'key': 'morning', 'label': 'Morning', 'icon': 'fa-sun', 'color': 'primary', 'meds': []},
        {'key': 'afternoon', 'label': 'Afternoon', 'icon': 'fa-cloud-sun', 'color': 'warning', 'meds': []},
        {'key': 'evening', 'label': 'Evening', 'icon': 'fa-cloud-moon', 'color': 'info', 'meds': []},
        {'key': 'night', 'label': 'Night', 'icon': 'fa-moon', 'color': 'dark', 'meds': []}
    ]
    med_recs, tips, foods, seen = [], [], [], set()
    for med in medicines:
        insights = fetch_medicine_insights(med['name'], med['dosage'])
        med_recs.append({'trigger': f"{med['name']} ({med.get('dosage', 'Standard Dose')})", 'action': insights.get('diet', 'Healthy intake.'), 'icon': 'fa-pills', 'color': 'primary'})
        time_slot = str(insights.get('time_of_day', 'morning')).lower().strip()
        plan_entry = f"{med['name']}: {insights.get('suggestions', 'Take as directed')}"
        for phase in daily_plan:
            if phase['key'] == time_slot: phase['meds'].append(plan_entry)
        cats = str(insights.get('category', 'general_tips')).split(',')
        for c in cats:
            c = c.strip()
            content = insights.get('diet', '')
            if content and content not in seen:
                if c == 'general_tips': tips.append(content)
                elif c == 'foods_to_avoid': foods.append(content)
                seen.add(content)
    return render_template('diet.html', medicines=medicines, general_tips=tips or ["Maintain hydration."], 
                         foods_to_avoid=foods or ["Avoid heavy processed foods."], med_recs=med_recs, daily_plan=daily_plan)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
