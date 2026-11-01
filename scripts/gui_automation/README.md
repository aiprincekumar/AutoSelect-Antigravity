# 🖱️ Modular Step-by-Step GUI Mouse Automation Pipeline
## (मॉड्यूलर स्टेप-बाय-स्टेप जीयूआई माउस ऑटोमेशन पाइपलाइन)

> **Repository:** [`AutoSelect-Commander`](file:///C:/Users/Atul%20Verma/Desktop/AutoSelect-Commander/)  
> **Location:** [`scripts/gui_automation/`](file:///C:/Users/Atul%20Verma/Desktop/AutoSelect-Commander/scripts/gui_automation/)  
> **Author:** Atul Verma (`aiprincekumar` / `aiprincekumar010100@gmail.com`)  
> **Environment:** Python 3.12+ | PyAutoGUI | Pillow  

---

## 📌 1. समस्या विश्लेषण और समाधान (Problem & Architectural Solution)

### ❓ पहले क्या समस्या आ रही थी? (Why previous automation hung)
उपयोगकर्ता द्वारा बताई गई समस्या:
> *"हर एक स्टेप के लिए जो माउस होवर कर रहा है, क्लिक कर रहा है, उसके लिए एक अलग पाइथन स्क्रिप्ट फाइल बनाना है। क्योंकि फर्स्ट स्टेप पर ही जाकर के रुक जा रहा है। माउस खोज रहा है कहाँ पर क्लिक करना, वहाँ पर ड्रैग हो रहा है, क्लिक कर रहा है, बस वहीं पर रुक जा रहा है। मतलब कि दो स्टेप पार कर रहा है, ड्रैग करा, लोकेशन पर और क्लिक किया, उसके बाद रुक गया। उसके बाद जो उसको ड्रैग करना है, रिकमेंडेशन ऑप्शन पर वहाँ पर जा ही नहीं रहा है। फिर तो सिलेक्ट क्या करेगा? और उसके बाद फिर सबमिट पर ड्रैग करना है, फिर तब क्लिक करना है, सबमिट पर। यह तो चार ऑप्शन छोड़ दे रहा है।"*

### 🛠️ तकनीकी कारण (Root Causes):
1. **Monolithic Hang:** पहले सभी स्टेप्स एक ही स्क्रिप्ट और टाइट लूप में चलने के कारण पहले क्लिक के बाद रुक जाते थे।
2. **Missing UI Settle Delay:** पहले क्लिक के बाद GUI / DOM को ऑप्शन कार्ड या रेडियो बटन रेंडर करने के लिए 0.5s से 1.2s का समय चाहिए होता है।
3. **No Per-Step Isolation:** स्टेप्स अलग न होने के कारण अगर कोई एक स्टेप फेल या मिस हुआ तो आगे के स्टेप्स (Recommended Option, Submit Button) एग्जीक्यूट ही नहीं होते थे।

### 💡 नया आर्किटेक्चर समाधान (Modular Pipeline Solution):
हर एक स्टेप को **पूर्णतः स्वतंत्र (Isolated), डीबगेबल और अलग स्क्रिप्ट फाइल** में विभाजित कर दिया गया है। आप हर एक स्टेप को अलग-अलग चला सकते हैं या मास्टर पाइपलाइन के ज़रिये क्रमबद्ध (Sequentially) चला सकते हैं।

---

## 📂 2. फाइलों की सूची (File Manifest)

| फाइल का नाम (File Name) | उद्देश्य (Purpose) | चलाने का तरीका (Execution Command) |
| :--- | :--- | :--- |
| [`config.json`](file:///C:/Users/Atul%20Verma/Desktop/AutoSelect-Commander/scripts/gui_automation/config.json) | सभी स्टेप्स के कोर्डिनेट्स (X, Y), डिले और सेटिंग्स। | JSON कॉन्फ़िगरेशन फाइल |
| [`common_utils.py`](file:///C:/Users/Atul%20Verma/Desktop/AutoSelect-Commander/scripts/gui_automation/common_utils.py) | स्मूथ बेज़ियर मूवमेंट (`easeOutQuad`), होवर व क्लिक इंजन। | शेयर्ड यूटिलिटी मॉड्यूल |
| [`step1_open_and_click_chat.py`](file:///C:/Users/Atul%20Verma/Desktop/AutoSelect-Commander/scripts/gui_automation/step1_open_and_click_chat.py) | **स्टेप 1:** चैट एरिया पर स्मूथ माउस मूवमेंट, होवर व फोकस क्लिक। | `python step1_open_and_click_chat.py` |
| [`step2_select_recommended_option.py`](file:///C:/Users/Atul%20Verma/Desktop/AutoSelect-Commander/scripts/gui_automation/step2_select_recommended_option.py) | **स्टेप 2:** `(Recommended)` ऑप्शन / रेडियो बटन पर नेविगेट, होवर व सेलेक्ट। | `python step2_select_recommended_option.py` |
| [`step3_click_submit_button.py`](file:///C:/Users/Atul%20Verma/Desktop/AutoSelect-Commander/scripts/gui_automation/step3_click_submit_button.py) | **स्टेप 3:** `Submit` / कन्फर्म बटन पर स्मूथ मूवमेंट, होवर व सबमिट क्लिक। | `python step3_click_submit_button.py` |
| [`step4_verify_execution.py`](file:///C:/Users/Atul%20Verma/Desktop/AutoSelect-Commander/scripts/gui_automation/step4_verify_execution.py) | **स्टेप 4:** माउस रिलीज चेक, स्टेट सेटल व एविडेंस स्क्रीनशॉट। | `python step4_verify_execution.py` |
| [`run_pipeline.py`](file:///C:/Users/Atul%20Verma/Desktop/AutoSelect-Commander/scripts/gui_automation/run_pipeline.py) | **मास्टर रनर:** स्टेप 1 -> 2 -> 3 -> 4 को एक साथ व्यवस्थित अंतराल के साथ चलाता है। | `python run_pipeline.py` |
| [`calibrate_coordinates.py`](file:///C:/Users/Atul%20Verma/Desktop/AutoSelect-Commander/scripts/gui_automation/calibrate_coordinates.py) | **कैलिब्रेशन टूल:** आपकी स्क्रीन के अनुसार वास्तविक (X, Y) सेव करने हेतु। | `python calibrate_coordinates.py` |

---

## ⚡ 3. इंस्टॉलेशन व आवश्यकताएं (Prerequisites & Setup)

यह लाइब्रेरी Python 3.10+ में काम करती है। आवश्यक पैकेज स्थापित करें:

```bash
# Standard Python pip
pip install pyautogui pillow

# या uv पैकेज मैनेजर के माध्यम से:
uv pip install pyautogui pillow
```

---

## 🎯 4. उपयोग की विधि (How to Use)

### 🔹 विधि 1: एक-एक स्टेप को अलग-अलग चलाना (Step-by-Step Isolated Execution)

यदि आप हर स्टेप को खुद परखना चाहते हैं या किसी एक स्टेप पर रुक कर देखना चाहते हैं:

#### स्टेप 1: चैट विंडो / इनपुट पर क्लिक करना
```bash
python scripts/gui_automation/step1_open_and_click_chat.py
```
*(3 सेकंड का काउंटडाउन मिलेगा ताकि आप अपने इच्छित विंडो पर स्विच कर सकें। माउस चैट पर जाएगा, 0.5s होवर करेगा, और क्लिक करेगा।)*

#### स्टेप 2: (Recommended) ऑप्शन सेलेक्ट करना
```bash
python scripts/gui_automation/step2_select_recommended_option.py
```
*(माउस स्मूथ गति से रिकमेंडेड ऑप्शन पर जाएगा, 0.7s होवर इफ़ेक्ट ट्रिगर करेगा और ऑप्शन पर क्लिक करके उसे सेलेक्ट करेगा।)*

#### स्टेप 3: Submit बटन पर क्लिक करना
```bash
python scripts/gui_automation/step3_click_submit_button.py
```
*(माउस सबमिट बटन पर जाएगा, होवर करेगा और सबमिट पर क्लिक करेगा।)*

#### स्टेप 4: परिणाम और स्टेटस वेरीफाई करना
```bash
python scripts/gui_automation/step4_verify_execution.py
```
*(सत्यापित करेगा कि माउस बटन रिलीज हो चुका है और `screenshots/` में एविडेंस स्क्रीनशॉट सेव करेगा।)*

---

### 🔹 विधि 2: पूरा पाइपलाइन एक बार में चलाना (Master Pipeline Execution)

चारों स्टेप्स को एक साथ क्रमबद्ध चलाने के लिए:

```bash
# पूरा पाइपलाइन चलाएं (स्टेप 1 -> स्टेप 2 -> स्टेप 3 -> स्टेप 4)
python scripts/gui_automation/run_pipeline.py

# केवल ड्राई-रन (बिना क्लिक किए केवल माउस मूवमेंट और होवर टेस्ट करना)
python scripts/gui_automation/run_pipeline.py --dry-run

# स्टेप्स के बीच 2 सेकंड का कस्टम डिले देना (धीमे रेंडर होने वाले GUI के लिए)
python scripts/gui_automation/run_pipeline.py --delay 2.0

# पाइपलाइन से केवल स्टेप 2 चलाना
python scripts/gui_automation/run_pipeline.py --step 2
```

---

### 🔹 विधि 3: अपनी स्क्रीन के अनुसार कोर्डिनेट कैलिब्रेट करना (Coordinate Calibration)

अलग-अलग मॉनिटर रिज़ॉल्यूशन (1080p, 2K, 4K) या विंडो साइज के लिए कोर्डिनेट सेट करना बहुत आसान है:

```bash
# 1. इंटरैक्टिव विज़ार्ड चलाएं:
python scripts/gui_automation/calibrate_coordinates.py
```
*विज़ार्ड आपसे कहेगा:*
1. माउस को चैट एरिया पर रखें -> एंटर दबाएं।
2. माउस को (Recommended) ऑप्शन पर रखें -> एंटर दबाएं।
3. माउस को Submit बटन पर रखें -> एंटर दबाएं।
*यह जानकारी सीधे `config.json` में ऑटोमैटिक सेव हो जाएगी!*

```bash
# 2. लाइव माउस कोर्डिनेट ट्रैकर देखना:
python scripts/gui_automation/calibrate_coordinates.py --live

# 3. वर्तमान में सेव कोर्डिनेट्स देखना:
python scripts/gui_automation/calibrate_coordinates.py --show
```

---

## 🛡️ 5. सुरक्षा एवं इमरजेंसी स्टॉप (Failsafe Safety)

- **इमरजेंसी स्टॉप (Emergency Kill-Switch):** किसी भी समय ऑटोमेशन को तुरंत रोकने के लिए अपने माउस को स्क्रीन के **टॉप-लेफ्ट कोने (0, 0)** पर ले जाएं। `pyautogui.FailSafeException` तुरंत ट्रिगर होकर स्क्रिप्ट को रोक देगा।
- **ड्राई-रन मोड (`--dry-run`):** वास्तविक क्लिक करने से पहले आप माउस का पाथ और होवरिंग बिना किसी क्लिक के टेस्ट कर सकते हैं।
- **एविडेंस स्क्रीनशॉट्स:** हर स्टेप का परिणाम `scripts/gui_automation/screenshots/` में टाइमस्टैम्प के साथ सेव होता है।
