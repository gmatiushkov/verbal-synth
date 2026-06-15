# Шаг 1a — Аудит покрытия (таксономия × роли)

> Сгенерировано `ml/scripts/audit_coverage.py` из `config/v5/taxonomy_to_role.json`.
> Источник истины — JSON; этот файл перегенерируется. См. `DATASET_v5_PLAN.md` §7 Шаг 1a.

## Сводка

- Целей покрыто: **140** (все цели `sound_taxonomy.json`).
- Ролей задействовано: **31** (существующих 31, новых 8).
- Целей с готовым эталоном/кандидатом: **52**; без референса (ТЗ на догенерацию): **88**.

### Доли категорий: маппинг vs план таксономии

| Категория | Целей в маппинге | Доля факт. | Доля план |
|---|---|---|---|
| acoustic_emulation | 44 | 31% | 0.28 |
| synth_roles | 34 | 24% | 0.26 |
| texture_atmos | 24 | 17% | 0.18 |
| percussive_fx | 24 | 17% | 0.16 |
| drums | 14 | 10% | 0.12 |

## Новые роли к заведению (ТЗ для roles.json)

| Роль | Банк | Целей покрывает | Эталон/калибровка | Обоснование |
|---|---|---|---|---|
| `guitar` | Acoustic | 8 | Guitar.json, Overdrive Short Guitar.json, [TEST]_classical_guitar_nylon_pluck.json, [DIV]_steel_guitar_warm_clean.json | Щипковая струна с ладами (нейлон/сталь/банджо/мандолина/балалайка/кото/арфа/клавесин). Отдельно от pluck: устойчивая идентичность (быстрая атака + спад + sustain≈0 + лёгкий детюн = двойная струна). |
| `reed` | Basic | 9 | [DS]_physharmonia_bright_voicing.json | Язычковые: одинарная трость (кларнет — полые нечётные обертоны), двойная (гобой/фагот носовой), свободный язычок (гармошка/аккордеон/фисгармония), волынка (дрон). Basic яркая позиция (нечётные обертоны) + лёгкое придыхание. |
| `pure_tone` | Basic | 4 | — | Чистый синус/треугольник без обертонов: свист, терменвокс, окарина, мягкий флейтовый лид. Часто с вибрато. Basic pos 0 (синус). |
| `noise_texture` | Basic | 10 | [DS]_cold_vault_breath.json | Шум-доминантные атмосферы: ветер/океан/дождь/статика/винил-крэкл/придыхание/гранула/whoosh. mix_noise высок, тон-осц подмешан слабо. |
| `gong` | Metallic | 4 | [TEST]_temple_gong_ceremonial.json, [DIV]_grand_gong_resonant.json, [DS]_classic_temple_gong.json | Инармоничный удар по металлу, длинное затухание: храмовый гонг, поющая чаша, анвил. Metallic высокая позиция (резкий/инармоничный), sustain=0, длинный хвост. |
| `digital_fx` | Digital | 7 | [DS]_digital_chip_riser.json | Цифровые/чиптюн/глитч/UI/лазер/бит-краш. Банк Digital (ИНВЕРСИЯ позиции: 0%=жёстче), gritty/distorted, короткие или со свипом. |
| `tom` | Basic | 3 | — | Настроенная мембрана/тональная перкуссия: том, литавры, конга/бонго. Basic низ-средний, мгновенная атака, спад, sustain=0. (Питч-дроп недостижим — аппроксимируем спадом.) |
| `cymbal` | Metallic | 1 | [DS]_breathing_evolution_open_hat.json | Тарелки крэш/райд: металл+шум, длиннее хай-хэта. Metallic высокая позиция + высокий mix_noise, очень высокий регистр, длинный хвост. |

## Цели на роль (параметрический архетип → инструменты)

-    **`bell`** (10): челеста; колокольчики/глокеншпиль; трубчатые колокола; FM-белл-лид; колокол (длинный затухающий); карильон/курантовый удар; треугольник; колокольчик-стик (короткий); хрустальный звон; стеклянная капля воды
- 🆕 **`noise_texture`** (10): шёпот/придыхание; гранулярная текстура; ветер/шумовой бриз; океан/волны (шум прибоя); дождь/гроза; подводная текстура; винил/лента-крэкл (lo-fi нойз); радиопомехи/статика; рой насекомых/живой органик; whoosh/transition
-    **`mallet`** (9): вибрафон; маримба/ксилофон; калимба (металлические язычки); стил-пан (карибский); музыкальная шкатулка; мэллет-синт (мягкий перкуссивный); каменный/металлический клац; клаве/деревянный клик; каубел (металлический)
- 🆕 **`reed`** (9): кларнет (полый, нечётные обертоны); гобой/двойная трость (носовой); фагот (низкий двойной язычок); саксофон (язычковый); губная гармоника; аккордеон/баян; фисгармония (reed organ); волынка (дрон+мелодия); колёсная лира/шарманка (дрон)
- 🆕 **`guitar`** (8): классическая гитара (щипок); стальная акустическая гитара; банджо; мандолина; балалайка/домра; ситар (дрон+щипок); кото/гучжэн; арфа
-    **`warm_pad`** (8): тёплый аналоговый пэд; пэд эволюционирующий (движение тембра); транс-гейт пэд (ритмичный гейт); светлый воздушный амбиент-пэд; сновидческая дымка; пульсирующая ритмичная текстура (гейт/чоппер); медленно открывающийся пэд-наплыв; перевёрнутый/реверс-наплыв (имитация long attack)
- 🆕 **`digital_fx`** (7): цифровой бит-краш стэб; глитч/артефакт; DTMF/телефонные тоны; спарк/электроразряд; UI/boot-звук интерфейса; ретро-аркадный sfx; лазер/sci-fi свип (фильтр-свип / LFO)
-    **`drone`** (6): бесконечный дрон (низкий); металлический резонансный дрон; диссонансный хоррор-дрон; космическая текстура; индустриальный гул; мрачный подвальный гул
-    **`choir_pad`** (5): хор/вокальный ах; формантный/токбокс-лид (гласные); хоровой пэд; ангельский хоровой шиммер-дрон; формантная вокальная текстура (движение гласных)
-    **`pluck`** (5): клавесин; pluck-бас; плак (короткий, перкуссивный); стакато-стэб/хит-чорд; арп-звук
-    **`saw_lead`** (5): supersaw-лид; пронзительный соло-лид; синк-лид (hard sync); hoover-лид (рейв); хардстайл/транс-лид
-    **`brass`** (4): труба (открытая/сурдина); тромбон; стилизованные духовые (туба, валторна); брасс-синт (sync/saw)
-    **`epiano`** (4): электропиано/родес; клавинет (фанк); электроклавишные/keys; lo-fi/винтаж keys
-    **`glass_pad`** (4): стеклянный/кристаллический пэд; ледяной/арктический эмбиент; стеклянный шиммер; реверс-шиммер свелл
- 🆕 **`gong`** (4): храмовый гонг; поющая чаша (singing bowl); металлический удар/анвил; удар/импакт (тёмный)
-    **`hihat`** (4): хай-хэт закрытый (короткий); хай-хэт открытый; шейкер/маракас (нойз); тамбурин
-    **`organ`** (4): церковный орган; орган Хаммонд с лесли; хаус-органный бас; рейв-стэб/орган-хаус-стэб
- 🆕 **`pure_tone`** (4): окарина; свист; терменвокс-подобный непрерывный тон; мягкий флейтовый лид
-    **`reese_bass`** (4): reese-бас (детюн, грязный); wobble/dubstep-бас (LFO→фильтр); growl/neuro-бас; fm-бас
-    **`snare_clap`** (4): снэр (нойз+тон); клэп; рим-шот/клик; пальцевый щелчок/snap
-    **`string`** (4): виолончель (смычок, вибрато); скрипка (вибрато, яркая); контрабас (пиццикато и смычок); струнный пэд (ensemble)
-    **`kick`** (3): саб-дроп импакт; синт-кик (808, сабовый синус); синт-кик (909, жёсткий)
- 🆕 **`tom`** (3): литавры (настроенный барабан); том (настроенный, питч-дроп); конга/бонго (тон-перкуссия)
-    **`flute`** (2): флейта (с придыханием); пан-флейта
-    **`riser_fx`** (2): взлёт/ризер (медленный подъём); downlifter (нисходящий свип)
-    **`square_lead`** (2): PWM/квадратный лид; чиптюн-лид
-    **`sub_bass`** (2): суббас (чистый син); 808-саб (длинный сабовый тон)
-    **`acid_bass`** (1): acid-бас (резонанс+огибающая)
- 🆕 **`cymbal`** (1): крэш/райд (металл+нойз)
-    **`piano`** (1): фортепиано (мягкий плак)
-    **`saw_bass`** (1): пилообразный синт-бас (аналоговый)

## ТЗ на реф-патчи: цели без референса (для Шага 2)

Сгруппировано по роли. Эти цели нужно догенерить Claude'ом и утвердить вручную (либо подобрать из существующих [TEST]/[DIV]/[DS]/[VAL]).

- **`mallet`** (9): вибрафон; маримба/ксилофон; калимба (металлические язычки); стил-пан (карибский); музыкальная шкатулка; мэллет-синт (мягкий перкуссивный); каменный/металлический клац; клаве/деревянный клик; каубел (металлический)
- **`noise_texture`** (9): гранулярная текстура; ветер/шумовой бриз; океан/волны (шум прибоя); дождь/гроза; подводная текстура; винил/лента-крэкл (lo-fi нойз); радиопомехи/статика; рой насекомых/живой органик; whoosh/transition
- **`reed`** (8): кларнет (полый, нечётные обертоны); гобой/двойная трость (носовой); фагот (низкий двойной язычок); саксофон (язычковый); губная гармоника; аккордеон/баян; волынка (дрон+мелодия); колёсная лира/шарманка (дрон)
- **`digital_fx`** (6): цифровой бит-краш стэб; DTMF/телефонные тоны; спарк/электроразряд; UI/boot-звук интерфейса; ретро-аркадный sfx; лазер/sci-fi свип (фильтр-свип / LFO)
- **`guitar`** (6): банджо; мандолина; балалайка/домра; ситар (дрон+щипок); кото/гучжэн; арфа
- **`warm_pad`** (5): транс-гейт пэд (ритмичный гейт); светлый воздушный амбиент-пэд; сновидческая дымка; пульсирующая ритмичная текстура (гейт/чоппер); перевёрнутый/реверс-наплыв (имитация long attack)
- **`brass`** (4): труба (открытая/сурдина); тромбон; стилизованные духовые (туба, валторна); брасс-синт (sync/saw)
- **`pure_tone`** (4): окарина; свист; терменвокс-подобный непрерывный тон; мягкий флейтовый лид
- **`saw_lead`** (4): пронзительный соло-лид; синк-лид (hard sync); hoover-лид (рейв); хардстайл/транс-лид
- **`snare_clap`** (4): снэр (нойз+тон); клэп; рим-шот/клик; пальцевый щелчок/snap
- **`epiano`** (3): клавинет (фанк); электроклавишные/keys; lo-fi/винтаж keys
- **`hihat`** (3): хай-хэт закрытый (короткий); шейкер/маракас (нойз); тамбурин
- **`reese_bass`** (3): wobble/dubstep-бас (LFO→фильтр); growl/neuro-бас; fm-бас
- **`tom`** (3): литавры (настроенный барабан); том (настроенный, питч-дроп); конга/бонго (тон-перкуссия)
- **`bell`** (2): FM-белл-лид; стеклянная капля воды
- **`glass_pad`** (2): ледяной/арктический эмбиент; реверс-шиммер свелл
- **`gong`** (2): металлический удар/анвил; удар/импакт (тёмный)
- **`organ`** (2): хаус-органный бас; рейв-стэб/орган-хаус-стэб
- **`pluck`** (2): клавесин; стакато-стэб/хит-чорд
- **`square_lead`** (2): PWM/квадратный лид; чиптюн-лид
- **`cymbal`** (1): крэш/райд (металл+нойз)
- **`flute`** (1): пан-флейта
- **`riser_fx`** (1): downlifter (нисходящий свип)
- **`saw_bass`** (1): пилообразный синт-бас (аналоговый)
- **`string`** (1): струнный пэд (ensemble)

## Полная таблица маппинга

| Категория | Цель | Роль | 🆕 | Пресет осей | Референс |
|---|---|---|---|---|---|
| acoustic_emulation | классическая гитара (щипок) | `guitar` | 🆕 | register=mid, brightness=warm, attack=fast, body=pluck, space=room | [TEST]_classical_guitar_nylon_pluck.json |
| acoustic_emulation | стальная акустическая гитара | `guitar` | 🆕 | register=mid, brightness=bright, attack=fast, body=pluck, texture=clean | [DIV]_steel_guitar_warm_clean.json |
| acoustic_emulation | банджо | `guitar` | 🆕 | register=high, brightness=bright, attack=instant, body=staccato | none |
| acoustic_emulation | мандолина | `guitar` | 🆕 | register=high, brightness=bright, attack=fast, body=pluck, movement=tremolo | none |
| acoustic_emulation | балалайка/домра | `guitar` | 🆕 | register=mid, brightness=bright, attack=fast, body=pluck | none |
| acoustic_emulation | ситар (дрон+щипок) | `guitar` | 🆕 | register=mid, brightness=bright, attack=fast, body=sustained, texture=gritty | none |
| acoustic_emulation | кото/гучжэн | `guitar` | 🆕 | register=mid, brightness=neutral, attack=fast, body=pluck, space=hall | none |
| acoustic_emulation | арфа | `guitar` | 🆕 | register=mid, brightness=warm, attack=fast, body=pluck, space=hall | none |
| acoustic_emulation | виолончель (смычок, вибрато) | `string` |  | register=low, brightness=warm, attack=medium, movement=vibrato, space=hall | Cello.json |
| acoustic_emulation | скрипка (вибрато, яркая) | `string` |  | register=high, brightness=bright, attack=medium, movement=vibrato, space=hall | Violin.json |
| acoustic_emulation | контрабас (пиццикато и смычок) | `string` |  | register=sub, brightness=dark, attack=medium, space=room | [DS]_contrabass_arco_warm.json |
| acoustic_emulation | флейта (с придыханием) | `flute` |  | register=high, brightness=neutral, attack=medium, texture=noisy, movement=vibrato | [VAL]_флейта_с_придыханием_воздушная.json |
| acoustic_emulation | пан-флейта | `flute` |  | register=high, brightness=warm, attack=medium, texture=noisy | none |
| acoustic_emulation | окарина | `pure_tone` | 🆕 | register=high, brightness=warm, attack=medium, movement=vibrato | none |
| acoustic_emulation | кларнет (полый, нечётные обертоны) | `reed` | 🆕 | register=mid, brightness=warm, attack=fast, body=sustained | none |
| acoustic_emulation | гобой/двойная трость (носовой) | `reed` | 🆕 | register=mid, brightness=bright, attack=fast, body=sustained | none |
| acoustic_emulation | фагот (низкий двойной язычок) | `reed` | 🆕 | register=low, brightness=warm, attack=medium, body=sustained | none |
| acoustic_emulation | саксофон (язычковый) | `reed` | 🆕 | register=mid, brightness=bright, attack=fast, texture=noisy, movement=vibrato | none |
| acoustic_emulation | труба (открытая/сурдина) | `brass` |  | register=high, brightness=bright, attack=fast, filter_motion=gentle_sweep | none |
| acoustic_emulation | тромбон | `brass` |  | register=low, brightness=neutral, attack=medium | none |
| acoustic_emulation | стилизованные духовые (туба, валторна) | `brass` |  | register=low, brightness=warm, attack=medium, space=hall | none |
| acoustic_emulation | губная гармоника | `reed` | 🆕 | register=mid, brightness=bright, attack=fast, texture=noisy | none |
| acoustic_emulation | аккордеон/баян | `reed` | 🆕 | register=mid, brightness=neutral, attack=fast, thickness=unison_thick, body=sustained | none |
| acoustic_emulation | фисгармония (reed organ) | `reed` | 🆕 | register=mid, brightness=warm, attack=medium, body=sustained | [DS]_physharmonia_bright_voicing.json |
| acoustic_emulation | церковный орган | `organ` |  | register=low, brightness=neutral, movement=static, space=hall | Church Organ.json |
| acoustic_emulation | орган Хаммонд с лесли | `organ` |  | register=mid, brightness=bright, movement=leslie, texture=gritty, space=room | Rock Leslie Organ.json |
| acoustic_emulation | фортепиано (мягкий плак) | `piano` |  | register=mid, brightness=warm, texture=clean, space=room | Piano.json |
| acoustic_emulation | электропиано/родес | `epiano` |  | register=mid, brightness=warm, texture=saturated, movement=tremolo | [VAL]_нежное_электропиано_с_мягкой_атакой.json |
| acoustic_emulation | клавинет (фанк) | `epiano` |  | register=mid, brightness=bright, attack=instant, body=pluck, texture=gritty | none |
| acoustic_emulation | клавесин | `pluck` |  | register=mid, brightness=bright, attack=instant, body=pluck | none |
| acoustic_emulation | челеста | `bell` |  | register=high, brightness=bright, body=pluck, space=hall | [DS]_celesta_classic_bell.json |
| acoustic_emulation | колокольчики/глокеншпиль | `bell` |  | register=very_high, brightness=piercing, body=pluck, space=hall | [TEST]_crystal_chime_ethereal.json |
| acoustic_emulation | вибрафон | `mallet` |  | register=mid, brightness=warm, body=long, movement=tremolo, space=hall | none |
| acoustic_emulation | маримба/ксилофон | `mallet` |  | register=mid, brightness=warm, body=pluck, texture=clean | none |
| acoustic_emulation | калимба (металлические язычки) | `mallet` |  | register=high, brightness=neutral, body=pluck | none |
| acoustic_emulation | стил-пан (карибский) | `mallet` |  | register=mid, brightness=bright, body=pluck, space=room | none |
| acoustic_emulation | трубчатые колокола | `bell` |  | register=mid, brightness=bright, body=long, space=hall | [TEST]_cathedral_long_bell.json |
| acoustic_emulation | литавры (настроенный барабан) | `tom` | 🆕 | register=low, brightness=dark, body=pluck, texture=saturated | none |
| acoustic_emulation | музыкальная шкатулка | `mallet` |  | register=very_high, brightness=bright, body=pluck, movement=tremolo, space=hall | none |
| acoustic_emulation | волынка (дрон+мелодия) | `reed` | 🆕 | register=mid, brightness=bright, attack=fast, body=drone, thickness=unison_thick | none |
| acoustic_emulation | колёсная лира/шарманка (дрон) | `reed` | 🆕 | register=mid, brightness=neutral, body=drone, texture=gritty | none |
| acoustic_emulation | хор/вокальный ах | `choir_pad` |  | register=mid, brightness=neutral, vowel=a_open, space=hall | Voices Singing Yao.json |
| acoustic_emulation | свист | `pure_tone` | 🆕 | register=high, brightness=bright, attack=medium, movement=vibrato | none |
| acoustic_emulation | терменвокс-подобный непрерывный тон | `pure_tone` | 🆕 | register=high, brightness=neutral, attack=soft, movement=vibrato, space=hall | none |
| synth_roles | суббас (чистый син) | `sub_bass` |  | register=sub, brightness=dark, body=sustained, texture=clean | [TEST]_pure_sub_sine.json |
| synth_roles | 808-саб (длинный сабовый тон) | `sub_bass` |  | register=sub, brightness=warm, body=long, texture=saturated | [DIV]_classic_808_warm_subkick.json |
| synth_roles | reese-бас (детюн, грязный) | `reese_bass` |  | register=low, brightness=neutral, texture=gritty, movement=filter_wobble | Reese Bass.json |
| synth_roles | acid-бас (резонанс+огибающая) | `acid_bass` |  | register=low, brightness=bright, filter_motion=pluck_wah, texture=gritty | Dirty Acid 303 Bass.json |
| synth_roles | пилообразный синт-бас (аналоговый) | `saw_bass` |  | register=low, brightness=neutral, attack=fast, texture=saturated, space=dry | none |
| synth_roles | wobble/dubstep-бас (LFO→фильтр) | `reese_bass` |  | register=low, brightness=neutral, movement=filter_wobble, texture=distorted | none |
| synth_roles | growl/neuro-бас | `reese_bass` |  | register=low, brightness=bright, movement=filter_wobble, texture=distorted, character=aggressive | none |
| synth_roles | pluck-бас | `pluck` |  | register=low, brightness=warm, attack=instant, body=pluck | [TEST]_acoustic_pluck_bass.json |
| synth_roles | fm-бас | `reese_bass` |  | register=low, brightness=bright, texture=gritty | none |
| synth_roles | хаус-органный бас | `organ` |  | register=low, brightness=bright, body=staccato, space=room | none |
| synth_roles | supersaw-лид | `saw_lead` |  | register=mid, brightness=bright, thickness=unison_thick, space=hall | [VAL]_острый_резкий_пилообразный_лид_для_транс.json |
| synth_roles | пронзительный соло-лид | `saw_lead` |  | register=high, brightness=piercing, movement=vibrato | none |
| synth_roles | PWM/квадратный лид | `square_lead` |  | register=mid, brightness=bright, movement=vibrato | none |
| synth_roles | синк-лид (hard sync) | `saw_lead` |  | register=high, brightness=piercing, filter_motion=gentle_sweep, character=aggressive | none |
| synth_roles | hoover-лид (рейв) | `saw_lead` |  | register=mid, brightness=bright, movement=vibrato, texture=gritty | none |
| synth_roles | хардстайл/транс-лид | `saw_lead` |  | register=high, brightness=piercing, texture=distorted | none |
| synth_roles | мягкий флейтовый лид | `pure_tone` | 🆕 | register=high, brightness=warm, attack=soft, movement=vibrato | none |
| synth_roles | чиптюн-лид | `square_lead` |  | register=high, brightness=bright, movement=vibrato | none |
| synth_roles | формантный/токбокс-лид (гласные) | `choir_pad` |  | register=mid, brightness=neutral, vowel=e_mid, body=sustained, movement=wt_morph | [TEST]_vowel_breath_evolution.json |
| synth_roles | FM-белл-лид | `bell` |  | register=high, brightness=bright, body=sustained, space=hall | none |
| synth_roles | тёплый аналоговый пэд | `warm_pad` |  | register=mid, brightness=warm, attack=soft, body=long, space=hall | Slow Ambient Pad.json |
| synth_roles | стеклянный/кристаллический пэд | `glass_pad` |  | register=high, brightness=bright, movement=wt_morph, space=vast | [TEST]_crystalline_breath_pad.json |
| synth_roles | струнный пэд (ensemble) | `string` |  | register=mid, brightness=warm, attack=soft, body=long, thickness=unison_thick, space=hall | none |
| synth_roles | хоровой пэд | `choir_pad` |  | register=mid, brightness=neutral, vowel=o_round, space=hall | Voices Singing Yao.json |
| synth_roles | пэд эволюционирующий (движение тембра) | `warm_pad` |  | register=mid, brightness=neutral, attack=swell, body=drone, movement=wt_morph, space=vast | [VAL]_стеклянный_пэд_с_медленным_движением_тем.json |
| synth_roles | транс-гейт пэд (ритмичный гейт) | `warm_pad` |  | register=mid, brightness=bright, body=sustained, movement=tremolo, space=hall | none |
| synth_roles | плак (короткий, перкуссивный) | `pluck` |  | register=mid, brightness=bright, attack=instant, body=pluck, space=room | [VAL]_короткий_сухой_деревянный_плак.json |
| synth_roles | стакато-стэб/хит-чорд | `pluck` |  | register=mid, brightness=bright, attack=instant, body=staccato | none |
| synth_roles | рейв-стэб/орган-хаус-стэб | `organ` |  | register=mid, brightness=bright, body=staccato, texture=gritty | none |
| synth_roles | мэллет-синт (мягкий перкуссивный) | `mallet` |  | register=mid, brightness=warm, body=pluck, space=room | none |
| synth_roles | электроклавишные/keys | `epiano` |  | register=mid, brightness=neutral, texture=clean, space=room | none |
| synth_roles | lo-fi/винтаж keys | `epiano` |  | register=mid, brightness=warm, texture=noisy, character=melancholic | none |
| synth_roles | арп-звук | `pluck` |  | register=mid, brightness=bright, attack=fast, body=pluck, space=room | [DIV]_melodic_vibrato_pluck.json |
| synth_roles | брасс-синт (sync/saw) | `brass` |  | register=mid, brightness=bright, attack=fast, filter_motion=gentle_sweep | none |
| texture_atmos | бесконечный дрон (низкий) | `drone` |  | register=low, brightness=dark, attack=swell, body=drone, space=vast | [TEST]_abyssal_infinite_drone.json |
| texture_atmos | металлический резонансный дрон | `drone` |  | register=low, brightness=neutral, body=drone, texture=gritty, space=vast | [DIV]_subterranean_metal_resonator.json |
| texture_atmos | диссонансный хоррор-дрон | `drone` |  | register=low, brightness=dark, body=drone, thickness=unison_thick, character=anxious, space=vast | [VAL]_тревожный_диссонансный_хоррор_дрон.json |
| texture_atmos | светлый воздушный амбиент-пэд | `warm_pad` |  | register=high, brightness=bright, attack=swell, body=drone, space=vast | none |
| texture_atmos | ангельский хоровой шиммер-дрон | `choir_pad` |  | register=high, brightness=bright, vowel=a_open, movement=wt_morph, space=vast | [DIV]_monastic_chant_resonance.json |
| texture_atmos | космическая текстура | `drone` |  | register=mid, brightness=neutral, body=drone, movement=wt_morph, space=vast | [TEST]_void_cosmic_dust.json |
| texture_atmos | ледяной/арктический эмбиент | `glass_pad` |  | register=high, brightness=bright, body=drone, character=cold_metallic, space=vast | none |
| texture_atmos | сновидческая дымка | `warm_pad` |  | register=mid, brightness=warm, attack=swell, body=drone, character=dreamy, space=vast | none |
| texture_atmos | формантная вокальная текстура (движение гласных) | `choir_pad` |  | register=mid, brightness=neutral, vowel=u_dark, movement=wt_morph, space=hall | [TEST]_vowel_breath_evolution.json |
| texture_atmos | шёпот/придыхание | `noise_texture` | 🆕 | register=mid, brightness=neutral, attack=soft, body=drone, space=hall | [DS]_cold_vault_breath.json |
| texture_atmos | стеклянный шиммер | `glass_pad` |  | register=high, brightness=piercing, movement=wt_morph, space=vast | [TEST]_shimmering_ether_pad.json |
| texture_atmos | реверс-шиммер свелл | `glass_pad` |  | register=high, brightness=bright, attack=swell, movement=wt_morph, space=vast | none |
| texture_atmos | гранулярная текстура | `noise_texture` | 🆕 | register=mid, brightness=neutral, body=drone, movement=wt_morph, space=hall | none |
| texture_atmos | ветер/шумовой бриз | `noise_texture` | 🆕 | register=mid, brightness=neutral, attack=swell, body=drone, space=vast | none |
| texture_atmos | океан/волны (шум прибоя) | `noise_texture` | 🆕 | register=low, brightness=warm, attack=swell, body=drone, movement=tremolo, space=vast | none |
| texture_atmos | дождь/гроза | `noise_texture` | 🆕 | register=mid, brightness=neutral, body=drone, space=hall | none |
| texture_atmos | подводная текстура | `noise_texture` | 🆕 | register=low, brightness=dark, body=drone, movement=filter_wobble, space=vast | none |
| texture_atmos | индустриальный гул | `drone` |  | register=low, brightness=dark, body=drone, texture=distorted, space=hall | [DIV]_abandoned_jet_engine_drone.json |
| texture_atmos | мрачный подвальный гул | `drone` |  | register=sub, brightness=dark, body=drone, character=anxious, space=vast | [DIV]_transformer_hum_low_drone.json |
| texture_atmos | винил/лента-крэкл (lo-fi нойз) | `noise_texture` | 🆕 | register=high, brightness=warm, body=drone, texture=noisy | none |
| texture_atmos | радиопомехи/статика | `noise_texture` | 🆕 | register=high, brightness=bright, body=drone, texture=noisy | none |
| texture_atmos | рой насекомых/живой органик | `noise_texture` | 🆕 | register=high, brightness=bright, body=drone, movement=tremolo, texture=noisy | none |
| texture_atmos | пульсирующая ритмичная текстура (гейт/чоппер) | `warm_pad` |  | register=mid, brightness=neutral, body=drone, movement=tremolo, space=hall | none |
| texture_atmos | медленно открывающийся пэд-наплыв | `warm_pad` |  | register=mid, brightness=warm, attack=swell, body=drone, space=vast | [VAL]_космический_эмбиент_пэд_медленно_дышит.json |
| percussive_fx | колокол (длинный затухающий) | `bell` |  | register=mid, brightness=bright, body=long, space=hall | [TEST]_long_bell_meditative.json |
| percussive_fx | храмовый гонг | `gong` | 🆕 | register=low, brightness=neutral, body=long, space=hall | [TEST]_temple_gong_ceremonial.json |
| percussive_fx | поющая чаша (singing bowl) | `gong` | 🆕 | register=mid, brightness=warm, body=long, movement=tremolo, space=hall | [DIV]_slow_ritual_drone_gong.json |
| percussive_fx | карильон/курантовый удар | `bell` |  | register=high, brightness=bright, body=long, space=hall | [DIV]_crystal_bell_chime.json |
| percussive_fx | треугольник | `bell` |  | register=very_high, brightness=piercing, body=long, space=room | [TEST]_triangle_metal_ping.json |
| percussive_fx | колокольчик-стик (короткий) | `bell` |  | register=very_high, brightness=bright, body=pluck, space=room | [DIV]_crystal_bell_chime.json |
| percussive_fx | хрустальный звон | `bell` |  | register=very_high, brightness=piercing, body=long, space=hall | [TEST]_crystal_chime_ethereal.json |
| percussive_fx | металлический удар/анвил | `gong` | 🆕 | register=mid, brightness=bright, body=pluck, texture=gritty | none |
| percussive_fx | каменный/металлический клац | `mallet` |  | register=mid, brightness=bright, attack=instant, body=staccato, texture=gritty | none |
| percussive_fx | стеклянная капля воды | `bell` |  | register=very_high, brightness=bright, attack=instant, body=pluck, space=room | none |
| percussive_fx | цифровой бит-краш стэб | `digital_fx` | 🆕 | register=mid, brightness=bright, attack=instant, body=staccato, texture=distorted | none |
| percussive_fx | глитч/артефакт | `digital_fx` | 🆕 | register=high, brightness=bright, attack=instant, body=staccato, texture=distorted | [DS]_digital_chip_riser.json |
| percussive_fx | DTMF/телефонные тоны | `digital_fx` | 🆕 | register=mid, brightness=neutral, body=sustained, texture=clean | none |
| percussive_fx | спарк/электроразряд | `digital_fx` | 🆕 | register=high, brightness=piercing, attack=instant, body=staccato, texture=noisy | none |
| percussive_fx | UI/boot-звук интерфейса | `digital_fx` | 🆕 | register=high, brightness=bright, attack=fast, body=pluck, texture=clean | none |
| percussive_fx | ретро-аркадный sfx | `digital_fx` | 🆕 | register=high, brightness=bright, attack=instant, body=pluck | none |
| percussive_fx | лазер/sci-fi свип (фильтр-свип / LFO) | `digital_fx` | 🆕 | register=high, brightness=piercing, filter_motion=strong_sweep, body=staccato | none |
| percussive_fx | взлёт/ризер (медленный подъём) | `riser_fx` |  | register=high, brightness=bright, attack=swell, filter_motion=strong_sweep, space=hall | [DS]_digital_chip_riser.json |
| percussive_fx | downlifter (нисходящий свип) | `riser_fx` |  | register=mid, brightness=neutral, filter_motion=strong_sweep, space=hall | none |
| percussive_fx | whoosh/transition | `noise_texture` | 🆕 | register=mid, brightness=neutral, attack=swell, filter_motion=strong_sweep, space=hall | none |
| percussive_fx | удар/импакт (тёмный) | `gong` | 🆕 | register=low, brightness=dark, attack=instant, body=long, texture=distorted, space=hall | none |
| percussive_fx | саб-дроп импакт | `kick` |  | register=sub, brightness=dark, attack=instant, body=long, texture=saturated | [DIV]_sub_drop_kick.json |
| percussive_fx | клаве/деревянный клик | `mallet` |  | register=high, brightness=bright, attack=instant, body=staccato, texture=clean | none |
| percussive_fx | перевёрнутый/реверс-наплыв (имитация long attack) | `warm_pad` |  | register=mid, brightness=neutral, attack=swell, body=pluck, space=hall | none |
| drums | синт-кик (808, сабовый синус) | `kick` |  | register=sub, brightness=dark, attack=instant, body=pluck, texture=clean | [DIV]_classic_808_warm_subkick.json |
| drums | синт-кик (909, жёсткий) | `kick` |  | register=low, brightness=warm, attack=instant, body=staccato, texture=gritty | [DIV]_dirty_909_aggressive_kick.json |
| drums | снэр (нойз+тон) | `snare_clap` |  | register=mid, brightness=bright, attack=instant, body=staccato, texture=noisy | none |
| drums | клэп | `snare_clap` |  | register=mid, brightness=bright, attack=instant, body=staccato, texture=noisy, space=room | none |
| drums | хай-хэт закрытый (короткий) | `hihat` |  | register=very_high, brightness=piercing, attack=instant, body=staccato, texture=noisy | none |
| drums | хай-хэт открытый | `hihat` |  | register=very_high, brightness=piercing, attack=instant, body=pluck, texture=noisy | [DS]_breathing_evolution_open_hat.json |
| drums | том (настроенный, питч-дроп) | `tom` | 🆕 | register=low, brightness=warm, attack=instant, body=pluck | none |
| drums | рим-шот/клик | `snare_clap` |  | register=high, brightness=bright, attack=instant, body=staccato, texture=noisy | none |
| drums | каубел (металлический) | `mallet` |  | register=high, brightness=bright, attack=instant, body=staccato, texture=gritty | none |
| drums | шейкер/маракас (нойз) | `hihat` |  | register=very_high, brightness=bright, attack=fast, body=staccato, texture=noisy | none |
| drums | тамбурин | `hihat` |  | register=very_high, brightness=bright, attack=instant, body=pluck, texture=noisy | none |
| drums | конга/бонго (тон-перкуссия) | `tom` | 🆕 | register=mid, brightness=warm, attack=instant, body=pluck | none |
| drums | крэш/райд (металл+нойз) | `cymbal` | 🆕 | register=very_high, brightness=piercing, attack=instant, body=long, texture=noisy, space=room | none |
| drums | пальцевый щелчок/snap | `snare_clap` |  | register=mid, brightness=bright, attack=instant, body=staccato, texture=noisy, space=dry | none |
