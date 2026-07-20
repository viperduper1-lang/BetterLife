# BetterLife 🥗🏋️

Remindere automate de **mese** și **antrenament**, trimise ca **push pe iPhone** (prin
[ntfy](https://ntfy.sh)), rulate gratuit în cloud cu **GitHub Actions**.

Te anunță când e timpul să mănânci (ca să nu mai mănânci neregulat), îți amintește
limita de calorii pe fiecare masă, îți dă grupa musculară de azi (biceps / triceps /
repaus) și goal-ul de calorii arse la bandă. La 21:30 „închide ziua" și te lasă liber
pentru proiectele tale.

Tot ce setezi tu (ore, calorii, gustări, antrenament) e într-un singur fișier:
**`config.yaml`**.

## Din ce e făcut

BetterLife are **două părți** care folosesc același `config.yaml`:

| Parte | Ce face | Când merge |
|-------|---------|------------|
| **Remindere cloud** (`notify.py` + GitHub Actions) | Îți trimit push pe iPhone la orele setate | Non-stop, chiar și cu PC-ul închis |
| **Aplicația desktop** (`BetterLife.exe`) | Frigider + plan pe 7 zile + calculator calorii + jurnal + buget | Când ești la PC |

Poți folosi doar aplicația desktop, doar reminderele cloud, sau amândouă.

---

## 🖥️ Aplicația desktop (BetterLife.exe)

**Dublu-click pe `BetterLife.exe`** — nu trebuie instalat nimic (interfață premium,
cu emoji color, prin WebView2 — deja prezent pe Windows 11). Are cinci secțiuni:

- **📊 Azi** — cât buget de calorii ți-a mai rămas azi (cu bară de progres), ce ai
  mâncat, grupa musculară de azi. Poți șterge intrări sau goli ziua.
- **🧊 Frigider** — bifezi ce alimente ai și **pui cât ai din fiecare** (în grame, kg
  sau bucăți — ex. „6 ouă", „500 g pui"). Fiecare cu emoji și calorii/100g. Caută/filtrează.
- **🗓️ Plan 7 zile** — apeși **„Generează planul"** și primești un **tabel pe 7 zile**
  cu antrenament + mic dejun / gustări / prânz / cină, folosind **doar ce ai în frigider,
  în limita cantităților** (nu-ți propune mai mult pui decât ai) și **fără să depășești
  limita fiecărei zile**. „🔀 Altă variantă" reshufflează.
- **🏋️ Antrenament editabil** (în tab-ul Plan) — alegi grupa musculară pe fiecare zi;
  **cardio la bandă în fiecare zi**; te avertizează dacă pui **două zile la rând aceeași
  grupă** și are **„Auto-aranjează"** care rotește corect grupele.
- **🧮 Calculator calorii** — scrii **numele produsului** și **caloriile** lui (la 100 g
  sau la porție), apeși **„Cât pot mânca?"** și îți spune câte grame poți mânca **fără
  să depășești limita zilnică**. Poți verifica o cantitate anume și o adaugi în ziua
  de azi cu un click. Poți alege produsul din listă ca să se completeze caloriile.
- **⚙️ Setări** — limita zilnică implicită de kcal, deschidere `config.yaml` și
  **conectarea contului GitHub** + butonul **„🔄 Trimite pe GitHub"**.

**Limita de kcal per zi** o setezi în tab-ul **Plan 7 zile** (câte o valoare pentru
fiecare zi a săptămânii) sau global în **Setări**.

### 🔔 Notificări pe telefon — din aplicație

Reminderele pe telefon rulează din cloud (GitHub Actions). Ca să rămână la zi cu
programul tău:

1. În **Setări**, lipește adresa repo-ului tău GitHub și apasă **„🔗 Conectează"**
   (prima dată se poate deschide browserul pentru login GitHub).
2. Ori de câte ori schimbi programul sau generezi săptămâna, apasă
   **„🔄 Trimite pe GitHub"** (și din Setări, și din tab-ul Plan).

Notificările pe telefon sunt **premium**: titlu cu emoji, priorități, tag-uri și
**iconița BetterLife** (bolul de salată) afișată pe fiecare notificare — imaginea e
`icon.png` din repo, iar în cloud se folosește automat (repo public).

Odată configurate, notificările merg **automat, non-stop** — nu trebuie să trimiți
în fiecare zi. Butonul e doar pentru a duce în cloud **modificările** tale.

Datele tale locale: `food_log.json` (jurnal), `pantry.json` (frigider),
`plan.json` (planul), `settings.json` (limite). Toate stau lângă exe.

### Rulare din sursă (fără exe)

```powershell
pip install -r requirements-app.txt
python app.py
```

### Reconstruire exe (după ce modifici codul)

Dublu-click pe **`build_exe.bat`** (sau rulează comanda din el). Rezultatul e
`BetterLife.exe` în folderul proiectului.

---

## 1. Instalează ntfy pe iPhone (2 min)

1. App Store → caută **„ntfy"** → instalează.
2. Deschide app-ul → **+** → **Subscribe to topic**.
3. Scrie exact același topic pe care îl pui în `config.yaml` (câmpul `ntfy.topic`).
   Alege ceva unic și secret, de ex. `betterlife-viper-9x7q2`.
4. Gata — orice notificare trimisă pe acel topic apare pe iPhone.

> Topicul e ca o parolă: oricine îl știe îți poate trimite notificări. Ține-l privat.

## 2. Test rapid pe PC (opțional, dar satisfăcător)

În folderul proiectului:

```powershell
pip install -r requirements.txt
python notify.py --list           # vezi tot programul + grupa musculară de azi
python notify.py --test breakfast # trimite ACUM un push de test pe iPhone
```

Dacă push-ul ajunge pe telefon, totul e legat corect. Chei valide pentru `--test`:
`breakfast`, `snack_am`, `lunch`, `snack_pm`, `workout`, `dinner`, `day_close`.

## 3. Pune-l în cloud, ca să meargă și cu PC-ul închis

1. Creează un repository nou pe GitHub și urcă aceste fișiere:
   ```powershell
   git init
   git add .
   git commit -m "BetterLife MVP"
   git branch -M main
   git remote add origin https://github.com/UTILIZATORUL_TAU/betterlife.git
   git push -u origin main
   ```
2. Pe GitHub: tab **Actions** → activează workflow-urile (dacă îți cere).
3. **Topicul** — două variante:
   - **Repo privat:** lasă topicul în `config.yaml`, e destul.
   - **Repo public:** scoate topicul din `config.yaml` și pune-l ca secret:
     **Settings → Secrets and variables → Actions → New secret**,
     nume `NTFY_TOPIC`, valoarea = topicul tău.
4. Testează în cloud: **Actions → BetterLife reminders → Run workflow**.

Gata. De acum primești push-uri automat la orele din `config.yaml`.

> **Gratuit:** repo **public** = minute GitHub Actions nelimitate (recomandat).
> Repo **privat** = 2000 min/lună gratis; verificarea la 15 min intră lejer în limită.

---

## Cum îți schimbi programul

Editează **`config.yaml`** (și `git push`, dacă e în cloud). Poți schimba:

- **Orele** meselor și gustărilor (`time: "HH:MM"`, oră locală).
- **Limitele de calorii** pe masă (`kcal_cap`) și **totalul zilnic** (`daily_kcal_cap`).
- **Gustările** (`options:` — mărul, iaurtul etc.).
- **Antrenamentul**: `workout.schedule` (ce grupă în ce zi, `Repaus` = odihnă),
  `treadmill_kcal_goal` (goal calorii bandă), `workout.details` (serii × repetări).
- **Textul** oricărei notificări (`message:`).

Nu trebuie să atingi niciodată orarul din GitHub Actions — scriptul calculează singur
ora corectă în `Europe/Bucharest` și se adaptează automat la ora de vară/iarnă.

## Cum funcționează (pe scurt)

- GitHub Actions rulează `notify.py --send-due` la fiecare 15 min.
- Scriptul se uită ce oră e (fus `Europe/Bucharest`) și trimite reminderele „scadente".
- `state.json` reține ce s-a trimis azi, ca să nu primești același push de două ori.

## Idei pentru pașii următori

- ✅ Calculator de calorii + jurnal zilnic (mâncat vs. limită) — gata.
- ✅ Frigider cu cantități + plan pe 7 zile în limita stocului real — gata.
- ✅ Antrenament editabil în plan (cardio zilnic, fără zile consecutive identice) — gata.
- ✅ Limită de kcal per zi + notificări premium pe telefon — gata.
- ✅ Conectare + trimitere pe GitHub din aplicație — gata.
- Adaugă propriile alimente în bază (produse cu ambalaj, rețete).
- Listă de cumpărături din planul săptămânal (ce-ți lipsește).
- Email-sumar seara cu bilanțul zilei.
