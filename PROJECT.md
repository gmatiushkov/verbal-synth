# VerbalSynth — Project Documentation

> Полный контекст для продолжения разработки в новой сессии.

---

## Обзор

**VerbalSynth** — это настольный wavetable-синтезатор, написанный на C++17 с использованием фреймворка JUCE. Это standalone GUI-приложение (не VST-плагин). Ключевая планируемая особенность — генерация звука по текстовому описанию (поле «Describe a sound...» + кнопка Generate), которая пока не реализована.

- **Репозиторий**: `C:\Root\6 - Dev\verbal-synth`
- **JUCE**: `C:\Root\6 - Dev\JUCE` (подключается как subdirectory через CMake)
- **Платформа**: Windows (Visual Studio), C++17
- **Сборка**: CMake 3.22+, target `VerbalSynth`
- **Окно**: 1024 × 760 px, не масштабируется

---

## Структура файлов

```
verbal-synth/
├── CMakeLists.txt          — сборка проекта
├── Source/
│   ├── Main.cpp            — точка входа (JUCEApplication)
│   ├── MainComponent.cpp/h — корневой UI-компонент (AudioAppComponent)
│   ├── SynthEngine.cpp/h   — аудио-движок, 8 голосов
│   ├── SynthVoice.cpp/h    — один полифонический голос
│   ├── SynthParameters.h   — SynthPatch (38 параметров, все float [0..1])
│   ├── WavetableBank.h     — wavetable данные + генерация встроенных банков
│   ├── WavetableOscillator.h — осциллятор с билинейной интерполяцией
│   ├── Oscillator.cpp/h    — старый морфирующий осциллятор (не используется в SynthVoice)
│   ├── NoiseGenerator.h    — белый шум (juce::Random)
│   ├── SynthFilter.cpp/h   — 4-порядковый TPT SVF (LP или HP), mono
│   ├── AdsrEnvelope.cpp/h  — обёртка juce::ADSR с log-маппингом времён
│   ├── LfoGenerator.cpp/h  — LFO, 5 форм волны (sine/tri/saw/rsaw/square)
│   ├── DriveProcessor.h    — tanh soft-clip + tone control (1-pole LP)
│   ├── ReverbEffect.cpp/h  — juce::dsp::Reverb
│   ├── PatchPanel.cpp/h    — главный UI-компонент со всеми ручками
│   ├── PresetManager.h     — менеджер пресетов (JSON ↔ SynthPatch)
│   ├── VerbalLookAndFeel.h — кастомный JUCE LookAndFeel (ноябок, слайдеры, кнопки)
│   ├── UIColors.h          — цветовая палитра (namespace UI, темная схема)
│   ├── WaveDisplay.h       — визуализатор формы волны (+ ghost-слой)
│   ├── AdsrDisplay.h       — превью огибающей ADSR (пропорционально времени)
│   ├── FilterVisualizer.h  — АЧХ LP+HP (20Hz–20kHz, −42..+24 dB, + ghost-слой)
│   └── SynthUtils.h        — namespace SynthUtils (logParam, midiToHz, octaveShift, …)
└── build/                  — CMake build dir (MSVC, не коммитится)
    └── VerbalSynth_artefacts/
        └── Release/Patches/ — JSON-пресеты рядом с .exe
```

---

## Архитектура

### Сигнальная цепочка (на голос)

```
OSC1 (WavetableOscillator) ─┐
OSC2 (WavetableOscillator) ─┼─ Mixer (mix_osc1 / mix_osc2 / mix_noise)
NoiseGenerator ─────────────┘
                              │
                         LP Filter (SynthFilter, 4th order TPT)
                              │
                         HP Filter (SynthFilter, 4th order TPT)
                              │
                         Amp ADSR envelope
                              │
                         Velocity × LFO2 tremolo
                              │
                       → Voice sum buffer
```

После суммирования всех голосов в **SynthEngine**:

```
Voice sum / kNumVoices (нормализация)
    │
DriveProcessor (tanh soft-clip + tone)
    │
ReverbEffect (juce::dsp::Reverb)
    │
Master Volume
    │
→ Audio output
```

### Полифония

- **8 голосов** (`SynthEngine::kNumVoices = 8`), фиксированный массив `std::array<SynthVoice, 8>`
- Voice stealing: round-robin (`mStealIndex`)
- Голос считается активным, пока его `AmpEnvelope.isActive()` == true (пока идёт release)

### Параметры (SynthPatch)

38 нормализованных float [0..1], хранятся как packed struct. Порядок критичен — используется `data()` для итерации.

| # | Имя | Описание |
|---|-----|----------|
| 0 | `osc1_table` | Индекс wavetable банка OSC1 (snap к целому банку) |
| 1 | `osc1_position` | Позиция внутри банка (frame) [0..1] |
| 2 | `osc1_octave` | Сдвиг октавы −2..+2, шаг 0.25 (5 значений) |
| 3 | `osc2_table` | То же для OSC2 |
| 4 | `osc2_position` | То же для OSC2 |
| 5 | `osc2_detune` | Детюн ±50 центов (0.5 = нейтрально) |
| 6 | `osc2_semitones` | Транспозиция ±24 полутона (0.5 = нейтрально) |
| 7 | `mix_osc1` | Уровень OSC1 [0..1] |
| 8 | `mix_osc2` | Уровень OSC2 [0..1] |
| 9 | `mix_noise` | Уровень шума [0..1] |
| 10 | `lp_cutoff` | LP cutoff, log 20–18000 Гц |
| 11 | `lp_resonance` | LP Q, 0→Q0.5, 1→Q10 |
| 12 | `hp_cutoff` | HP cutoff, log 20–18000 Гц |
| 13 | `hp_resonance` | HP Q |
| 14 | `filter_keytrack` | Key tracking обоих фильтров [0..1] |
| 15 | `amp_attack` | A, log 0.5ms–5s |
| 16 | `amp_decay` | D, log 1ms–5s |
| 17 | `amp_sustain` | S [0..1] |
| 18 | `amp_release` | R, log 5ms–10s |
| 19 | `fenv_attack` | Filter env A |
| 20 | `fenv_decay` | Filter env D |
| 21 | `fenv_sustain` | Filter env S |
| 22 | `fenv_release` | Filter env R |
| 23 | `fenv_amount` | Глубина модуляции LP cutoff (0.5=нейтр, 0=−макс, 1=+макс) |
| 24 | `fenv_to_wt` | Filter env → WT position оба OSC |
| 25 | `lfo1_rate` | LFO1 частота, log 0.01–20 Гц |
| 26 | `lfo1_shape` | 0=sine, 0.33=tri, 0.67=saw, 1=square |
| 27 | `lfo1_to_pitch` | LFO1 → pitch (до ±2 полутона) |
| 28 | `lfo1_to_filter` | LFO1 → LP cutoff (до ±2 октавы) |
| 29 | `lfo2_rate` | LFO2 частота |
| 30 | `lfo2_shape` | Форма волны LFO2 |
| 31 | `lfo2_to_wt` | LFO2 → wavetable position оба OSC |
| 32 | `lfo2_to_amp` | LFO2 → амплитуда (тремоло) |
| 33 | `drive_amount` | Глубина насыщения (0=чисто, 1=жёсткий дистошн) |
| 34 | `drive_tone` | Тон (0=тёмный ~1.5kHz, 1=яркий ~15kHz) |
| 35 | `reverb_time` | Время реверберации |
| 36 | `reverb_damp` | Демпфирование |
| 37 | `reverb_mix` | Wet/Dry |

---

## Wavetable-банки

**Формат**: 16 фреймов × 2048 сэмплов, float.  
**Интерполяция**: билинейная по фрейму и по фазе (WavetableOscillator).  
**Генерация**: 4 ключевых кейфрейма (позиции 0/5/10/15), остальные 12 интерполируются.

**Основа синтезатора — 6 кастомных WAV-банков** в папке `Wavetables/` рядом с .exe. Встроенные банки (`WavetableBank::createBuiltIn()`) служат лишь заглушкой на случай отсутствия файлов.

| # | Файл / Название | Описание |
|---|-----------------|----------|
| 1 | Basic | sine → tri → saw → square |
| 2 | Organ | drawbar-орган (нарастание обертонов) |
| 3 | Acoustic | нарастание обертонов; звук струнных — фортепиано, скрипки, виолончели, клавесин, гитара и т. д. |
| 4 | Vocal | гласные У → О → А → Э → И (форманты) |
| 5 | Metallic | металлические и стеклянные тембры (колокольчики, колокола, треугольник и т. д.); смещение WT Pos меняет соотношение обертонов |
| 6 | Digital | квадратная волна со скруглениями → нарастающий цифровой шум; форма волны дробится — для агрессивных диджитал- и чиптюн-звуков |

**Загрузка**: WAV читается как последовательность фреймов по 2048 сэмплов (16 фреймов на банк). Если файлы отсутствуют, движок падает обратно на встроенные процедурные банки.

---

## Модуляция (детали реализации)

### LFO1
- **→ Pitch**: обновляется каждые 16 сэмплов (subsampling для CPU), сдвиг до ±2 полутона
- **→ LP Cutoff**: умножитель `pow(2, lfo1Val * amount * 2)` (до ±2 октавы), per-sample

### LFO2
- **→ WT Position**: `pos + lfo2Val * amount * 0.5`, per-sample, clamped [0..1]
- **→ Amp (tremolo)**: `max(0, 1 + lfo2Val * amount)`, per-sample

### Filter Envelope
- **→ LP Cutoff**: `lpCutHz * pow(2, fenvVal * fenvAmt * 4)` (до ±4 октавы)
- **→ WT Position**: аддитивно, `fenvVal * fenv_to_wt`, per-sample

### Key Tracking
- Оба фильтра: `keyFactor = pow(noteHz / 440, keytrack)`, cutoff смещается пропорционально

---

## Фильтр

`SynthFilter` — 4-й порядок (два последовательных TPT SVF):
- `mFilter`: пользовательский Q (0.5..10), тип LP/BP/HP
- `mFilter2`: фиксированный Q = Butterworth (0.7071), тот же тип
- Метод `processSampleRaw(input, cutoffHz)` используется в per-sample loop голоса — напрямую устанавливает cutoff без SmoothedValue (это быстрее, т.к. cutoff уже меняется per-sample из-за LFO/env)
- Метод `processSample()` использует SmoothedValue (20ms), применяется при статичном cutoff

---

## DriveProcessor

- Экспоненциальная кривая gain: `inputGain = pow(40, drive)` (1x..40x)
- Компенсация уровня: `outputGain = kRef / tanh(kRef * inputGain)`, kRef=0.1
- Tone control: 1-pole LP blend, cutoff 1500..15000 Гц
- Bypass при `drive < 1e-4`

---

## UI Layout

```
┌─────────────────────────────────────────────────────┐
│ Title │ < │ Preset Name * │ > │ Save │  [prompt]  [Generate] │ (50px)
├─────────────────────────────────────────────────────┤
│        PatchPanel                                    │
│  ┌────────┬────────┬───────┬───────────────────┐   │
│  │ OSC 1  │ OSC 2  │ Mixer │      Filter        │   │  Row1 36%
│  └────────┴────────┴───────┴───────────────────┘   │
│  ┌──────────┬────────────────┬────────┬────────┐   │
│  │ Amp ADSR │ Filter Envelope│ LFO 1  │ LFO 2  │   │  Row2 40%
│  └──────────┴────────────────┴────────┴────────┘   │
│  ┌─────────────┬──────────────┬──────────────────┐  │
│  │    Drive    │    Reverb    │    Controls       │  │  Row3 24%
│  └─────────────┴──────────────┴──────────────────┘  │
├─────────────────────────────────────────────────────┤
│              MIDI Keyboard (105px)                   │
└─────────────────────────────────────────────────────┘
```

### Controls group (Row3 right)
- **Velocity Sens** toggle — включает velocity → громкость
- **Show Mod** toggle — показывать/скрывать анимацию модуляции на ручках
- **Key Follow** (param 14) — key tracking фильтров
- **Volume** — master volume (не часть SynthPatch, не сохраняется в пресете)

### OSC-группа
- Waveform display (50px) — текущий фрейм + ghost (LFO2 позиция)
- Горизонтальный слайдер позиции (22px)
- Ручки: Table, Oct(OSC1) или Table, Detune, Semis(OSC2)

### Mixer
- Вертикальные фейдеры: OSC1 / OSC2 / Noise

### ADSR-группы
- ADSR preview (68px)
- Вертикальные фейдеры A, D, S, R
- Filter Envelope дополнительно имеет правую колонку с ручками `to Filter` и `to WT`

### LFO-группы
- 2×2 сетка: Rate + Shape (верх), to Pitch + to Filter (LFO1) или to WT Pos + to Amp (LFO2)
- LED в правом углу заголовка (пульсирует с уровнем LFO, 60 Hz timer)

### Filter-группа
- FilterVisualizer (всё свободное пространство)
- 4 ручки снизу: HP Cut, HP Res, LP Cut, LP Res

---

## Анимация модуляции (LFO-индикаторы)

60 Hz `timerCallback` в PatchPanel:
1. Считывает `getLfo1Level()` / `getLfo2Level()` (atomic из аудио-потока)
2. Устанавливает на слайдерах свойства `mod_level`, `mod_amount`, `mod_scale`
3. VerbalLookAndFeel рисует поверх ручки/слайдера:
   - Дугу (mod range) цветом `MOD_COLOR` (тёмно-зелёный)
   - Точку (живая позиция) цветом `MOD_DOT` (ярко-зелёный)
4. FilterVisualizer — ghost-кривая при активном LFO1→Filter
5. WaveDisplay — ghost-фрейм при активном LFO2→WT

Анимация отключается тоглом «Show Mod» (mod_amount выставляется в 0 для всех слайдеров).

---

## Компьютерная клавиатура (MIDI)

| Клавиша | Нота |
|---------|------|
| A | До (C) |
| W | До# |
| S | Ре |
| E | Ре# |
| D | Ми |
| F | Фа |
| T | Фа# |
| G | Соль |
| Y | Соль# |
| H | Ля |
| U | Ля# |
| J | Си |
| K | До (октава выше) |
| O | До# |
| L | Ре |
| **Z** | Октава вниз |
| **X** | Октава вверх |
| **Space** | Toggle test note (C4) |

Начальная октава: 4. Диапазон: 0–8. Поддерживаются полифонические нажатия.

---

## Система пресетов

**Формат**: JSON, одна запись на параметр по имени из `SynthPatch::paramNames()`.  
**Расположение**: `<app_dir>/Patches/*.json`.  
**Автосоздание**: при запуске создаётся `—— Init ——.json` (дефолтный `SynthPatch{}`).  
**UI**: `<` / `>` навигация, клик на имя → выпадающий список, кнопка Save (Save / Save As).  
**Dirty flag**: `*` после имени пресета при несохранённых изменениях.

Параметры **Volume** и **Velocity Sens** в пресете **не хранятся** — они глобальные контролы.

---

## Сборка

```powershell
# Конфигурация (один раз)
cmake -B build -G "Visual Studio 17 2022" -A x64 .

# Сборка Release
cmake --build build --config Release

# Бинарник:
# build\VerbalSynth_artefacts\Release\VerbalSynth.exe
```

JUCE подключён как `add_subdirectory("C:/Root/6 - Dev/JUCE" JUCE)` — путь хардкодный. При работе на другой машине нужно изменить CMakeLists.txt.

Буфер: 128 сэмплов (задаётся в `MainComponent::MainComponent()` через `deviceManager.setAudioDeviceSetup`).

---

## Нереализованные функции

### Generate (AI patch generation)
В UI есть `mPromptInput` (текстовое поле) и `mGenerateBtn` (кнопка «Generate»), но у кнопки нет callback'а — функциональность не реализована. Планировалось: по текстовому описанию генерировать `SynthPatch` (38 нормализованных float) и применять его к движку.

Для реализации достаточно добавить `mGenerateBtn.onClick = [this]() { ... }` в `MainComponent::MainComponent()`, который:
1. Читает `mPromptInput.getText()`
2. Генерирует `SynthPatch` (через LLM API или локальную логику)
3. Вызывает `mEngine.applyPatch(patch)` и `mPatchPanel.setPatch(patch)`

---

## Цветовая палитра (UIColors.h)

| Константа | Цвет (hex) | Назначение |
|-----------|-----------|------------|
| `BG` | `#080c12` | Фон приложения |
| `PANEL` | `#0d1620` | Фон группы |
| `BORDER` | `#1e3a50` | Рамка группы |
| `BORDER_HI` | `#2e5a78` | Рамка при фокусе |
| `TITLE` | `#60d8c0` | Заголовки групп |
| `LABEL` | `#4a7090` | Подписи параметров |
| `VALUE` | `#d0ecff` | Значения параметров |
| `KNOB_FILL` | `#00907c` | Заполнение ручки/кнопки |
| `KNOB_THUMB` | `#e8b840` | Указатель ручки (золотой) |
| `MOD_COLOR` | `#006850` | Дуга диапазона модуляции |
| `MOD_DOT` | `#20d080` | Точка живой позиции LFO |
| `LED_ON` | `#00e8a0` | LFO LED — максимум |

---

## Известные архитектурные особенности

1. **`processSampleRaw` vs `processSample`**: В per-sample render loop голоса используется `processSampleRaw` (прямое выставление cutoff без SmoothedValue), потому что cutoff меняется каждый сэмпл из-за LFO/env. SmoothedValue в этом контексте не нужен и добавляет лишнюю работу.

2. **Subsampling LFO pitch**: Обновление частоты осциллятора по LFO1 происходит каждые 16 сэмплов (`(i & 15) == 0`). Слуховой артефакт незначителен при типичных LFO-частотах.

3. **Нормализация громкости голосов**: `buffer.applyGain(1.f / kNumVoices)` после суммирования — простой делитель без учёта фактического числа активных голосов.

4. **LFO-форма «rsaw»** (обратная пила): LfoGenerator поддерживает 5 форм. В UI `lfo1_shape`/`lfo2_shape` имеют шаг `1/3` (4 позиции: 0, 0.33, 0.67, 1.0), что даёт sine/tri/saw/square (rsaw недоступна из UI).

5. **Oscillator.h** — старый морфирующий осциллятор (sine/tri/saw/square через `juce::dsp::Oscillator`) существует в кодовой базе, но в `SynthVoice` не используется — заменён `WavetableOscillator`.

6. **`osc1_octave` шаг**: Слайдер имеет step 0.25 (5 дискретных значений: 0, 0.25, 0.5, 0.75, 1.0 → −2, −1, 0, +1, +2 окт).

7. **`lfo_shape` шаг**: Слайдеры 26 и 30 имеют step `1/3` (4 дискретных значения).

8. **Init-пресет**: Имя `—— Init ——` (два em-dash с каждой стороны, UTF-8 `\xe2\x80\x94\xe2\x80\x94`). При сохранении под этим именем PatchPanel обновляет double-click return values всех ручек.
