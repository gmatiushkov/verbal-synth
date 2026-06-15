# Шаг 2 — Чек-лист прослушки кандидат-эталонов

> Сгенерировано `ml/scripts/render_specs.py --taxonomy`. Источник — `taxonomy_to_role.json`.
> Каждый патч `«<префикс>...»` выгружен в Patches. Прослушай, отметь вердикт:
> `[x]` — годен как эталон · `[~]` — почти, нужна правка базы/правил · `[ ]` — мимо (в Шаг 3).
> Колонка «эталон-кандидат» — заводской/golden патч на ту же цель: если он лучше — берём ЕГО.

- Всего целей: **140**.
- С заводским/golden эталоном для сверки: **52**; чисто синтез-кандидат: **88**.

## acoustic_emulation

### `bell`

| ✓ | Цель | Банк | Что слышно (real) | Дропнуто | Эталон-кандидат |
|---|---|---|---|---|---|
| [ ] | челеста | Metallic | position=10% position=30% cutoff=6000 Гц attack=1 мс sustain=0% release=300 мс decay=500 мс | — | [DS]_celesta_classic_bell.json |
| [ ] | колокольчики/глокеншпиль | Metallic | position=10% position=30% cutoff=11000 Гц attack=1 мс sustain=0% release=300 мс decay=500 мс | — | [TEST]_crystal_chime_ethereal.json |
| [ ] | трубчатые колокола | Metallic | position=10% position=30% cutoff=6000 Гц attack=1 мс sustain=75% release=2.50 с decay=400 мс | — | [TEST]_cathedral_long_bell.json |

### `brass`

| ✓ | Цель | Банк | Что слышно (real) | Дропнуто | Эталон-кандидат |
|---|---|---|---|---|---|
| [ ] | труба (открытая/сурдина) | Basic | position=80% position=80% cutoff=6000 Гц attack=12 мс sustain=82% release=250 мс | — | — |
| [ ] | тромбон | Basic | position=80% position=80% cutoff=2500 Гц attack=80 мс sustain=82% release=250 мс | — | — |
| [ ] | стилизованные духовые (туба, валторна) | Basic | position=80% position=80% cutoff=850 Гц attack=80 мс sustain=82% release=250 мс | — | — |

### `choir_pad`

| ✓ | Цель | Банк | Что слышно (real) | Дропнуто | Эталон-кандидат |
|---|---|---|---|---|---|
| [ ] | хор/вокальный ах | Vocal | position=50% position=50% cutoff=2500 Гц attack=120 мс sustain=90% release=800 мс | — | Voices Singing Yao.json |

### `epiano`

| ✓ | Цель | Банк | Что слышно (real) | Дропнуто | Эталон-кандидат |
|---|---|---|---|---|---|
| [ ] | электропиано/родес | Acoustic | position=25% position=25% cutoff=850 Гц attack=4 мс sustain=35% release=400 мс decay=600 мс | — | [VAL]_нежное_электропиано_с_мягкой_атакой.json |
| [ ] | клавинет (фанк) | Acoustic | position=25% position=25% cutoff=6000 Гц attack=4 мс sustain=35% release=400 мс decay=600 мс | attack=instant, body=pluck | — |

### `flute`

| ✓ | Цель | Банк | Что слышно (real) | Дропнуто | Эталон-кандидат |
|---|---|---|---|---|---|
| [ ] | флейта (с придыханием) | Acoustic | position=20% position=30% cutoff=2500 Гц attack=120 мс sustain=82% release=300 мс | attack=medium | [VAL]_флейта_с_придыханием_воздушная.json |
| [ ] | пан-флейта | Acoustic | position=20% position=30% cutoff=850 Гц attack=120 мс sustain=82% release=300 мс | attack=medium | — |

### `guitar`

| ✓ | Цель | Банк | Что слышно (real) | Дропнуто | Эталон-кандидат |
|---|---|---|---|---|---|
| [ ] | классическая гитара (щипок) | Acoustic | position=69% position=88% cutoff=850 Гц attack=12 мс sustain=0% release=300 мс decay=500 мс | — | [TEST]_classical_guitar_nylon_pluck.json |
| [ ] | стальная акустическая гитара | Acoustic | position=69% position=88% cutoff=6000 Гц attack=12 мс sustain=0% release=300 мс decay=500 мс | — | [DIV]_steel_guitar_warm_clean.json |
| [ ] | банджо | Acoustic | position=69% position=88% cutoff=6000 Гц attack=1 мс sustain=0% release=80 мс decay=120 мс | — | — |
| [ ] | мандолина | Acoustic | position=69% position=88% cutoff=6000 Гц attack=12 мс sustain=0% release=300 мс decay=500 мс | — | — |
| [ ] | балалайка/домра | Acoustic | position=69% position=88% cutoff=6000 Гц attack=12 мс sustain=0% release=300 мс decay=500 мс | — | — |
| [ ] | ситар (дрон+щипок) | Acoustic | position=69% position=88% cutoff=6000 Гц attack=12 мс sustain=80% release=450 мс decay=300 мс | — | — |
| [ ] | кото/гучжэн | Acoustic | position=69% position=88% cutoff=2500 Гц attack=12 мс sustain=0% release=300 мс decay=500 мс | — | — |
| [ ] | арфа | Acoustic | position=69% position=88% cutoff=850 Гц attack=12 мс sustain=0% release=300 мс decay=500 мс | — | — |

### `mallet`

| ✓ | Цель | Банк | Что слышно (real) | Дропнуто | Эталон-кандидат |
|---|---|---|---|---|---|
| [ ] | вибрафон | Metallic | position=15% position=30% cutoff=850 Гц attack=1 мс sustain=75% release=2.50 с decay=400 мс | movement=tremolo | — |
| [ ] | маримба/ксилофон | Acoustic | position=15% position=30% cutoff=850 Гц attack=1 мс sustain=0% release=300 мс decay=500 мс | — | — |
| [ ] | калимба (металлические язычки) | Acoustic | position=15% position=30% cutoff=2500 Гц attack=1 мс sustain=0% release=300 мс decay=500 мс | — | — |
| [ ] | стил-пан (карибский) | Metallic | position=15% position=30% cutoff=6000 Гц attack=1 мс sustain=0% release=300 мс decay=500 мс | — | — |
| [ ] | музыкальная шкатулка | Metallic | position=15% position=30% cutoff=6000 Гц attack=1 мс sustain=0% release=300 мс decay=500 мс | movement=tremolo | — |

### `organ`

| ✓ | Цель | Банк | Что слышно (real) | Дропнуто | Эталон-кандидат |
|---|---|---|---|---|---|
| [ ] | церковный орган | Organ | position=45% position=90% cutoff=2500 Гц attack=4 мс sustain=82% release=30 мс decay=20 мс | — | Church Organ.json |
| [ ] | орган Хаммонд с лесли | Organ | position=45% position=90% cutoff=6000 Гц attack=4 мс sustain=82% release=30 мс decay=20 мс | — | Rock Leslie Organ.json |

### `piano`

| ✓ | Цель | Банк | Что слышно (real) | Дропнуто | Эталон-кандидат |
|---|---|---|---|---|---|
| [ ] | фортепиано (мягкий плак) | Acoustic | position=50% position=79% cutoff=850 Гц attack=3 мс sustain=0% release=320 мс decay=2.00 с | — | Piano.json |

### `pluck`

| ✓ | Цель | Банк | Что слышно (real) | Дропнуто | Эталон-кандидат |
|---|---|---|---|---|---|
| [ ] | клавесин | Basic | position=40% position=30% cutoff=6000 Гц attack=2 мс sustain=0% release=300 мс decay=400 мс | attack=instant, body=pluck | — |

### `pure_tone`

| ✓ | Цель | Банк | Что слышно (real) | Дропнуто | Эталон-кандидат |
|---|---|---|---|---|---|
| [ ] | окарина | Basic | position=0% position=30% cutoff=850 Гц attack=80 мс sustain=85% release=250 мс | — | — |
| [ ] | свист | Basic | position=0% position=30% cutoff=6000 Гц attack=80 мс sustain=85% release=250 мс | — | — |
| [ ] | терменвокс-подобный непрерывный тон | Basic | position=0% position=30% cutoff=2500 Гц attack=400 мс sustain=85% release=250 мс | — | — |

### `reed`

| ✓ | Цель | Банк | Что слышно (real) | Дропнуто | Эталон-кандидат |
|---|---|---|---|---|---|
| [ ] | кларнет (полый, нечётные обертоны) | Basic | position=90% position=30% cutoff=850 Гц attack=12 мс sustain=80% release=450 мс decay=300 мс | — | — |
| [ ] | гобой/двойная трость (носовой) | Basic | position=90% position=30% cutoff=6000 Гц attack=12 мс sustain=80% release=450 мс decay=300 мс | — | — |
| [ ] | фагот (низкий двойной язычок) | Basic | position=90% position=30% cutoff=850 Гц attack=80 мс sustain=80% release=450 мс decay=300 мс | — | — |
| [ ] | саксофон (язычковый) | Basic | position=90% position=30% cutoff=6000 Гц attack=12 мс sustain=80% release=200 мс | — | — |
| [ ] | губная гармоника | Basic | position=90% position=30% cutoff=6000 Гц attack=12 мс sustain=80% release=200 мс | — | — |
| [ ] | аккордеон/баян | Basic | position=90% position=30% cutoff=2500 Гц attack=12 мс sustain=80% release=450 мс decay=300 мс | — | — |
| [ ] | фисгармония (reed organ) | Basic | position=90% position=30% cutoff=850 Гц attack=80 мс sustain=80% release=450 мс decay=300 мс | — | [DS]_physharmonia_bright_voicing.json |
| [ ] | волынка (дрон+мелодия) | Basic | position=90% position=30% cutoff=6000 Гц attack=12 мс sustain=100% release=4.00 с decay=500 мс | — | — |
| [ ] | колёсная лира/шарманка (дрон) | Basic | position=90% position=30% cutoff=2500 Гц attack=40 мс sustain=100% release=4.00 с decay=500 мс | — | — |

### `string`

| ✓ | Цель | Банк | Что слышно (real) | Дропнуто | Эталон-кандидат |
|---|---|---|---|---|---|
| [ ] | виолончель (смычок, вибрато) | Acoustic | position=78% position=66% cutoff=850 Гц attack=80 мс sustain=81% release=350 мс | — | Cello.json |
| [ ] | скрипка (вибрато, яркая) | Acoustic | position=78% position=66% cutoff=6000 Гц attack=80 мс sustain=81% release=350 мс | — | Violin.json |
| [ ] | контрабас (пиццикато и смычок) | Acoustic | position=78% position=66% cutoff=400 Гц attack=80 мс sustain=81% release=350 мс | — | [DS]_contrabass_arco_warm.json |

### `tom`

| ✓ | Цель | Банк | Что слышно (real) | Дропнуто | Эталон-кандидат |
|---|---|---|---|---|---|
| [ ] | литавры (настроенный барабан) | Basic | position=20% position=30% cutoff=400 Гц attack=1 мс sustain=0% release=300 мс decay=500 мс | — | — |

## synth_roles

### `acid_bass`

| ✓ | Цель | Банк | Что слышно (real) | Дропнуто | Эталон-кандидат |
|---|---|---|---|---|---|
| [ ] | acid-бас (резонанс+огибающая) | Basic | position=68% position=30% cutoff=6000 Гц attack=1 мс sustain=0% release=6 мс decay=830 мс | — | Dirty Acid 303 Bass.json |

### `bell`

| ✓ | Цель | Банк | Что слышно (real) | Дропнуто | Эталон-кандидат |
|---|---|---|---|---|---|
| [ ] | FM-белл-лид | Metallic | position=10% position=30% cutoff=6000 Гц attack=1 мс sustain=80% release=450 мс decay=300 мс | — | — |

### `brass`

| ✓ | Цель | Банк | Что слышно (real) | Дропнуто | Эталон-кандидат |
|---|---|---|---|---|---|
| [ ] | брасс-синт (sync/saw) | Basic | position=80% position=80% cutoff=6000 Гц attack=12 мс sustain=82% release=250 мс | — | — |

### `choir_pad`

| ✓ | Цель | Банк | Что слышно (real) | Дропнуто | Эталон-кандидат |
|---|---|---|---|---|---|
| [ ] | формантный/токбокс-лид (гласные) | Vocal | position=75% position=75% cutoff=2500 Гц attack=120 мс sustain=90% release=800 мс | body=sustained | [TEST]_vowel_breath_evolution.json |
| [ ] | хоровой пэд | Vocal | position=25% position=25% cutoff=2500 Гц attack=120 мс sustain=90% release=800 мс | — | Voices Singing Yao.json |

### `epiano`

| ✓ | Цель | Банк | Что слышно (real) | Дропнуто | Эталон-кандидат |
|---|---|---|---|---|---|
| [ ] | электроклавишные/keys | Acoustic | position=25% position=25% cutoff=2500 Гц attack=4 мс sustain=35% release=400 мс decay=600 мс | — | — |
| [ ] | lo-fi/винтаж keys | Acoustic | position=25% position=25% cutoff=850 Гц attack=4 мс sustain=35% release=400 мс decay=600 мс | — | — |

### `glass_pad`

| ✓ | Цель | Банк | Что слышно (real) | Дропнуто | Эталон-кандидат |
|---|---|---|---|---|---|
| [ ] | стеклянный/кристаллический пэд | Metallic | position=20% position=20% cutoff=6000 Гц attack=500 мс sustain=80% release=2.50 с | — | [TEST]_crystalline_breath_pad.json |

### `mallet`

| ✓ | Цель | Банк | Что слышно (real) | Дропнуто | Эталон-кандидат |
|---|---|---|---|---|---|
| [ ] | мэллет-синт (мягкий перкуссивный) | Acoustic | position=15% position=30% cutoff=850 Гц attack=1 мс sustain=0% release=300 мс decay=500 мс | — | — |

### `organ`

| ✓ | Цель | Банк | Что слышно (real) | Дропнуто | Эталон-кандидат |
|---|---|---|---|---|---|
| [ ] | хаус-органный бас | Organ | position=45% position=90% cutoff=6000 Гц attack=4 мс sustain=82% release=30 мс decay=20 мс | body=staccato | — |
| [ ] | рейв-стэб/орган-хаус-стэб | Organ | position=45% position=90% cutoff=6000 Гц attack=4 мс sustain=82% release=30 мс decay=20 мс | body=staccato | — |

### `pluck`

| ✓ | Цель | Банк | Что слышно (real) | Дропнуто | Эталон-кандидат |
|---|---|---|---|---|---|
| [ ] | pluck-бас | Basic | position=40% position=30% cutoff=850 Гц attack=2 мс sustain=0% release=300 мс decay=400 мс | attack=instant, body=pluck | [TEST]_acoustic_pluck_bass.json |
| [ ] | плак (короткий, перкуссивный) | Basic | position=40% position=30% cutoff=6000 Гц attack=2 мс sustain=0% release=300 мс decay=400 мс | attack=instant, body=pluck | [VAL]_короткий_сухой_деревянный_плак.json |
| [ ] | стакато-стэб/хит-чорд | Basic | position=40% position=30% cutoff=6000 Гц attack=2 мс sustain=0% release=300 мс decay=400 мс | attack=instant, body=staccato | — |
| [ ] | арп-звук | Basic | position=40% position=30% cutoff=6000 Гц attack=2 мс sustain=0% release=300 мс decay=400 мс | attack=fast, body=pluck | [DIV]_melodic_vibrato_pluck.json |

### `pure_tone`

| ✓ | Цель | Банк | Что слышно (real) | Дропнуто | Эталон-кандидат |
|---|---|---|---|---|---|
| [ ] | мягкий флейтовый лид | Basic | position=0% position=30% cutoff=850 Гц attack=400 мс sustain=85% release=250 мс | — | — |

### `reese_bass`

| ✓ | Цель | Банк | Что слышно (real) | Дропнуто | Эталон-кандидат |
|---|---|---|---|---|---|
| [ ] | reese-бас (детюн, грязный) | Basic | position=75% position=74% cutoff=2500 Гц attack=7 мс sustain=88% release=80 мс | — | Reese Bass.json |
| [ ] | wobble/dubstep-бас (LFO→фильтр) | Basic | position=75% position=74% cutoff=2500 Гц attack=7 мс sustain=88% release=80 мс | — | — |
| [ ] | growl/neuro-бас | Basic | position=75% position=74% cutoff=6000 Гц attack=7 мс sustain=88% release=80 мс | — | — |
| [ ] | fm-бас | Basic | position=75% position=74% cutoff=6000 Гц attack=7 мс sustain=88% release=80 мс | — | — |

### `saw_bass`

| ✓ | Цель | Банк | Что слышно (real) | Дропнуто | Эталон-кандидат |
|---|---|---|---|---|---|
| [ ] | пилообразный синт-бас (аналоговый) | Basic | position=85% position=30% cutoff=2500 Гц attack=12 мс sustain=75% release=200 мс | — | — |

### `saw_lead`

| ✓ | Цель | Банк | Что слышно (real) | Дропнуто | Эталон-кандидат |
|---|---|---|---|---|---|
| [ ] | supersaw-лид | Basic | position=95% position=95% cutoff=6000 Гц attack=10 мс sustain=80% release=250 мс | thickness=unison_thick | [VAL]_острый_резкий_пилообразный_лид_для_транс.json |
| [ ] | пронзительный соло-лид | Basic | position=95% position=95% cutoff=11000 Гц attack=10 мс sustain=80% release=250 мс | — | — |
| [ ] | синк-лид (hard sync) | Basic | position=95% position=95% cutoff=11000 Гц attack=10 мс sustain=80% release=250 мс | filter_motion=gentle_sweep | — |
| [ ] | hoover-лид (рейв) | Basic | position=95% position=95% cutoff=6000 Гц attack=10 мс sustain=80% release=250 мс | — | — |
| [ ] | хардстайл/транс-лид | Basic | position=95% position=95% cutoff=11000 Гц attack=10 мс sustain=80% release=250 мс | — | — |

### `square_lead`

| ✓ | Цель | Банк | Что слышно (real) | Дропнуто | Эталон-кандидат |
|---|---|---|---|---|---|
| [ ] | PWM/квадратный лид | Basic | position=100% position=30% cutoff=6000 Гц attack=10 мс sustain=78% release=200 мс | — | — |
| [ ] | чиптюн-лид | Basic | position=100% position=30% cutoff=6000 Гц attack=10 мс sustain=78% release=200 мс | — | — |

### `string`

| ✓ | Цель | Банк | Что слышно (real) | Дропнуто | Эталон-кандидат |
|---|---|---|---|---|---|
| [ ] | струнный пэд (ensemble) | Acoustic | position=78% position=66% cutoff=850 Гц attack=400 мс sustain=81% release=350 мс | body=long, thickness=unison_thick | — |

### `sub_bass`

| ✓ | Цель | Банк | Что слышно (real) | Дропнуто | Эталон-кандидат |
|---|---|---|---|---|---|
| [ ] | суббас (чистый син) | Basic | position=0% position=30% cutoff=400 Гц attack=4 мс sustain=80% release=450 мс decay=300 мс | — | [TEST]_pure_sub_sine.json |
| [ ] | 808-саб (длинный сабовый тон) | Basic | position=0% position=30% cutoff=850 Гц attack=4 мс sustain=75% release=2.50 с decay=400 мс | — | [DIV]_classic_808_warm_subkick.json |

### `warm_pad`

| ✓ | Цель | Банк | Что слышно (real) | Дропнуто | Эталон-кандидат |
|---|---|---|---|---|---|
| [ ] | тёплый аналоговый пэд | Basic | position=35% position=35% cutoff=850 Гц attack=400 мс sustain=85% release=2.20 с | body=long | Slow Ambient Pad.json |
| [ ] | пэд эволюционирующий (движение тембра) | Basic | position=35% position=35% cutoff=2500 Гц attack=1.50 с sustain=85% release=2.20 с | body=drone | [VAL]_стеклянный_пэд_с_медленным_движением_тем.json |
| [ ] | транс-гейт пэд (ритмичный гейт) | Basic | position=35% position=35% cutoff=6000 Гц attack=600 мс sustain=85% release=2.20 с | body=sustained | — |

## texture_atmos

### `choir_pad`

| ✓ | Цель | Банк | Что слышно (real) | Дропнуто | Эталон-кандидат |
|---|---|---|---|---|---|
| [ ] | ангельский хоровой шиммер-дрон | Vocal | position=50% position=50% cutoff=6000 Гц attack=120 мс sustain=90% release=800 мс | — | [DIV]_monastic_chant_resonance.json |
| [ ] | формантная вокальная текстура (движение гласных) | Vocal | position=0% position=0% cutoff=2500 Гц attack=120 мс sustain=90% release=800 мс | — | [TEST]_vowel_breath_evolution.json |

### `drone`

| ✓ | Цель | Банк | Что слышно (real) | Дропнуто | Эталон-кандидат |
|---|---|---|---|---|---|
| [ ] | бесконечный дрон (низкий) | Basic | position=40% position=40% cutoff=400 Гц attack=1.20 с sustain=100% release=4.00 с | attack=swell, body=drone | [TEST]_abyssal_infinite_drone.json |
| [ ] | металлический резонансный дрон | Basic | position=40% position=40% cutoff=2500 Гц attack=1.20 с sustain=100% release=4.00 с | body=drone | [DIV]_subterranean_metal_resonator.json |
| [ ] | диссонансный хоррор-дрон | Basic | position=40% position=40% cutoff=400 Гц attack=1.20 с sustain=100% release=4.00 с | body=drone, thickness=unison_thick | [VAL]_тревожный_диссонансный_хоррор_дрон.json |
| [ ] | космическая текстура | Basic | position=40% position=40% cutoff=2500 Гц attack=1.20 с sustain=100% release=4.00 с | body=drone | [TEST]_void_cosmic_dust.json |
| [ ] | индустриальный гул | Basic | position=40% position=40% cutoff=400 Гц attack=1.20 с sustain=100% release=4.00 с | body=drone | [DIV]_abandoned_jet_engine_drone.json |
| [ ] | мрачный подвальный гул | Basic | position=40% position=40% cutoff=400 Гц attack=1.20 с sustain=100% release=4.00 с | body=drone | [DIV]_transformer_hum_low_drone.json |

### `glass_pad`

| ✓ | Цель | Банк | Что слышно (real) | Дропнуто | Эталон-кандидат |
|---|---|---|---|---|---|
| [ ] | ледяной/арктический эмбиент | Metallic | position=20% position=20% cutoff=6000 Гц attack=500 мс sustain=80% release=2.50 с | body=drone | — |
| [ ] | стеклянный шиммер | Metallic | position=20% position=20% cutoff=11000 Гц attack=500 мс sustain=80% release=2.50 с | — | [TEST]_shimmering_ether_pad.json |
| [ ] | реверс-шиммер свелл | Metallic | position=20% position=20% cutoff=6000 Гц attack=500 мс sustain=80% release=2.50 с | attack=swell | — |

### `noise_texture`

| ✓ | Цель | Банк | Что слышно (real) | Дропнуто | Эталон-кандидат |
|---|---|---|---|---|---|
| [ ] | шёпот/придыхание | Basic | position=30% position=30% cutoff=2500 Гц attack=400 мс sustain=90% release=2.50 с | body=drone | [DS]_cold_vault_breath.json |
| [ ] | гранулярная текстура | Basic | position=30% position=30% cutoff=2500 Гц attack=800 мс sustain=90% release=2.50 с | body=drone | — |
| [ ] | ветер/шумовой бриз | Basic | position=30% position=30% cutoff=2500 Гц attack=1.50 с sustain=90% release=2.50 с | body=drone | — |
| [ ] | океан/волны (шум прибоя) | Basic | position=30% position=30% cutoff=850 Гц attack=1.50 с sustain=90% release=2.50 с | body=drone | — |
| [ ] | дождь/гроза | Basic | position=30% position=30% cutoff=2500 Гц attack=800 мс sustain=90% release=2.50 с | body=drone | — |
| [ ] | подводная текстура | Basic | position=30% position=30% cutoff=400 Гц attack=800 мс sustain=90% release=2.50 с | body=drone | — |
| [ ] | винил/лента-крэкл (lo-fi нойз) | Basic | position=30% position=30% cutoff=850 Гц attack=800 мс sustain=90% release=2.50 с | body=drone | — |
| [ ] | радиопомехи/статика | Basic | position=30% position=30% cutoff=6000 Гц attack=800 мс sustain=90% release=2.50 с | body=drone | — |
| [ ] | рой насекомых/живой органик | Basic | position=30% position=30% cutoff=6000 Гц attack=800 мс sustain=90% release=2.50 с | body=drone | — |

### `warm_pad`

| ✓ | Цель | Банк | Что слышно (real) | Дропнуто | Эталон-кандидат |
|---|---|---|---|---|---|
| [ ] | светлый воздушный амбиент-пэд | Basic | position=35% position=35% cutoff=6000 Гц attack=1.50 с sustain=85% release=2.20 с | body=drone | — |
| [ ] | сновидческая дымка | Basic | position=35% position=35% cutoff=850 Гц attack=1.50 с sustain=85% release=2.20 с | body=drone | — |
| [ ] | пульсирующая ритмичная текстура (гейт/чоппер) | Basic | position=35% position=35% cutoff=2500 Гц attack=600 мс sustain=85% release=2.20 с | body=drone | — |
| [ ] | медленно открывающийся пэд-наплыв | Basic | position=35% position=35% cutoff=850 Гц attack=1.50 с sustain=85% release=2.20 с | body=drone | [VAL]_космический_эмбиент_пэд_медленно_дышит.json |

## percussive_fx

### `bell`

| ✓ | Цель | Банк | Что слышно (real) | Дропнуто | Эталон-кандидат |
|---|---|---|---|---|---|
| [ ] | колокол (длинный затухающий) | Metallic | position=10% position=30% cutoff=6000 Гц attack=1 мс sustain=75% release=2.50 с decay=400 мс | — | [TEST]_long_bell_meditative.json |
| [ ] | карильон/курантовый удар | Metallic | position=10% position=30% cutoff=6000 Гц attack=1 мс sustain=75% release=2.50 с decay=400 мс | — | [DIV]_crystal_bell_chime.json |
| [ ] | треугольник | Metallic | position=10% position=30% cutoff=11000 Гц attack=1 мс sustain=75% release=2.50 с decay=400 мс | — | [TEST]_triangle_metal_ping.json |
| [ ] | колокольчик-стик (короткий) | Metallic | position=10% position=30% cutoff=6000 Гц attack=1 мс sustain=0% release=300 мс decay=500 мс | — | [DIV]_crystal_bell_chime.json |
| [ ] | хрустальный звон | Metallic | position=10% position=30% cutoff=11000 Гц attack=1 мс sustain=75% release=2.50 с decay=400 мс | — | [TEST]_crystal_chime_ethereal.json |
| [ ] | стеклянная капля воды | Metallic | position=10% position=30% cutoff=6000 Гц attack=1 мс sustain=0% release=300 мс decay=500 мс | attack=instant | — |

### `digital_fx`

| ✓ | Цель | Банк | Что слышно (real) | Дропнуто | Эталон-кандидат |
|---|---|---|---|---|---|
| [ ] | цифровой бит-краш стэб | Digital | position=0% position=30% cutoff=6000 Гц attack=1 мс sustain=0% release=80 мс decay=120 мс | — | — |
| [ ] | глитч/артефакт | Digital | position=0% position=30% cutoff=6000 Гц attack=1 мс sustain=0% release=80 мс decay=120 мс | — | [DS]_digital_chip_riser.json |
| [ ] | DTMF/телефонные тоны | Digital | position=0% position=30% cutoff=2500 Гц attack=1 мс sustain=80% release=450 мс decay=300 мс | — | — |
| [ ] | спарк/электроразряд | Digital | position=0% position=30% cutoff=11000 Гц attack=1 мс sustain=0% release=80 мс decay=120 мс | — | — |
| [ ] | UI/boot-звук интерфейса | Digital | position=0% position=30% cutoff=6000 Гц attack=12 мс sustain=0% release=300 мс decay=500 мс | — | — |
| [ ] | ретро-аркадный sfx | Digital | position=0% position=30% cutoff=6000 Гц attack=1 мс sustain=0% release=300 мс decay=500 мс | — | — |
| [ ] | лазер/sci-fi свип (фильтр-свип / LFO) | Digital | position=0% position=30% cutoff=11000 Гц attack=1 мс sustain=0% release=80 мс decay=120 мс | — | — |

### `gong`

| ✓ | Цель | Банк | Что слышно (real) | Дропнуто | Эталон-кандидат |
|---|---|---|---|---|---|
| [ ] | храмовый гонг | Metallic | position=70% position=30% cutoff=2500 Гц attack=1 мс sustain=75% release=2.50 с decay=400 мс | — | [TEST]_temple_gong_ceremonial.json |
| [ ] | поющая чаша (singing bowl) | Metallic | position=70% position=30% cutoff=850 Гц attack=1 мс sustain=75% release=2.50 с decay=400 мс | — | [DIV]_slow_ritual_drone_gong.json |
| [ ] | металлический удар/анвил | Metallic | position=70% position=30% cutoff=6000 Гц attack=1 мс sustain=0% release=300 мс decay=500 мс | — | — |
| [ ] | удар/импакт (тёмный) | Metallic | position=70% position=30% cutoff=400 Гц attack=1 мс sustain=75% release=2.50 с decay=400 мс | attack=instant | — |

### `kick`

| ✓ | Цель | Банк | Что слышно (real) | Дропнуто | Эталон-кандидат |
|---|---|---|---|---|---|
| [ ] | саб-дроп импакт | Basic | position=0% position=30% cutoff=400 Гц attack=1 мс sustain=0% release=100 мс decay=250 мс | attack=instant, body=long | [DIV]_sub_drop_kick.json |

### `mallet`

| ✓ | Цель | Банк | Что слышно (real) | Дропнуто | Эталон-кандидат |
|---|---|---|---|---|---|
| [ ] | каменный/металлический клац | Metallic | position=15% position=30% cutoff=6000 Гц attack=1 мс sustain=0% release=80 мс decay=120 мс | attack=instant | — |
| [ ] | клаве/деревянный клик | Acoustic | position=15% position=30% cutoff=6000 Гц attack=1 мс sustain=0% release=80 мс decay=120 мс | attack=instant | — |

### `noise_texture`

| ✓ | Цель | Банк | Что слышно (real) | Дропнуто | Эталон-кандидат |
|---|---|---|---|---|---|
| [ ] | whoosh/transition | Basic | position=30% position=30% cutoff=2500 Гц attack=1.50 с sustain=90% release=2.50 с | — | — |

### `riser_fx`

| ✓ | Цель | Банк | Что слышно (real) | Дропнуто | Эталон-кандидат |
|---|---|---|---|---|---|
| [ ] | взлёт/ризер (медленный подъём) | Digital | position=10% position=30% cutoff=6000 Гц attack=1.50 с sustain=90% release=300 мс | attack=swell | [DS]_digital_chip_riser.json |
| [ ] | downlifter (нисходящий свип) | Digital | position=10% position=30% cutoff=2500 Гц attack=1.50 с sustain=90% release=300 мс | — | — |

### `warm_pad`

| ✓ | Цель | Банк | Что слышно (real) | Дропнуто | Эталон-кандидат |
|---|---|---|---|---|---|
| [ ] | перевёрнутый/реверс-наплыв (имитация long attack) | Basic | position=35% position=35% cutoff=2500 Гц attack=1.50 с sustain=85% release=2.20 с | body=pluck | — |

## drums

### `cymbal`

| ✓ | Цель | Банк | Что слышно (real) | Дропнуто | Эталон-кандидат |
|---|---|---|---|---|---|
| [ ] | крэш/райд (металл+нойз) | Metallic | position=90% position=30% cutoff=11000 Гц attack=1 мс sustain=75% release=2.50 с decay=400 мс | attack=instant | — |

### `hihat`

| ✓ | Цель | Банк | Что слышно (real) | Дропнуто | Эталон-кандидат |
|---|---|---|---|---|---|
| [ ] | хай-хэт закрытый (короткий) | Metallic | position=90% position=30% cutoff=11000 Гц attack=1 мс sustain=0% release=80 мс decay=120 мс | attack=instant, texture=noisy | — |
| [ ] | хай-хэт открытый | Metallic | position=90% position=30% cutoff=11000 Гц attack=1 мс sustain=0% release=300 мс decay=500 мс | attack=instant, texture=noisy | [DS]_breathing_evolution_open_hat.json |
| [ ] | шейкер/маракас (нойз) | Metallic | position=90% position=30% cutoff=6000 Гц attack=1 мс sustain=0% release=80 мс decay=120 мс | attack=fast, texture=noisy | — |
| [ ] | тамбурин | Metallic | position=90% position=30% cutoff=6000 Гц attack=1 мс sustain=0% release=300 мс decay=500 мс | attack=instant, texture=noisy | — |

### `kick`

| ✓ | Цель | Банк | Что слышно (real) | Дропнуто | Эталон-кандидат |
|---|---|---|---|---|---|
| [ ] | синт-кик (808, сабовый синус) | Basic | position=0% position=30% cutoff=400 Гц attack=1 мс sustain=0% release=100 мс decay=250 мс | attack=instant, body=pluck | [DIV]_classic_808_warm_subkick.json |
| [ ] | синт-кик (909, жёсткий) | Basic | position=0% position=30% cutoff=850 Гц attack=1 мс sustain=0% release=100 мс decay=250 мс | attack=instant, body=staccato | [DIV]_dirty_909_aggressive_kick.json |

### `mallet`

| ✓ | Цель | Банк | Что слышно (real) | Дропнуто | Эталон-кандидат |
|---|---|---|---|---|---|
| [ ] | каубел (металлический) | Metallic | position=15% position=30% cutoff=6000 Гц attack=1 мс sustain=0% release=80 мс decay=120 мс | attack=instant | — |

### `snare_clap`

| ✓ | Цель | Банк | Что слышно (real) | Дропнуто | Эталон-кандидат |
|---|---|---|---|---|---|
| [ ] | снэр (нойз+тон) | Basic | position=30% position=30% cutoff=6000 Гц attack=1 мс sustain=0% release=150 мс decay=200 мс | attack=instant, body=staccato | — |
| [ ] | клэп | Basic | position=30% position=30% cutoff=6000 Гц attack=1 мс sustain=0% release=150 мс decay=200 мс | attack=instant, body=staccato | — |
| [ ] | рим-шот/клик | Basic | position=30% position=30% cutoff=6000 Гц attack=1 мс sustain=0% release=150 мс decay=200 мс | attack=instant, body=staccato | — |
| [ ] | пальцевый щелчок/snap | Basic | position=30% position=30% cutoff=6000 Гц attack=1 мс sustain=0% release=150 мс decay=200 мс | attack=instant, body=staccato | — |

### `tom`

| ✓ | Цель | Банк | Что слышно (real) | Дропнуто | Эталон-кандидат |
|---|---|---|---|---|---|
| [ ] | том (настроенный, питч-дроп) | Basic | position=20% position=30% cutoff=850 Гц attack=1 мс sustain=0% release=300 мс decay=500 мс | attack=instant | — |
| [ ] | конга/бонго (тон-перкуссия) | Basic | position=20% position=30% cutoff=850 Гц attack=1 мс sustain=0% release=300 мс decay=500 мс | attack=instant | — |
