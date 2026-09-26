# VoiceTrans AI - Nidaamka Wicitaanka Cod-ilaa-Cod ee AI (Real-Time Voice-to-Voice Call Translation)

Nidaam wicitaan toos ah (Real-Time Voice Call) oo labo qof ku wada hadlayaan luqado kala duwan (tusaale **Af-Soomaali**, **English**, **Carabi**, **Turki**, **Sawaaxili**, iwm). Codka qof kasta waxaa isla markiiba **AI ugu badalaysaa cod dabiici ah (Neural Voice)** oo ku hadlaya luqadda qofka kale u saaran.

---

## Astaamaha Muhiimka ah (Key Features)

1. **Wicitaan Cod Toos ah (Pure Voice-to-Voice Call)**:
   - Sida WhatsApp ama Telegram Call oo kale, labada qof waxay isku maqlayaan cod toos ah.
   - AI ayaa dhexda ugu jirta oo codka qofka koowaad u beddeleysa codka qofka labaad luqaddiisa.

2. **Taageerada Luqadaha Adduunka (50+ Languages)**:
   - **Af-Soomaali**: Codadka dabiiciga ah ee rasmiga ah: `so-SO-MuuseNeural` (Lab) iyo `so-SO-UbaxNeural` (Dhedig).
   - **Ingiriis (English)**: US, UK, Australia (Jenny, Guy, Ryan, Sonia).
   - **Carabi (Arabic)**: Saudi, Egypt, UAE (Hamed, Zariyah, Shakir, Salma).
   - **Sawaaxili (Swahili)**, **Turki (Turkish)**, **Faransiis (French)**, **Isbaanish (Spanish)**, **Jarmal (German)**, **Talyaani**, **Hindi**, **Shiinees**, iyo kuwo kale.

3. **Xawaare Sare (Ultra-Low Latency Pipeline)**:
   - **Whisper Large-v3** (~200ms) ee fahmidda codka (Speech-to-Text).
   - **Llama 3.3 70B** (~100ms) ee turjumaadda tooska ah.
   - **Edge-TTS Neural Voices** (~300ms) ee codka dabiiciga ah.
   - Isku-dar: ~1.0 ilaa 1.5 ilbiriqsi gudahood ayuu codku ku gaarayaa qofka kale!

4. **Nidaamka Diiwaangelinta & Galitaanka (User Auth)**:
   - Register & Login (SQLite + JWT Tokens).
   - Dookhyada luqadda asalka ah iyo luqadda aad rabto inaad wax ku maqasho.

5. **Muuqaalka Wicitaanka (Call UI)**:
   - Glowing Pulse Avatar oo muujinaya marka la hadlayo ama AI turjumayso.
   - In-Call Language Switcher (waxaad beddeli kartaa luqadaha adigoo wicitaanka ku dhex jira!).
   - Live Subtitles/Captions (muujinaya qoraalka asalka ah iyo kan la turjumay).
   - Badhamada Mute Mic, Deafen Speaker, iyo End Call.

---

## Sida Loo Kiciyo Nidaamka (How to Run)

### 1. Rakib Dependencies-ka:
```bash
pip install -r requirements.txt
```

### 2. Geli API Keys-kaaga (.env):
Koobiyee `.env.example` una bixi `.env`:
```bash
cp .env.example .env
```
Ku dar `GROQ_API_KEY` (ka soo qaado bilaash: [console.groq.com/keys](https://console.groq.com/keys)).

### 3. Kici Server-ka:
```bash
python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Fur Bogga:
Fur Browser-kaaga: `http://localhost:8000`

---

## Sida Loo Tijaabiyo Wicitaanka (Testing the Voice Call)

1. Fur laba tab oo kala duwan (tusaale: Tab caadi ah iyo Tab Incognito ah, ama Chrome iyo Edge):
   - **Tab 1**: Is diiwaangeli (tusaale: `cali`), dooro Speaking Language: **Af-Soomaali**, Listening Language: **Af-Soomaali**.
   - **Tab 2**: Is diiwaangeli (tusaale: `john`), dooro Speaking Language: **English**, Listening Language: **English**.
2. Tab 1: Riix **"Samee Qolka Wicitaanka (Generate Call)"**, koobiyee link-ga ama Room ID-ga.
3. Tab 2: Gal link-ga ama ku qor Room ID-ga sanduuqa **"Ku Biir Wicitaan"**.
4. Labada tab hadda wicitaanka way ku jiraan!
5. Tab 1 ku hadal Af-Soomaali: *"Asc sxb, sideed tahay?"*
   - Tab 2 wuxuu maqlayaa cod Ingiriis ah oo leh: *"Hello friend, how are you?"*
6. Tab 2 ku hadal English: *"I am doing great, thank you!"*
   - Tab 1 wuxuu maqlayaa cod Soomaali ah oo leh: *"Aad baan u fiicanahay, mahadsanid!"*
