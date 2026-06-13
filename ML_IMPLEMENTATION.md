# VerbalSynth — ML Text-to-Patch Implementation Plan

> Документ описывает полный план реализации функции генерации патчей синтезатора по текстовому описанию.
> Связанный документ архитектуры проекта: [PROJECT.md](PROJECT.md)

---

## Концепция

Пользователь вводит текст ("звонкий колокольчик с длинным эхо") и нажимает Generate.
Система генерирует `SynthPatch` (38 нормализованных float [0..1]) и применяет его к движку.

**Выбранный подход: Вариант D — обучение на данных от LLM (Гибрид)**

1. Claude API генерирует датасет `(текст, патч)` — используется только при создании датасета
2. Обучается маленькая сеть `MiniLM-L6 + MLP` на этом датасете
3. На продакшене работает только маленькая модель (~23MB) — без интернета, без LLM

> **⚠️ Фаза 1 пересмотрена (v2).** Стратегия и формат генерации датасета описаны в
> [DATASET_PLAN.md](DATASET_PLAN.md). Ключевое отличие: **Claude проектирует патч и описания
> вместе** (а не описывает случайно сгенерированные патчи). Скрипты `generate_patches.py` +
> `generate_texts.py` ниже **устарели** и заменены единым `ml/scripts/generate_dataset.py`.
> Разделы 1.1–1.3 оставлены для истории; смотри DATASET_PLAN.md как источник правды.
> Разделы Фазы 2 (обучение), 3 (интеграция C++), 4 (ONNX) остаются актуальными.

---

## Архитектура системы

```
[Текстовый запрос]
       ↓
  all-MiniLM-L6-v2       ← замороженный, 22MB, CPU ~50ms
  (sentence-transformers)
       ↓
  вектор 384 float
       ↓
  MLP: 384→256→128→64→38  ← обучаемая голова, ~0.6MB
  ReLU + Dropout + Sigmoid
       ↓
  [38 параметров SynthPatch]
       ↓
  SynthEngine::applyPatch()
  PatchPanel::setPatch()
```

**Инференс на Windows dev:** Python subprocess (простота разработки)
**Инференс на RPi (будущее):** ONNX Runtime C++ (нативно, без Python)

---

## Структура файлов проекта

```
verbal-synth/
├── PROJECT.md                  ← архитектура синтезатора
├── ML_IMPLEMENTATION.md        ← этот файл
├── ml/
│   ├── generate_patches.py     ← программная генерация патчей по архетипам
│   ├── generate_texts.py       ← вызов Claude API → текстовые описания
│   ├── train.py                ← обучение MiniLM+MLP на PyTorch
│   ├── predict.py              ← инференс (вызывается из C++ subprocess)
│   ├── export_onnx.py          ← экспорт в ONNX для RPi
│   ├── test_embeddings.py      ← быстрый тест MiniLM
│   ├── patches_raw.json        ← сгенерированные патчи без текстов
│   ├── patches.jsonl           ← финальный датасет (text + params)
│   ├── archetypes/             ← вручную созданные эталонные патчи
│   │   ├── bell.json
│   │   ├── bass.json
│   │   ├── pad.json
│   │   └── ...
│   └── models/
│       ├── synth_predictor.pt  ← обученная модель PyTorch
│       └── synth_predictor.onnx← экспортированная для RPi
└── Source/
    └── MainComponent.cpp       ← интеграция (mGenerateBtn.onClick)
```

---

## Параметры SynthPatch (порядок критичен для вектора)

```python
PARAM_NAMES = [
    "osc1_table",      # 0  — банк wavetable (0=Basic, 0.2=Organ, 0.4=Acoustic,
                       #       0.6=Vocal, 0.8=Metallic, 1.0=Digital)
    "osc1_position",   # 1  — позиция в банке [0..1]
    "osc1_octave",     # 2  — октава −2..+2 (шаг 0.25; 0.5=нейтрально)
    "osc2_table",      # 3
    "osc2_position",   # 4
    "osc2_detune",     # 5  — детюн ±50 центов (0.5=нейтрально)
    "osc2_semitones",  # 6  — транспозиция ±24 полутона (0.5=нейтрально)
    "mix_osc1",        # 7  — уровень OSC1 [0..1]
    "mix_osc2",        # 8  — уровень OSC2 [0..1]
    "mix_noise",       # 9  — уровень шума [0..1]
    "lp_cutoff",       # 10 — LP cutoff, log 20–18000 Гц
    "lp_resonance",    # 11 — LP Q (0→Q0.5, 1→Q10)
    "hp_cutoff",       # 12 — HP cutoff
    "hp_resonance",    # 13 — HP Q
    "filter_keytrack", # 14 — key tracking фильтров [0..1]
    "amp_attack",      # 15 — A, log 0.5ms–5s
    "amp_decay",       # 16 — D, log 1ms–5s
    "amp_sustain",     # 17 — S [0..1]
    "amp_release",     # 18 — R, log 5ms–10s
    "fenv_attack",     # 19 — Filter env A
    "fenv_decay",      # 20 — Filter env D
    "fenv_sustain",    # 21 — Filter env S
    "fenv_release",    # 22 — Filter env R
    "fenv_amount",     # 23 — глубина мод LP cutoff (0.5=нейтр, 0=−макс, 1=+макс)
    "fenv_to_wt",      # 24 — Filter env → WT position
    "lfo1_rate",       # 25 — LFO1 частота, log 0.01–20 Гц
    "lfo1_shape",      # 26 — 0=sine, 0.33=tri, 0.67=saw, 1=square
    "lfo1_to_pitch",   # 27 — LFO1 → pitch (до ±2 полутона)
    "lfo1_to_filter",  # 28 — LFO1 → LP cutoff (до ±2 октавы)
    "lfo2_rate",       # 29 — LFO2 частота
    "lfo2_shape",      # 30 — форма волны LFO2
    "lfo2_to_wt",      # 31 — LFO2 → wavetable position
    "lfo2_to_amp",     # 32 — LFO2 → амплитуда (тремоло)
    "drive_amount",    # 33 — насыщение (0=чисто, 1=жёсткий дистошн)
    "drive_tone",      # 34 — тон (0=тёмный ~1.5kHz, 1=яркий ~15kHz)
    "reverb_time",     # 35 — время реверберации
    "reverb_damp",     # 36 — демпфирование реверба
    "reverb_mix",      # 37 — Wet/Dry реверба
]
```

---

## Фаза 1 — Создание датасета

> **УСТАРЕЛО (v1).** Разделы 1.1–1.3 ниже описывают старый подход (случайная генерация по
> архетипам → описание). Он заменён на v2 (Claude проектирует патч+описания) — см.
> [DATASET_PLAN.md](DATASET_PLAN.md), [ml/config/system_prompt.md](ml/config/system_prompt.md),
> [ml/config/param_reference.json](ml/config/param_reference.json),
> [ml/config/sound_taxonomy.json](ml/config/sound_taxonomy.json). Сохранено для контекста.

### 1.1 generate_patches.py — программная генерация ⚠️ DEPRECATED

```python
import json, random
from pathlib import Path

def rnd(lo, hi): return round(random.uniform(lo, hi), 4)
def mid(lo, hi): return round((lo + hi) / 2, 4)

# Базовый нейтральный патч
def neutral():
    return {k: 0.5 for k in PARAM_NAMES}

# Архетипы — переопределяем только значимые параметры
ARCHETYPES = {
    "pad": {
        "amp_attack":   (0.6, 1.0),   # медленная атака
        "amp_sustain":  (0.7, 1.0),   # высокое сустейн
        "amp_release":  (0.65, 1.0),  # долгий релиз
        "lp_cutoff":    (0.3, 0.6),   # тёплый/приглушённый
        "reverb_time":  (0.6, 1.0),
        "reverb_mix":   (0.4, 0.8),
        "lfo1_to_filter":(0.1, 0.4),  # движение фильтра
        "lfo2_to_wt":   (0.1, 0.35),  # движение тембра
        "mix_noise":    (0.0, 0.08),
    },
    "bass": {
        "osc1_octave":  (0.0, 0.3),   # низко
        "amp_attack":   (0.0, 0.12),  # быстрая атака
        "amp_sustain":  (0.65, 1.0),
        "amp_release":  (0.1, 0.35),
        "lp_cutoff":    (0.25, 0.55), # тёмный
        "reverb_mix":   (0.0, 0.15),  # сухой
        "drive_amount": (0.15, 0.55), # немного дистошна
        "drive_tone":   (0.2, 0.5),
    },
    "bell": {
        "osc1_table":   (0.75, 1.0),  # Metallic или Digital
        "osc1_octave":  (0.5, 1.0),   # высоко
        "amp_attack":   (0.0, 0.08),  # мгновенная атака
        "amp_sustain":  (0.0, 0.2),   # затухает
        "amp_decay":    (0.35, 0.75),
        "amp_release":  (0.5, 0.9),
        "fenv_amount":  (0.6, 0.85),  # яркий атак
        "fenv_decay":   (0.25, 0.5),
        "reverb_time":  (0.6, 1.0),
        "reverb_mix":   (0.3, 0.7),
        "mix_osc2":     (0.0, 0.35),
    },
    "lead": {
        "amp_attack":   (0.0, 0.18),
        "amp_sustain":  (0.5, 0.9),
        "amp_release":  (0.15, 0.4),
        "lp_cutoff":    (0.5, 0.9),   # яркий
        "mix_osc2":     (0.0, 0.4),
        "reverb_mix":   (0.0, 0.25),
        "osc1_octave":  (0.4, 0.75),
    },
    "drone": {
        "amp_attack":   (0.4, 0.85),
        "amp_sustain":  (0.9, 1.0),
        "amp_release":  (0.7, 1.0),
        "lfo1_to_filter":(0.2, 0.6),
        "lfo2_to_wt":   (0.2, 0.5),
        "lfo1_rate":    (0.1, 0.3),   # медленное LFO
        "reverb_mix":   (0.3, 0.7),
    },
    "keys": {
        "osc1_table":   (0.15, 0.45), # Organ или Acoustic
        "amp_attack":   (0.0, 0.08),
        "amp_decay":    (0.3, 0.65),
        "amp_sustain":  (0.2, 0.65),
        "amp_release":  (0.15, 0.45),
        "reverb_mix":   (0.05, 0.3),
    },
    "noise_fx": {
        "mix_noise":    (0.4, 1.0),
        "lp_cutoff":    (0.2, 0.7),
        "drive_amount": (0.2, 0.6),
        "reverb_time":  (0.5, 1.0),
        "reverb_mix":   (0.4, 0.8),
        "lfo1_to_filter":(0.3, 0.8),
    },
    "pluck": {
        "amp_attack":   (0.0, 0.05),
        "amp_decay":    (0.25, 0.55),
        "amp_sustain":  (0.0, 0.15),
        "amp_release":  (0.2, 0.5),
        "fenv_amount":  (0.55, 0.8),
        "fenv_decay":   (0.15, 0.4),
        "reverb_mix":   (0.1, 0.4),
    },
}

def generate_patch(archetype_name):
    params = {k: 0.5 for k in PARAM_NAMES}
    # Нейтральные значения для специфических параметров
    params.update({"osc2_detune": 0.5, "osc2_semitones": 0.5,
                   "mix_osc1": 0.8, "mix_osc2": 0.0, "mix_noise": 0.0,
                   "hp_cutoff": 0.04, "hp_resonance": 0.1,
                   "lfo1_to_pitch": 0.0, "drive_tone": 0.5,
                   "fenv_to_wt": 0.0, "lfo2_to_amp": 0.0})
    # Применяем архетип
    for param, (lo, hi) in ARCHETYPES[archetype_name].items():
        params[param] = rnd(lo, hi)
    # Клампинг [0..1]
    return {k: max(0.0, min(1.0, v)) for k, v in params.items()}

# Генерация: 200 патчей на архетип = ~1600 всего
patches = []
for arch in ARCHETYPES:
    for _ in range(200):
        patches.append({"archetype": arch, "params": generate_patch(arch)})

# Плюс ручные якорные патчи из archetypes/ директории
# (добавить вручную созданные эталонные патчи с archetype метаданными)

Path("ml/patches_raw.json").write_text(
    json.dumps(patches, indent=2, ensure_ascii=False)
)
print(f"Generated {len(patches)} patches")
```

### 1.2 generate_texts.py — генерация описаний через Claude API ⚠️ DEPRECATED

```python
import anthropic, json, time
from pathlib import Path

# Установка: pip install anthropic
# Переменная среды: ANTHROPIC_API_KEY=sk-ant-...

client = anthropic.Anthropic()

PARAM_DESCRIPTIONS_SHORT = """
Wavetable banks (osc_table): 0.0=Basic(sine/saw/square), 0.2=Organ(drawbar harmonics),
0.4=Acoustic(strings,piano,violin), 0.6=Vocal(U-O-A-E-I formants),
0.8=Metallic(bells,triangle,glass), 1.0=Digital(chiptune,glitch)
osc_position: 0=first frame, 1=last frame of wavetable
osc_octave: 0=-2oct, 0.25=-1oct, 0.5=neutral, 0.75=+1oct, 1.0=+2oct
lp_cutoff: 0=dark/muffled(20Hz), 1=bright/open(18kHz)
amp_attack: 0=instant, 1=very slow 5s fade-in
amp_sustain: level held while key pressed
amp_release: 0=immediate cutoff, 1=10s fade-out
reverb_mix: 0=dry, 1=fully wet/spacious
drive_amount: 0=clean, 1=heavy distortion
lfo_to_filter: 0=no movement, 1=intense filter sweep
lfo2_to_wt: 0=static, 1=strong wavetable animation
"""

SYSTEM = f"""You are a synthesizer sound designer. 
Given parameter values, write text descriptions a musician would type to find this sound.
{PARAM_DESCRIPTIONS_SHORT}
Mix languages: include both English and Russian descriptions.
Vary styles: some technical, some emotional/metaphorical, some referencing real instruments or contexts.
"""

def get_descriptions(params: dict, archetype: str, n: int = 7) -> list[str]:
    # Отправляем только значимые (отличающиеся от 0.5) параметры
    significant = {k: round(v, 3) for k, v in params.items()
                   if abs(v - 0.5) > 0.08 or k in
                   ("osc1_table","amp_attack","amp_release","reverb_mix","lp_cutoff")}
    params_str = ", ".join(f"{k}={v}" for k, v in significant.items())

    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=500,
        system=SYSTEM,
        messages=[{"role": "user", "content":
            f"Archetype: {archetype}\nKey params: {params_str}\n\n"
            f"Write {n} different text descriptions. "
            f"Output ONLY a JSON array of strings, nothing else."}]
    )
    raw = msg.content[0].text.strip()
    # Обрезаем до первого [ если есть лишний текст
    if "[" in raw:
        raw = raw[raw.index("["):]
    return json.loads(raw)

def main():
    patches = json.loads(Path("ml/patches_raw.json").read_text())
    output_path = Path("ml/patches.jsonl")

    # Восстановление с точки останова
    already_done = 0
    if output_path.exists():
        already_done = sum(1 for _ in output_path.read_text().splitlines() if _)
        patches_done = already_done // 7  # ~7 описаний на патч
        patches = patches[patches_done:]
        print(f"Resuming from patch {patches_done}/{len(patches)+patches_done}")

    with open(output_path, "a", encoding="utf-8") as f:
        for i, entry in enumerate(patches):
            try:
                texts = get_descriptions(entry["params"], entry["archetype"])
                params_list = [entry["params"][k] for k in PARAM_NAMES]
                for text in texts:
                    line = json.dumps({"text": text, "params": params_list},
                                      ensure_ascii=False)
                    f.write(line + "\n")
                f.flush()

                if i % 20 == 0:
                    total = already_done + (i + 1) * 7
                    print(f"[{i+1}/{len(patches)}] ~{total} examples total")

                time.sleep(0.3)  # rate limiting

            except Exception as e:
                print(f"Error at patch {i}: {e}")
                time.sleep(2)
                continue

if __name__ == "__main__":
    main()
```

### 1.3 Формат датасета (patches.jsonl)

Каждая строка — один обучающий пример:
```json
{"text": "яркий звонкий колокольчик с длинным эхо", "params": [0.8, 0.2, 0.75, ...38 чисел...]}
{"text": "bright metallic bell, very spacious reverb", "params": [0.8, 0.2, 0.75, ...]}
{"text": "crystal chime, long decay", "params": [0.8, 0.2, 0.75, ...]}
```

Целевой объём: ~8000–12000 примеров (1600 патчей × 7 описаний + ручные).

---

## Фаза 2 — Обучение модели

### 2.1 train.py

```python
import torch, json, numpy as np
from torch import nn
from torch.utils.data import Dataset, DataLoader, random_split
from sentence_transformers import SentenceTransformer
from pathlib import Path

PARAM_NAMES = [...]  # полный список из секции выше

# ── Датасет ──────────────────────────────────────────────────
class SynthDataset(Dataset):
    def __init__(self, jsonl_path: str, encoder: SentenceTransformer):
        records = [json.loads(l) for l in Path(jsonl_path).read_text().splitlines() if l]
        texts  = [r["text"] for r in records]
        params = [r["params"] for r in records]

        print(f"Encoding {len(texts)} texts...")
        embeddings = encoder.encode(texts, batch_size=128, show_progress_bar=True,
                                    convert_to_numpy=True)
        self.X = torch.tensor(embeddings, dtype=torch.float32)
        self.Y = torch.tensor(params, dtype=torch.float32)

    def __len__(self): return len(self.Y)
    def __getitem__(self, i): return self.X[i], self.Y[i]

# ── Архитектура ───────────────────────────────────────────────
class SynthPredictor(nn.Module):
    def __init__(self, input_dim=384, hidden=(256, 128, 64), output_dim=38):
        super().__init__()
        layers = []
        prev = input_dim
        for h in hidden:
            layers += [nn.Linear(prev, h), nn.LayerNorm(h), nn.GELU(), nn.Dropout(0.15)]
            prev = h
        layers += [nn.Linear(prev, output_dim), nn.Sigmoid()]
        self.net = nn.Sequential(*layers)

    def forward(self, x):
        return self.net(x)

# ── Обучение ──────────────────────────────────────────────────
def train():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Device: {device}")

    encoder = SentenceTransformer("all-MiniLM-L6-v2")
    encoder.eval()

    dataset = SynthDataset("ml/patches.jsonl", encoder)
    n_val   = max(200, int(0.1 * len(dataset)))
    n_train = len(dataset) - n_val
    train_set, val_set = random_split(dataset, [n_train, n_val])

    train_loader = DataLoader(train_set, batch_size=128, shuffle=True,  num_workers=2)
    val_loader   = DataLoader(val_set,   batch_size=128, shuffle=False, num_workers=2)

    model = SynthPredictor().to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=3e-4, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=80)

    best_val = float("inf")
    for epoch in range(100):
        # Train
        model.train()
        train_loss = 0.0
        for X, Y in train_loader:
            X, Y = X.to(device), Y.to(device)
            loss = nn.HuberLoss(delta=0.1)(model(X), Y)
            optimizer.zero_grad(); loss.backward(); optimizer.step()
            train_loss += loss.item()

        # Validate
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for X, Y in val_loader:
                val_loss += nn.HuberLoss(delta=0.1)(model(X.to(device)), Y.to(device)).item()

        train_loss /= len(train_loader)
        val_loss   /= len(val_loader)
        scheduler.step()

        if val_loss < best_val:
            best_val = val_loss
            torch.save(model.state_dict(), "ml/models/synth_predictor.pt")

        if epoch % 10 == 0:
            print(f"Epoch {epoch:3d}: train={train_loss:.4f}  val={val_loss:.4f}  best={best_val:.4f}")

    print(f"\nDone. Best val loss: {best_val:.4f}")
    print("Model saved to ml/models/synth_predictor.pt")

if __name__ == "__main__":
    train()
```

**Ожидаемые метрики:**
- Huber loss < 0.05 — хорошо (ошибка ~±5% по параметру в среднем)
- Huber loss < 0.03 — отлично
- Время обучения на GTX 1050 Ti: ~20–40 минут при 10K примерах

### 2.2 predict.py — инференс (вызывается из C++)

```python
#!/usr/bin/env python3
"""
Использование: python ml/predict.py "тёплый аналоговый бас"
Выводит JSON с 38 параметрами патча.
"""
import sys, json, torch
from pathlib import Path
from sentence_transformers import SentenceTransformer

# Добавляем ml/ в путь для импорта SynthPredictor
sys.path.insert(0, str(Path(__file__).parent))
from train import SynthPredictor, PARAM_NAMES

# Загрузка один раз при старте (модели кешируются в памяти процесса)
_encoder = None
_model   = None

def load_models():
    global _encoder, _model
    if _encoder is None:
        _encoder = SentenceTransformer("all-MiniLM-L6-v2")
        _model   = SynthPredictor()
        model_path = Path(__file__).parent / "models/synth_predictor.pt"
        _model.load_state_dict(torch.load(model_path, map_location="cpu"))
        _model.eval()

def predict(text: str) -> dict:
    load_models()
    emb = torch.tensor(_encoder.encode([text]))
    with torch.no_grad():
        params = _model(emb)[0].tolist()
    return dict(zip(PARAM_NAMES, params))

if __name__ == "__main__":
    text = " ".join(sys.argv[1:])
    if not text:
        print(json.dumps({"error": "No text provided"}))
        sys.exit(1)
    result = predict(text)
    print(json.dumps(result, ensure_ascii=False))
```

---

## Фаза 3 — Интеграция в C++ (JUCE)

### 3.1 Подключение в MainComponent.cpp

Найти в `MainComponent::MainComponent()` место где настраивается `mGenerateBtn` и добавить:

```cpp
mGenerateBtn.onClick = [this]()
{
    auto prompt = mPromptInput.getText().trim();
    if (prompt.isEmpty())
        return;

    mGenerateBtn.setEnabled(false);
    mGenerateBtn.setButtonText("...");

    // Запускаем Python в фоне (не блокируем UI)
    Thread::launch([this, prompt]()
    {
        juce::ChildProcess proc;
        // Путь к скрипту — рядом с .exe
        auto exeDir = juce::File::getSpecialLocation(
            juce::File::currentExecutableFile).getParentDirectory();
        auto scriptPath = exeDir.getChildFile("../../../../../../ml/predict.py")
                                .getFullPathName();

        juce::String cmd = "python \"" + scriptPath + "\" " + prompt;

        SynthPatch patch;
        bool success = false;

        if (proc.start(cmd))
        {
            auto output = proc.readAllProcessOutput(8000); // 8 сек таймаут
            auto json   = juce::JSON::parse(output);

            if (json.isObject())
            {
                auto* obj = json.getDynamicObject();
                if (obj)
                {
                    auto& props = obj->getProperties();
                    // Заполняем поля SynthPatch по имени
                    float* data = patch.data();
                    const auto& names = SynthPatch::paramNames();
                    for (int i = 0; i < 38; ++i)
                    {
                        auto val = props[names[i]];
                        if (!val.isVoid())
                            data[i] = juce::jlimit(0.f, 1.f, (float)val);
                    }
                    success = true;
                }
            }
        }

        // Применяем на audio thread через MessageManager
        juce::MessageManager::callAsync([this, patch, success]()
        {
            if (success)
            {
                mEngine.applyPatch(patch);
                mPatchPanel.setPatch(patch);
            }
            mGenerateBtn.setEnabled(true);
            mGenerateBtn.setButtonText("Generate");
        });
    });
};
```

### 3.2 Убедиться что в SynthPatch есть paramNames()

В `SynthParameters.h` нужен статический метод:
```cpp
static const std::vector<juce::String>& paramNames()
{
    static std::vector<juce::String> names = {
        "osc1_table", "osc1_position", "osc1_octave",
        "osc2_table", "osc2_position", "osc2_detune", "osc2_semitones",
        "mix_osc1", "mix_osc2", "mix_noise",
        "lp_cutoff", "lp_resonance", "hp_cutoff", "hp_resonance", "filter_keytrack",
        "amp_attack", "amp_decay", "amp_sustain", "amp_release",
        "fenv_attack", "fenv_decay", "fenv_sustain", "fenv_release",
        "fenv_amount", "fenv_to_wt",
        "lfo1_rate", "lfo1_shape", "lfo1_to_pitch", "lfo1_to_filter",
        "lfo2_rate", "lfo2_shape", "lfo2_to_wt", "lfo2_to_amp",
        "drive_amount", "drive_tone",
        "reverb_time", "reverb_damp", "reverb_mix"
    };
    return names;
}
```

---

## Фаза 4 — Экспорт в ONNX (для будущего RPi)

### 4.1 export_onnx.py

```python
import torch
from pathlib import Path
from train import SynthPredictor

model = SynthPredictor()
model.load_state_dict(torch.load("ml/models/synth_predictor.pt", map_location="cpu"))
model.eval()

dummy = torch.randn(1, 384)
torch.onnx.export(
    model, dummy,
    "ml/models/synth_predictor.onnx",
    input_names=["embedding"],
    output_names=["params"],
    dynamic_axes={"embedding": {0: "batch"}, "params": {0: "batch"}},
    opset_version=17
)
print("Exported to ml/models/synth_predictor.onnx")

# Проверка
import onnxruntime as ort
sess = ort.InferenceSession("ml/models/synth_predictor.onnx")
out  = sess.run(None, {"embedding": dummy.numpy()})
print(f"ONNX output shape: {out[0].shape}")  # должно быть (1, 38)
```

Для RPi: `pip install onnxruntime` (ARM-сборка), MiniLM тоже работает через `sentence-transformers` на CPU.

---

## Быстрые тесты перед обучением

### test_embeddings.py

```python
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

model = SentenceTransformer('all-MiniLM-L6-v2')

groups = {
    "bell":  ["яркий колокольчик", "bright metallic bell", "crystal chime sound"],
    "bass":  ["тёплый аналоговый бас", "warm fat bass", "deep low bass"],
    "pad":   ["космический пэд", "spacey ambient pad", "atmospheric slow pad"],
}

all_texts   = [t for g in groups.values() for t in g]
all_labels  = [l for l, g in groups.items() for _ in g]
embeddings  = model.encode(all_texts)
sim         = cosine_similarity(embeddings)

print("Cosine similarities (higher = more similar):")
for i, (t1, l1) in enumerate(zip(all_texts, all_labels)):
    for j, (t2, l2) in enumerate(zip(all_texts, all_labels)):
        if i < j:
            marker = "✓" if l1 == l2 else "✗"
            print(f"  {marker} {sim[i,j]:.3f}  [{l1}] '{t1}' ↔ [{l2}] '{t2}'")
```

**Ожидаемый результат:** внутригрупповые сходства > 0.5, межгрупповые < 0.3.

---

## Зависимости Python

```txt
# ml/requirements.txt
sentence-transformers>=2.7.0
torch>=2.3.0
numpy>=1.26.0
anthropic>=0.28.0
scikit-learn>=1.4.0   # для теста
onnxruntime>=1.18.0   # для экспорта/RPi
```

Установка:
```powershell
pip install -r ml/requirements.txt
```

---

## Пошаговый роадмап

| # | Задача | Статус | Оценка |
|---|--------|--------|--------|
| 1 | Послушать 3 тестовых патча `[TEST]*` в синтезаторе | ✅ создано | 5 мин |
| 2 | Запустить `test_embeddings.py` — проверить MiniLM | ⬜ | 10 мин |
| 3 | Создать директорию `ml/`, файлы скриптов | ⬜ | 30 мин |
| 4 | Написать `generate_dataset.py` (v2: Claude проектирует патч+описания) | ⬜ | — |
| 5 | Вставить ключ aiprimetech, запустить `generate_dataset.py --test` → прослушать → `--all` | ⬜ | API |
| 6 | Запустить `train.py` на GPU | ⬜ | 30-40 мин |
| 7 | Проверить `predict.py` из командной строки | ⬜ | 15 мин |
| 8 | Добавить `mGenerateBtn.onClick` в `MainComponent.cpp` | ⬜ | 1-2 часа |
| 9 | Тест кнопки Generate в запущенном синтезаторе | ⬜ | 30 мин |
| 10 | Расширить датасет, дообучить при нужде | ⬜ | итеративно |
| 11 | Экспорт в ONNX для RPi | ⬜ | 1 час |

---

## Оценка стоимости датасета

> Актуальная оценка — в [DATASET_PLAN.md](DATASET_PLAN.md) § «Оценка стоимости».
> Кратко (v2, claude-opus-4-8, тариф Default 0.7×, ~800 патчей × 6 описаний):
> ~$14 в обычном режиме, ~$7 с Batch API (−50%). Системный промпт кэшируется.
> Бюджет $25 проходит с запасом; можно стартовать с 400 патчей (~$3–4).

---

## Известные ограничения

1. **Python subprocess latency**: первый вызов `predict.py` медленный (~3-5 сек) из-за загрузки моделей. Решение: держать процесс живым или использовать ONNX Runtime нативно в C++.
2. **Качество данных = качество модели**: если Claude генерирует неточные описания, модель это наследует. Контроль: ручная проверка выборки датасета.
3. **Out-of-distribution запросы**: очень необычные описания ("звук одиночества") могут дать случайный результат. Допустимо для v1.
4. **lfo1_shape / osc1_octave дискретные**: модель предскажет непрерывные значения, снаппинг к дискретным значениям происходит в движке — это нормально.
