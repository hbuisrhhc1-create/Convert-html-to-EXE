# 🚀 Universal Dynamic App Builder (HTML to EXE)

כלי אוטומטי המבוסס על **GitHub Actions** להמרת אתרי אינטרנט או קבצי HTML מקומיים לאפליקציית Windows שולחנית עצמאית (`.exe`) המבוססת על **.NET 8** ו-**Microsoft WebView2**.

---

## ✨ תכונות עיקריות

* **קובץ EXE עצמאי (Single-File Self-Contained):** יצירת קובץ הירצה יחיד שאינו דורש התקנת .NET Framework/SDK במחשב היעד.
* **חלון גרפי נקי:** האפליקציה רצה במוד `WinExe` ללא חלון קונסולה שחור ברקע.
* **חילוץ אייקון אוטומטי:**
  * זיהוי קובצי תמונה מקומיים ב-Repository (`favicon.png`, `icon.png`, `favicon.ico`).
  * חילוץ אוטומטי של ה-Favicon מתגיות ה-HTML של אתר יעד.
  * Fallback לשירות חילוץ אייקונים ברזולוציה גבוהה לפי דומיין.
  * צריבת האייקון לתוך ה-EXE והחלתו על סרגל המשימות והחלון בזמן ריצה.
* **התקנה אוטומטית של WebView2 Runtime:** במידה ורכיב ה-WebView2 חסר במחשב הלקוח, התוכנה תציע להוריד להתקין אותו אוטומטית דרך ה-Evergreen Bootstrapper של Microsoft.
* **הטמעת גרסה ומטא-דאטה:** שתילת שם התוכנה, הגרסה ושם החברה ישירות בתוך פרטי הקובץ (Properties -> Details).

---

## ⚙️ פרמטרי קלט (Workflow Inputs)

| שם הפרמטר | סוג | חובה | ברירת מחדל | תיאור |
| :--- | :--- | :--- | :--- | :--- |
| `website_url` | String | לא | *ריק* | כתובת אתר מלאה (`https://...`). במידה ומולא, יוגדר כמקור הראשי. |
| `local_html_file` | String | לא | `index.html` | נתיב לקובץ HTML מקומי ב-Repository (משמש במידה ו-`website_url` ריק). |
| `app_name` | String | **כן** | `MyWebApp` | שם האפליקציה (יצוין בכותרת החלון ובשם הקובץ). |
| `app_version` | String | **כן** | `1.0.0` | גרסת התוכנה שתוטמע במאפייני ה-EXE. |
| `include_assets` | Boolean | **כן** | `false` | האם לארוז את קובץ ה-EXE יחד עם קבצים נלווים בקובץ ZIP. |

---

## 🚀 איך להריץ

### אפשרות 1: דרך ממשק GitHub (Web UI)
1. היכנס בלשונית **Actions** במאגר.
2. בחר ב-Workflow: **Universal Dynamic App Builder**.
3. לחץ על **Run workflow**.
4. הזן את הפרטים המבוקשים ולחץ על **Run workflow**.
5. בגמר ההרצה, הורד את ה-Artifact שנוצר בתחתית עמוד הריצה.

### אפשרות 2: דרך ה-CLI (`gh`)
```bash
gh workflow run build.yml \
  --repo username/repository-name \
  --field website_url="[https://example.com](https://example.com)" \
  --field app_name="MyCustomApp" \
  --field app_version="1.2.0" \
  --field include_assets="false"
