# Step 5 Automation: Antigravity Lifecycle Sentinel Subsystem

> **सबसिस्टम:** Step 5 Automation (Zero-Touch Lifecycle Sentinel & Task Orchestrator)  
> **डेवलपर:** Atul Verma (`aiprincekumar` / `aiprincekumar010100@gmail.com`)  
> **प्रोजेक्ट:** AutoSelect-Commander Automation Suite (`Keyboard Automation/`)  
> **स्टैंडर्ड:** Department 12 (DevOps, Build & Release), Department 06 (Backend), Department 13 (SRE & Process Control)

---

## 🎯 मुख्य उद्देश्य (Core Mission)

इस सबसिस्टम का उद्देश्य Antigravity IDE के साथ ऑटो-रन सर्वर और स्टेप 0 से 4 तक के टास्क ऑटोमेशन को **100% Zero-Touch (बिना किसी क्लिक या कमांड के)** सिंक करना है:

1. **Windows Login / Startup:**
   - विंडोज़ ऑन होने पर यह बैकग्राउंड सेंटिनल साइलेंटली एक्टिव हो जाता है (0.00% CPU, no console window).
2. **जैसे ही Antigravity स्टार्ट होती है:**
   - सेंटिनल तुरंत डिटेक्ट करता है (`Antigravity.exe`).
   - हेडलेस मोड में `dashboard_server.py` (Port 8501) ऑटोमैटिक स्टार्ट होता है।
   - सर्वर उठते ही स्टेप 0 से 4 का संपूर्ण ऑटोमेशन टास्क (`/api/automation/start`) ऑटोमैटिक एक्टिवेट हो जाता है।
   - डैशबोर्ड खोलने पर स्टार्ट बटन पहले से ही 'Active / Running' स्थिति में मिलेगा।
3. **जैसे ही Antigravity बंद (Exit / X) होती है:**
   - सेंटिनल डिटेक्ट करता है कि Antigravity बंद हो चुकी है।
   - ऑटोमेशन टास्क सुरक्षित रूप से बंद (`/api/automation/stop`) हो जाता है।
   - डैशबोर्ड सर्वर प्रोसेस क्लीनली टर्मिनेट हो जाती है और पोर्ट 8501 तुरंत रिलीज हो जाता है (Zero dangling processes, Zero port locks).

---

## 📁 सबसिस्टम फाइल संरचना (File Topology)

```
step_5_automation/
├── __init__.py                          # Python package entrypoint
├── antigravity_lifecycle_sentinel.py    # कोर लाइफसाइकिल सेंटिनल इंजन (Win32 ctypes scanner)
├── start_sentinel_background.vbs       # हेडलेस VBScript लॉन्चर (WindowStyle 0 - कोई पॉपअप नहीं)
├── stop_sentinel.bat                   # मैन्युअल स्टॉप स्क्रिप्ट (सेंटिनल + सर्वर + ऑटोमेशन क्लीन शटडाउन)
├── install_startup_shortcut.bat         # विंडोज़ स्टार्टअप फोल्डर में ऑटो-बूट शॉर्टकट स्थापित करने वाला इंस्टालर
├── uninstall_startup_shortcut.bat       # विंडोज़ स्टार्टअप से ऑटो-बूट हटाने वाला अनइंस्टालर
├── test_sentinel.py                    # यूनिट और इंटीग्रेशन टेस्ट सूट (7/7 टेस्ट पास)
├── sentinel_state.json                 # लाइव टेलीमेट्री स्थिति और टाइमस्टैम्प (ऑटो-जनरेटेड)
├── sentinel.log                        # रोलिंग रोटेटिंग लॉग फाइल (मैक्स 512KB)
└── README.md                           # यह विस्तृत गाइड और आर्किटेक्चर दस्तावेज़
```

---

## 🚀 इस्तेमाल करने का तरीका (One-Click Setup)

### 1. विंडोज़ स्टार्टअप में एक्टिवेट करना (Life-Long Automation)
फ़ोल्डर में मौजूद `install_startup_shortcut.bat` पर सिर्फ एक बार डबल-क्लिक करें:
```cmd
step_5_automation\install_startup_shortcut.bat
```
*यह आपके Windows Startup फ़ोल्डर में शॉर्टकट जोड़ देगा और सेंटिनल को तुरंत बैकग्राउंड में चालू कर देगा। इसके बाद आपको कभी भी इसे दोबारा हाथ नहीं लगाना पड़ेगा।*

### 2. मैन्युअल टेस्ट या रन करना
- **लाइव स्थिति जांचना:**
  ```cmd
  .venv\Scripts\python.exe step_5_automation\antigravity_lifecycle_sentinel.py --status
  ```
- **एक बार सिंगल चेक चलाना:**
  ```cmd
  .venv\Scripts\python.exe step_5_automation\antigravity_lifecycle_sentinel.py --check
  ```
- **सब कुछ तुरंत स्टॉप करना:**
  ```cmd
  step_5_automation\stop_sentinel.bat
  ```

---

## 🧪 टेस्ट सूट (Verification Proof)

सभी 7 यूनिट टेस्ट सफलतापूर्वक प्रमाणित हैं:
```cmd
.venv\Scripts\python.exe -m unittest step_5_automation\test_sentinel.py
```
```
Ran 7 tests in 1.570s
OK
```
