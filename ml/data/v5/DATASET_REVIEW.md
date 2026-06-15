# Ревизия датасета v5 — 140 патчей (из 560)

Грузи пресет `[V5] …` в синте, слушай — и сверяй с описаниями ниже. `src=anchor` — параметры из утверждённого тобой реф-якоря (ground-truth); `src=rules` — детерминированный генератор.


## acoustic_emulation (44)

### [V5] аккордеон-баян
- цель: **аккордеон/баян** · роль: `reed` · src: `rules`
- оси: register:mid, brightness:neutral, attack:fast, thickness:unison_thick, body:sustained
- параметры: table=Basic · position=90% · octave=+0 окт · mix_osc1=85% · table=Basic · mix_osc2=60% · mix_noise=14% · lp_cutoff=2500 Гц · amp_attack=12 мс · amp_decay=300 мс · amp_sustain=80% · amp_release=450 мс
- описания (6): «расстроенный баян» · «жирный уличный аккордеон» · «баян, толстый язычок» · «серединка, расстроенные язычки» · «уличный аккордеон» · «баян, тёплый, жирный»

### [V5] арфа
- цель: **арфа** · роль: `guitar` · src: `rules`
- оси: register:mid, brightness:warm, attack:fast, body:pluck, space:hall
- параметры: table=Acoustic · position=69% · octave=+0 окт · mix_osc1=80% · table=Acoustic · mix_osc2=56% · mix_noise=0% · lp_cutoff=850 Гц · amp_attack=12 мс · amp_decay=500 мс · amp_sustain=0% · amp_release=300 мс
- описания (6): «арфа» · «воздушная арфа» · «мягкий щипок арфы» · «переливы струн» · «арфа для релакса» · «арфа затухает мягко»

### [V5] балалайка-домра
- цель: **балалайка/домра** · роль: `guitar` · src: `rules`
- оси: register:mid, brightness:bright, attack:fast, body:pluck
- параметры: table=Acoustic · position=69% · octave=+0 окт · mix_osc1=80% · table=Acoustic · mix_osc2=56% · mix_noise=0% · lp_cutoff=6000 Гц · amp_attack=12 мс · amp_decay=500 мс · amp_sustain=0% · amp_release=300 мс
- описания (6): «балалайка» · «домра» · «щипок балалайки» · «народный щипок» · «звонкая балалайка» · «яркий народный звук»

### [V5] банджо
- цель: **банджо** · роль: `guitar` · src: `rules`
- оси: register:high, brightness:bright, attack:instant, body:staccato
- параметры: table=Acoustic · position=69% · octave=+1 окт · mix_osc1=80% · table=Acoustic · mix_osc2=56% · mix_noise=0% · lp_cutoff=6000 Гц · amp_attack=1 мс · amp_decay=120 мс · amp_sustain=0% · amp_release=80 мс
- описания (6): «банджо» · «дребезжащее банджо» · «кантри банджо» · «щипок банджо» · «отрывистый щипок» · «высокое банджо»

### [V5] вибрафон
- цель: **вибрафон** · роль: `mallet` · src: `anchor`
- оси: register:mid, brightness:warm, body:long, movement:tremolo, space:hall
- параметры: table=Metallic · position=19% · octave=+1 окт · mix_osc1=80% · table=Metallic · mix_osc2=61% · mix_noise=0% · lp_cutoff=3266 Гц · amp_attack=1 мс · amp_decay=1.92 с · amp_sustain=0% · amp_release=1.80 с
- описания (6): «вибрафон» · «тёплый джаз» · «длинный хвост» · «мягкий джазовый металл» · «тремоло вибрафон» · «серединка с тремоло»

### [V5] виолончель (смычок, вибрато)
- цель: **виолончель (смычок, вибрато)** · роль: `string` · src: `rules`
- оси: register:low, brightness:warm, attack:medium, movement:vibrato, space:hall
- параметры: table=Acoustic · position=78% · octave=-1 окт · mix_osc1=80% · table=Acoustic · mix_osc2=0% · mix_noise=0% · lp_cutoff=850 Гц · amp_attack=80 мс · amp_decay=71 мс · amp_sustain=81% · amp_release=350 мс
- описания (6): «виолончель» · «густая виолончель» · «глубокий бас смычком» · «виолончель с вибрато» · «тёплый низкий смычок» · «дрожащий бас серединки»

### [V5] волынка (дрон+мелодия)
- цель: **волынка (дрон+мелодия)** · роль: `reed` · src: `rules`
- оси: register:mid, brightness:bright, attack:fast, body:drone, thickness:unison_thick
- параметры: table=Basic · position=90% · octave=+0 окт · mix_osc1=85% · table=Basic · mix_osc2=60% · mix_noise=14% · lp_cutoff=6000 Гц · amp_attack=12 мс · amp_decay=500 мс · amp_sustain=100% · amp_release=4.00 с
- описания (6): «волынка» · «шотландский дрон» · «жирный язычковый дрон» · «толстый гудящий дрон» · «гобой-подобная волынка» · «быстрая атака волынки»

### [V5] гобой-двойная трость (носовой)
- цель: **гобой/двойная трость (носовой)** · роль: `reed` · src: `rules`
- оси: register:mid, brightness:bright, attack:fast, body:sustained
- параметры: table=Basic · position=90% · octave=+0 окт · mix_osc1=85% · table=Basic · mix_osc2=66% · mix_noise=14% · lp_cutoff=6000 Гц · amp_attack=12 мс · amp_decay=300 мс · amp_sustain=80% · amp_release=450 мс
- описания (6): «гобой» · «пронзительный язычок» · «яркий гнусавый звук» · «серединка, трость, быстро» · «носовой тембр, светлый» · «гобой, пронзительный, средний»

### [V5] губная гармоника
- цель: **губная гармоника** · роль: `reed` · src: `rules`
- оси: register:mid, brightness:bright, attack:fast, texture:noisy
- параметры: table=Basic · position=90% · octave=+0 окт · mix_osc1=85% · table=Basic · mix_osc2=66% · mix_noise=30% · lp_cutoff=6000 Гц · amp_attack=12 мс · amp_decay=71 мс · amp_sustain=80% · amp_release=200 мс
- описания (6): «блюзовая губная гармоника» · «яркая гармошка» · «хриплая гармоника» · «светлая гармошка с придыханием» · «блюзовый язычок» · «harp, хриплая, шумная»

### [V5] калимба (металлические язычки)
- цель: **калимба (металлические язычки)** · роль: `mallet` · src: `rules`
- оси: register:high, brightness:neutral, body:pluck
- параметры: table=Acoustic · position=15% · octave=+1 окт · mix_osc1=85% · table=Acoustic · mix_osc2=67% · mix_noise=0% · lp_cutoff=2500 Гц · amp_attack=1 мс · amp_decay=500 мс · amp_sustain=0% · amp_release=300 мс
- описания (6): «калимба» · «мягкий высокий щипок» · «нейтральная калимба» · «калимба верх» · «мягкий язычок» · «санса высокая»

### [V5] клавесин
- цель: **клавесин** · роль: `pluck` · src: `rules`
- оси: register:mid, brightness:bright, attack:instant, body:pluck
- параметры: table=Basic · position=67% · octave=+0 окт · mix_osc1=85% · table=Basic · mix_osc2=52% · mix_noise=0% · lp_cutoff=6000 Гц · amp_attack=2 мс · amp_decay=400 мс · amp_sustain=0% · amp_release=300 мс
- описания (6): «клавесин» · «барочный щипок» · «звонкий клавесин» · «яркий плак» · «механический щипок струн» · «светлый клавесин с щелчком»

### [V5] клавинет (фанк)
- цель: **клавинет (фанк)** · роль: `epiano` · src: `rules`
- оси: register:mid, brightness:bright, attack:instant, body:pluck, texture:gritty
- параметры: table=Acoustic · position=25% · octave=+0 окт · mix_osc1=80% · table=Acoustic · mix_osc2=70% · mix_noise=5% · lp_cutoff=6000 Гц · amp_attack=4 мс · amp_decay=600 мс · amp_sustain=35% · amp_release=400 мс
- описания (6): «фанк-клавинет» · «щёлкающий клавинет» · «острый электро-щипок» · «грязный фанк» · «bright clavinet» · «яркий щёлкающий плак»

### [V5] кларнет (полый, нечётные обертоны)
- цель: **кларнет (полый, нечётные обертоны)** · роль: `reed` · src: `anchor`
- оси: register:mid, brightness:warm, attack:fast, body:sustained
- параметры: table=Basic · position=94% · octave=+0 окт · mix_osc1=80% · table=Vocal · mix_osc2=66% · mix_noise=14% · lp_cutoff=3099 Гц · amp_attack=130 мс · amp_decay=100 мс · amp_sustain=85% · amp_release=350 мс
- описания (6): «кларнет тёплый» · «полый деревянный язычок» · «серединка с тянущимся звуком» · «мягкий кларнет, резкий старт» · «деревянный тянущийся тон» · «кларнет, быстрая атака, тёплый»

### [V5] классическая гитара (щипок)
- цель: **классическая гитара (щипок)** · роль: `guitar` · src: `rules`
- оси: register:mid, brightness:warm, attack:fast, body:pluck, space:room
- параметры: table=Acoustic · position=69% · octave=+0 окт · mix_osc1=80% · table=Acoustic · mix_osc2=56% · mix_noise=0% · lp_cutoff=850 Гц · amp_attack=12 мс · amp_decay=500 мс · amp_sustain=0% · amp_release=300 мс
- описания (6): «классическая гитара» · «нейлоновая гитара» · «тёплый щипок» · «акустическая гитарка» · «щёлкающий перебор» · «мягкий гитарный звук»

### [V5] колокольчики-глокеншпиль
- цель: **колокольчики/глокеншпиль** · роль: `bell` · src: `rules`
- оси: register:very_high, brightness:piercing, body:pluck, space:hall
- параметры: table=Metallic · position=10% · octave=+2 окт · mix_osc1=85% · table=Metallic · mix_osc2=0% · mix_noise=0% · lp_cutoff=11000 Гц · amp_attack=1 мс · amp_decay=500 мс · amp_sustain=0% · amp_release=300 мс
- описания (6): «глокеншпиль» · «металлический звон» · «пронзительные колокольчики» · «очень высокий звон» · «звонкий металл» · «верхний глокеншпиль»

### [V5] колёсная лира-шарманка (дрон)
- цель: **колёсная лира/шарманка (дрон)** · роль: `reed` · src: `rules`
- оси: register:mid, brightness:neutral, body:drone, texture:gritty
- параметры: table=Basic · position=90% · octave=+0 окт · mix_osc1=85% · table=Basic · mix_osc2=66% · mix_noise=5% · lp_cutoff=2500 Гц · amp_attack=40 мс · amp_decay=500 мс · amp_sustain=100% · amp_release=4.00 с
- описания (6): «колёсная лира-дрон» · «шарманка, грязный язычок» · «гулкий механический фон» · «средневековая подложка» · «язычковый гудящий дрон» · «реedenый шарманочный фон»

### [V5] контрабас (пиццикато и смычок)
- цель: **контрабас (пиццикато и смычок)** · роль: `string` · src: `rules`
- оси: register:sub, brightness:dark, attack:medium, space:room
- параметры: table=Acoustic · position=78% · octave=-2 окт · mix_osc1=80% · table=Acoustic · mix_osc2=0% · mix_noise=0% · lp_cutoff=400 Гц · amp_attack=80 мс · amp_decay=71 мс · amp_sustain=81% · amp_release=350 мс
- описания (6): «контрабас пиццикато» · «глубокий глухой струнный» · «сабовый комнатный звук» · «туманный контрабас без блеска» · «щипок на контрабасе, тёмный и густой» · «низкая струна, мягко отщипнутая»

### [V5] кото-гучжэн
- цель: **кото/гучжэн** · роль: `guitar` · src: `rules`
- оси: register:mid, brightness:neutral, attack:fast, body:pluck, space:hall
- параметры: table=Acoustic · position=69% · octave=+0 окт · mix_osc1=80% · table=Acoustic · mix_osc2=56% · mix_noise=0% · lp_cutoff=2500 Гц · amp_attack=12 мс · amp_decay=500 мс · amp_sustain=0% · amp_release=300 мс
- описания (6): «кото» · «японский щипок» · «затухающая восточная струна» · «просторный кото» · «балансированный щипок серединки» · «гучжэн зальный»

### [V5] литавры (настроенный барабан)
- цель: **литавры (настроенный барабан)** · роль: `tom` · src: `anchor`
- оси: register:low, brightness:dark, body:pluck, texture:saturated
- параметры: table=Metallic · position=15% · octave=-2 окт · mix_osc1=80% · table=Acoustic · mix_osc2=69% · mix_noise=86% · lp_cutoff=1219 Гц · amp_attack=1 мс · amp_decay=1.63 с · amp_sustain=0% · amp_release=526 мс
- описания (6): «настроенные литавры» · «глубокий оркестровый раскат» · «басовый затухающий том» · «туманный низкий гул» · «литавры-конга, глухой» · «насыщенный тёмный раскат»

### [V5] мандолина
- цель: **мандолина** · роль: `guitar` · src: `rules`
- оси: register:high, brightness:bright, attack:fast, body:pluck, movement:tremolo
- параметры: table=Acoustic · position=69% · octave=+1 окт · mix_osc1=80% · table=Acoustic · mix_osc2=56% · mix_noise=0% · lp_cutoff=6000 Гц · amp_attack=12 мс · amp_decay=500 мс · amp_sustain=0% · amp_release=300 мс
- описания (6): «мандолина» · «тремоло мандолины» · «пульсирующая мандолина» · «быстрый щипок мандолины» · «сдвоенные струны» · «звонкое тремоло»

### [V5] маримба-ксилофон
- цель: **маримба/ксилофон** · роль: `mallet` · src: `anchor`
- оси: register:mid, brightness:warm, body:pluck, texture:clean
- параметры: table=Basic · position=7% · octave=+1 окт · mix_osc1=80% · table=Metallic · mix_osc2=73% · mix_noise=0% · lp_cutoff=2100 Гц · amp_attack=1 мс · amp_decay=191 мс · amp_sustain=0% · amp_release=252 мс
- описания (6): «маримба» · «тёплый деревянный удар» · «мягкая перкуссия» · «чистый средний регистр» · «деревянная шкатулка» · «ксилофон тёплый»

### [V5] музыкальная шкатулка
- цель: **музыкальная шкатулка** · роль: `mallet` · src: `rules`
- оси: register:very_high, brightness:bright, body:pluck, movement:tremolo, space:hall
- параметры: table=Metallic · position=15% · octave=+2 окт · mix_osc1=85% · table=Metallic · mix_osc2=67% · mix_noise=0% · lp_cutoff=6000 Гц · amp_attack=1 мс · amp_decay=500 мс · amp_sustain=0% · amp_release=300 мс
- описания (6): «музыкальная шкатулка» · «хрупкий детский звон» · «ностальгическая шкатулка» · «тремоло высокой шкатулки» · «пульсирующий пэд шкатулки» · «пронзительный звон из детства»

### [V5] окарина
- цель: **окарина** · роль: `pure_tone` · src: `rules`
- оси: register:high, brightness:warm, attack:medium, movement:vibrato
- параметры: table=Basic · position=0% · octave=+1 окт · mix_osc1=80% · table=Basic · mix_osc2=19% · mix_noise=0% · lp_cutoff=850 Гц · amp_attack=80 мс · amp_decay=71 мс · amp_sustain=85% · amp_release=250 мс
- описания (6): «окарина с вибрато» · «мягкий свист окарины» · «круглый тёплый тон» · «глиняная свистулька колеблется» · «высокая окарина с вибрато» · «мягкий синус окарины»

### [V5] орган Хаммонд с лесли
- цель: **орган Хаммонд с лесли** · роль: `organ` · src: `rules`
- оси: register:mid, brightness:bright, movement:leslie, texture:gritty, space:room
- параметры: table=Organ · position=45% · octave=+0 окт · mix_osc1=80% · table=Organ · mix_osc2=55% · mix_noise=5% · lp_cutoff=6000 Гц · amp_attack=4 мс · amp_decay=20 мс · amp_sustain=82% · amp_release=30 мс
- описания (6): «хаммонд с лесли» · «роторный орган» · «грязный рок-орган» · «орган с вращающимся динамиком» · «светлый кружащийся орган» · «шершавый хаммонд в комнате»

### [V5] пан-флейта
- цель: **пан-флейта** · роль: `flute` · src: `rules`
- оси: register:high, brightness:warm, attack:medium, texture:noisy
- параметры: table=Acoustic · position=8% · octave=+1 окт · mix_osc1=65% · table=Acoustic · mix_osc2=45% · mix_noise=30% · lp_cutoff=850 Гц · amp_attack=120 мс · amp_decay=71 мс · amp_sustain=82% · amp_release=300 мс
- описания (6): «пан-флейта тёплая» · «мягкая этно-флейта» · «полый тёплый верх» · «пан-флейта, дыхательная и мягкая» · «этно духовая с придыханием» · «мягкий полый свист пан-флейты»

### [V5] саксофон (язычковый)
- цель: **саксофон (язычковый)** · роль: `reed` · src: `rules`
- оси: register:mid, brightness:bright, attack:fast, texture:noisy, movement:vibrato
- параметры: table=Basic · position=90% · octave=+0 окт · mix_osc1=85% · table=Basic · mix_osc2=66% · mix_noise=30% · lp_cutoff=6000 Гц · amp_attack=12 мс · amp_decay=71 мс · amp_sustain=80% · amp_release=200 мс
- описания (6): «саксофон» · «дымный сакс, джаз» · «яркий медный язычок» · «серединка, вибрато, шумно» · «сакс, воздушный, колышется» · «саксофон, джаз, придыхание»

### [V5] свист
- цель: **свист** · роль: `pure_tone` · src: `anchor`
- оси: register:high, brightness:bright, attack:medium, movement:vibrato
- параметры: table=Basic · position=4% · octave=+1 окт · mix_osc1=80% · table=Basic · mix_osc2=38% · mix_noise=1% · lp_cutoff=18000 Гц · amp_attack=15 мс · amp_decay=80 мс · amp_sustain=88% · amp_release=150 мс
- описания (6): «губной свист» · «свист с вибрато» · «высокий чистый тон» · «свист, светлый и яркий» · «синусоидальный свист» · «свист окарины»

### [V5] ситар (дрон+щипок)
- цель: **ситар (дрон+щипок)** · роль: `guitar` · src: `rules`
- оси: register:mid, brightness:bright, attack:fast, body:sustained, texture:gritty
- параметры: table=Acoustic · position=69% · octave=+0 окт · mix_osc1=80% · table=Acoustic · mix_osc2=56% · mix_noise=5% · lp_cutoff=6000 Гц · amp_attack=12 мс · amp_decay=300 мс · amp_sustain=80% · amp_release=450 мс
- описания (6): «ситар» · «восточный щипок» · «дребезжащий ситар» · «индийский щипок струны» · «грязный резонанс серединки» · «шершавый тёплый ситар»

### [V5] скрипка (вибрато, яркая)
- цель: **скрипка (вибрато, яркая)** · роль: `string` · src: `rules`
- оси: register:high, brightness:bright, attack:medium, movement:vibrato, space:hall
- параметры: table=Acoustic · position=78% · octave=+1 окт · mix_osc1=80% · table=Acoustic · mix_osc2=0% · mix_noise=0% · lp_cutoff=6000 Гц · amp_attack=80 мс · amp_decay=71 мс · amp_sustain=81% · amp_release=350 мс
- описания (6): «скрипка» · «яркая скрипка» · «пронзительный верх» · «виолончельный верх» · «смычок вверху» · «дрожащий верх серединки»

### [V5] стальная акустическая гитара
- цель: **стальная акустическая гитара** · роль: `guitar` · src: `rules`
- оси: register:mid, brightness:bright, attack:fast, body:pluck, texture:clean
- параметры: table=Acoustic · position=69% · octave=+0 окт · mix_osc1=80% · table=Acoustic · mix_osc2=56% · mix_noise=0% · lp_cutoff=6000 Гц · amp_attack=12 мс · amp_decay=500 мс · amp_sustain=0% · amp_release=300 мс
- описания (6): «стальная акустическая гитара» · «звонкая струна» · «бой на акустике» · «яркий щипок стали» · «светлая акустическая гитара» · «чистый стальной звук»

### [V5] стил-пан (карибский)
- цель: **стил-пан (карибский)** · роль: `mallet` · src: `rules`
- оси: register:mid, brightness:bright, body:pluck, space:room
- параметры: table=Metallic · position=15% · octave=+0 окт · mix_osc1=85% · table=Metallic · mix_osc2=67% · mix_noise=0% · lp_cutoff=6000 Гц · amp_attack=1 мс · amp_decay=500 мс · amp_sustain=0% · amp_release=300 мс
- описания (6): «карибский стил-пан» · «тропический звонкий металл» · «маримба, карибский оттенок» · «яркий стаккато стил-пан» · «калимба-подобный карибский удар» · «стил-пан, тропический, светлый»

### [V5] стилизованные духовые (туба, валторна)
- цель: **стилизованные духовые (туба, валторна)** · роль: `brass` · src: `rules`
- оси: register:low, brightness:warm, attack:medium, space:hall
- параметры: table=Basic · position=62% · octave=-1 окт · mix_osc1=85% · table=Basic · mix_osc2=60% · mix_noise=11% · lp_cutoff=850 Гц · amp_attack=80 мс · amp_decay=71 мс · amp_sustain=82% · amp_release=250 мс
- описания (6): «тёплый духовой» · «благородная медь» · «зальный басовый духовой» · «мягкая туба» · «туба и валторна, тёплый низ» · «просторный медный пэд»

### [V5] терменвокс-подобный непрерывный тон
- цель: **терменвокс-подобный непрерывный тон** · роль: `pure_tone` · src: `anchor`
- оси: register:high, brightness:neutral, attack:soft, movement:vibrato, space:hall
- параметры: table=Basic · position=4% · octave=+0 окт · mix_osc1=80% · table=Basic · mix_osc2=0% · mix_noise=0% · lp_cutoff=18000 Гц · amp_attack=64 мс · amp_decay=1 мс · amp_sustain=100% · amp_release=317 мс
- описания (6): «терменвокс» · «космический голос» · «поющий высокий тон» · «плывущий синус» · «зальный свистящий тон» · «свист с вибрато, пространство»

### [V5] тромбон
- цель: **тромбон** · роль: `brass` · src: `anchor`
- оси: register:low, brightness:neutral, attack:medium
- параметры: table=Basic · position=62% · octave=-1 окт · mix_osc1=80% · table=Basic · mix_osc2=60% · mix_noise=11% · lp_cutoff=3899 Гц · amp_attack=32 мс · amp_decay=420 мс · amp_sustain=81% · amp_release=43 мс
- описания (6): «тромбон» · «скользящая медь» · «низкий густой духовой» · «тромбон, басовый, сбалансированный» · «низкая медь, скользит» · «тромбон, тёплый, нейтральный»

### [V5] труба (открытая-сурдина)
- цель: **труба (открытая/сурдина)** · роль: `brass` · src: `anchor`
- оси: register:high, brightness:bright, attack:fast, filter_motion:gentle_sweep
- параметры: table=Basic · position=62% · octave=+0 окт · mix_osc1=80% · table=Basic · mix_osc2=60% · mix_noise=11% · lp_cutoff=3899 Гц · amp_attack=32 мс · amp_decay=420 мс · amp_sustain=81% · amp_release=56 мс
- описания (6): «труба» · «фанфары» · «яркая медь, свип» · «высокая труба, мягко открывается» · «открытая труба, быстро» · «блат труба, верхний регистр»

### [V5] трубчатые колокола
- цель: **трубчатые колокола** · роль: `bell` · src: `rules`
- оси: register:mid, brightness:bright, body:long, space:hall
- параметры: table=Metallic · position=10% · octave=+0 окт · mix_osc1=85% · table=Metallic · mix_osc2=0% · mix_noise=0% · lp_cutoff=6000 Гц · amp_attack=1 мс · amp_decay=400 мс · amp_sustain=2% · amp_release=2.50 с
- описания (6): «трубчатые колокола» · «оркестровый длинный звон» · «торжественный просторный колокол» · «бескрайний колокольный звон» · «зальный колокол, долгий хвост» · «торжественный, просторный, яркий»

### [V5] фагот (низкий двойной язычок)
- цель: **фагот (низкий двойной язычок)** · роль: `reed` · src: `rules`
- оси: register:low, brightness:warm, attack:medium, body:sustained
- параметры: table=Basic · position=90% · octave=-1 окт · mix_osc1=85% · table=Basic · mix_osc2=66% · mix_noise=14% · lp_cutoff=850 Гц · amp_attack=80 мс · amp_decay=300 мс · amp_sustain=80% · amp_release=450 мс
- описания (6): «фагот» · «деревянный бас» · «ворчливый язычок» · «низкий фагот, тёплый» · «басовая трость, мягко» · «фагот, низкий, держится»

### [V5] фисгармония (reed organ)
- цель: **фисгармония (reed organ)** · роль: `reed` · src: `rules`
- оси: register:mid, brightness:warm, attack:medium, body:sustained
- параметры: table=Basic · position=90% · octave=+0 окт · mix_osc1=85% · table=Basic · mix_osc2=66% · mix_noise=14% · lp_cutoff=850 Гц · amp_attack=80 мс · amp_decay=300 мс · amp_sustain=80% · amp_release=450 мс
- описания (6): «тёплый язычковый орган» · «фисгармония» · «тёплый гудящий язычок» · «церковный язычок, тёплый» · «серединка, тёплый орган» · «physharmonica, язычковый»

### [V5] флейта (с придыханием)
- цель: **флейта (с придыханием)** · роль: `flute` · src: `anchor`
- оси: register:high, brightness:neutral, attack:medium, texture:noisy, movement:vibrato
- параметры: table=Basic · position=8% · octave=+0 окт · mix_osc1=65% · table=Basic · mix_osc2=45% · mix_noise=7% · lp_cutoff=1729 Гц · amp_attack=40 мс · amp_decay=120 мс · amp_sustain=90% · amp_release=300 мс
- описания (6): «флейта с придыханием» · «воздушная высокая дудочка» · «свистящий верхний регистр» · «нежное придыхание на флейте» · «воздушный звенящий свист» · «флейта свистящая, лёгкая»

### [V5] фортепиано (мягкий плак)
- цель: **фортепиано (мягкий плак)** · роль: `piano` · src: `rules`
- оси: register:mid, brightness:warm, texture:clean, space:room
- параметры: table=Acoustic · position=50% · octave=+0 окт · mix_osc1=80% · table=Acoustic · mix_osc2=60% · mix_noise=0% · lp_cutoff=850 Гц · amp_attack=3 мс · amp_decay=2.00 с · amp_sustain=0% · amp_release=320 мс
- описания (6): «мягкое пианино» · «тёплый рояль» · «тихое фортепиано с эхом» · «акустическое пианино серединка» · «мягкий плак рояля» · «тёплый угасающий рояль»

### [V5] хор-вокальный ах
- цель: **хор/вокальный ах** · роль: `choir_pad` · src: `rules`
- оси: register:mid, brightness:neutral, vowel:a_open, space:hall
- параметры: table=Vocal · position=50% · octave=+0 окт · mix_osc1=80% · table=Vocal · mix_osc2=57% · mix_noise=0% · lp_cutoff=2500 Гц · amp_attack=120 мс · amp_decay=71 мс · amp_sustain=90% · amp_release=800 мс
- описания (6): «хоровое ах» · «ангельский хор на а» · «зальный вокальный пэд» · «ахи хора в пространстве» · «хор, звук ааа» · «пэд хорового а»

### [V5] церковный орган
- цель: **церковный орган** · роль: `organ` · src: `rules`
- оси: register:low, brightness:neutral, movement:static, space:hall
- параметры: table=Organ · position=45% · octave=-1 окт · mix_osc1=80% · table=Organ · mix_osc2=55% · mix_noise=4% · lp_cutoff=2500 Гц · amp_attack=4 мс · amp_decay=20 мс · amp_sustain=82% · amp_release=30 мс
- описания (6): «величавый церковный орган» · «соборный орган» · «хоральный орган» · «орган с квинтой» · «грандиозный низкий орган» · «зальный величественный орган»

### [V5] челеста
- цель: **челеста** · роль: `bell` · src: `rules`
- оси: register:high, brightness:bright, body:pluck, space:hall
- параметры: table=Metallic · position=10% · octave=+1 окт · mix_osc1=85% · table=Metallic · mix_osc2=0% · mix_noise=0% · lp_cutoff=6000 Гц · amp_attack=1 мс · amp_decay=500 мс · amp_sustain=0% · amp_release=300 мс
- описания (6): «челеста» · «хрустальный звон» · «колокольчиковые клавиши» · «яркий верхний регистр» · «сказочный пэд» · «зальный звон сказки»

### [V5] электропиано-родес
- цель: **электропиано/родес** · роль: `epiano` · src: `anchor`
- оси: register:mid, brightness:warm, texture:saturated, movement:tremolo
- параметры: table=Basic · position=30% · octave=+0 окт · mix_osc1=80% · table=Basic · mix_osc2=70% · mix_noise=3% · lp_cutoff=3779 Гц · amp_attack=8 мс · amp_decay=2.10 с · amp_sustain=0% · amp_release=74 мс
- описания (6): «родес с тремоло» · «ламповый родес» · «пульсирующие соул-клавиши» · «тёплый электропиано» · «родес качается» · «rhodes, тёплый, с лампой»


## synth_roles (34)

### [V5] 808-саб (длинный сабовый тон)
- цель: **808-саб (длинный сабовый тон)** · роль: `sub_bass` · src: `rules`
- оси: register:sub, brightness:warm, body:long, texture:saturated
- параметры: table=Basic · position=0% · octave=-2 окт · mix_osc1=100% · table=Basic · mix_osc2=0% · mix_noise=0% · lp_cutoff=850 Гц · amp_attack=4 мс · amp_decay=400 мс · amp_sustain=75% · amp_release=2.50 с
- описания (6): «808 саб» · «тёплый длинный саб» · «гудящий подвальный бас» · «мягкий 808-суб для трэпа» · «тёплый суб-бас с долгим хвостом» · «насыщенный сабовый гул»

### [V5] FM-белл-лид
- цель: **FM-белл-лид** · роль: `bell` · src: `rules`
- оси: register:high, brightness:bright, body:sustained, space:hall
- параметры: table=Metallic · position=10% · octave=+1 окт · mix_osc1=85% · table=Metallic · mix_osc2=0% · mix_noise=0% · lp_cutoff=6000 Гц · amp_attack=1 мс · amp_decay=300 мс · amp_sustain=2% · amp_release=450 мс
- описания (6): «fm-белл» · «DX-колокольчик» · «яркий зальный перезвон» · «цифровой звон в зале» · «высокий колокол с хвостом» · «светлый fm-лид»

### [V5] PWM-квадратный лид
- цель: **PWM/квадратный лид** · роль: `square_lead` · src: `anchor`
- оси: register:mid, brightness:bright, movement:vibrato
- параметры: table=Basic · position=93% · octave=+0 окт · mix_osc1=80% · table=Digital · mix_osc2=55% · mix_noise=0% · lp_cutoff=9500 Гц · amp_attack=13 мс · amp_decay=350 мс · amp_sustain=65% · amp_release=300 мс
- описания (6): «PWM-лид винтажный» · «квадратный лид для чиптюна» · «полый светлый лид» · «8-бит PWM ведущий голос» · «яркий квадратный лид» · «серединка, винтажный, вибрирует»

### [V5] acid-бас (резонанс+огибающая)
- цель: **acid-бас (резонанс+огибающая)** · роль: `acid_bass` · src: `rules`
- оси: register:low, brightness:bright, filter_motion:pluck_wah, texture:gritty
- параметры: table=Basic · position=68% · octave=-1 окт · mix_osc1=80% · table=Basic · mix_osc2=0% · mix_noise=5% · lp_cutoff=6000 Гц · amp_attack=1 мс · amp_decay=830 мс · amp_sustain=0% · amp_release=6 мс
- описания (6): «кислотный бас» · «яркий 303» · «сквелч-бас» · «acid 303, вау-щипок» · «кислотный бас, светлый» · «цепкий 303-й для техно»

### [V5] fm-бас
- цель: **fm-бас** · роль: `reese_bass` · src: `rules`
- оси: register:low, brightness:bright, texture:gritty
- параметры: table=Basic · position=75% · octave=-1 окт · mix_osc1=90% · table=Basic · mix_osc2=63% · mix_noise=5% · lp_cutoff=6000 Гц · amp_attack=7 мс · amp_decay=71 мс · amp_sustain=88% · amp_release=80 мс
- описания (6): «металлический фм-бас» · «колокольный рииз» · «цифровой fm бас» · «шершавый fm низ» · «грязный рииз» · «фм бас колокольчик»

### [V5] growl-neuro-бас
- цель: **growl/neuro-бас** · роль: `reese_bass` · src: `rules`
- оси: register:low, brightness:bright, movement:filter_wobble, texture:distorted, character:aggressive
- параметры: table=Basic · position=75% · octave=-1 окт · mix_osc1=90% · table=Basic · mix_osc2=63% · mix_noise=0% · lp_cutoff=6000 Гц · amp_attack=7 мс · amp_decay=71 мс · amp_sustain=88% · amp_release=80 мс
- описания (6): «рычащий нейро-бас» · «гроул для днб» · «злой агрессивный бас» · «reese bass wobble» · «гроул с фильтром» · «рычащий низ с дисторшном»

### [V5] hoover-лид (рейв)
- цель: **hoover-лид (рейв)** · роль: `saw_lead` · src: `rules`
- оси: register:mid, brightness:bright, movement:vibrato, texture:gritty
- параметры: table=Basic · position=71% · octave=+0 окт · mix_osc1=80% · table=Basic · mix_osc2=70% · mix_noise=5% · lp_cutoff=6000 Гц · amp_attack=10 мс · amp_decay=71 мс · amp_sustain=80% · amp_release=250 мс
- описания (6): «hoover-лид рейв» · «воющий синт 90х» · «грязный хувер для транса» · «рейв-лид с шероховатым характером» · «яркий hoover» · «суперпила, воющая, шершавая»

### [V5] lo-fi-винтаж keys
- цель: **lo-fi/винтаж keys** · роль: `epiano` · src: `rules`
- оси: register:mid, brightness:warm, texture:noisy, character:melancholic
- параметры: table=Acoustic · position=25% · octave=+0 окт · mix_osc1=80% · table=Acoustic · mix_osc2=70% · mix_noise=30% · lp_cutoff=850 Гц · amp_attack=4 мс · amp_decay=600 мс · amp_sustain=35% · amp_release=400 мс
- описания (6): «пыльный родес» · «хрустящие клавиши» · «грустное электропиано» · «ностальгические клавиши с шумом» · «меланхоличный пэд с придыханием» · «винтажное пиано серединка»

### [V5] pluck-бас
- цель: **pluck-бас** · роль: `pluck` · src: `rules`
- оси: register:low, brightness:warm, attack:instant, body:pluck
- параметры: table=Basic · position=67% · octave=-1 окт · mix_osc1=85% · table=Basic · mix_osc2=52% · mix_noise=0% · lp_cutoff=850 Гц · amp_attack=2 мс · amp_decay=400 мс · amp_sustain=0% · amp_release=300 мс
- описания (6): «плак-бас» · «упругий щипковый бас» · «тёплый затухающий низ» · «щипок с щелчком» · «бас-плак» · «мягкий низкий плак»

### [V5] reese-бас (детюн, грязный)
- цель: **reese-бас (детюн, грязный)** · роль: `reese_bass` · src: `rules`
- оси: register:low, brightness:neutral, texture:gritty, movement:filter_wobble
- параметры: table=Basic · position=75% · octave=-1 окт · mix_osc1=90% · table=Basic · mix_osc2=63% · mix_noise=5% · lp_cutoff=2500 Гц · amp_attack=7 мс · amp_decay=71 мс · amp_sustain=88% · amp_release=80 мс
- описания (6): «реиз-бас» · «расстроенный грязный бас» · «дрожащий D&B-бас» · «DnB, реиз, шершавый» · «зернистый нейро-бас» · «реиз для драм-н-бейса»

### [V5] supersaw-лид
- цель: **supersaw-лид** · роль: `saw_lead` · src: `anchor`
- оси: register:mid, brightness:bright, thickness:unison_thick, space:hall
- параметры: table=Basic · position=71% · octave=+0 окт · mix_osc1=80% · table=Basic · mix_osc2=67% · mix_noise=0% · lp_cutoff=5378 Гц · amp_attack=11 мс · amp_decay=340 мс · amp_sustain=89% · amp_release=180 мс
- описания (6): «суперпила» · «транс-лид» · «детюн рейв-лид» · «зальный суперсай» · «пилообразный лид» · «жирный лид для транса»

### [V5] wobble-dubstep-бас (LFO→фильтр)
- цель: **wobble/dubstep-бас (LFO→фильтр)** · роль: `reese_bass` · src: `rules`
- оси: register:low, brightness:neutral, movement:filter_wobble, texture:distorted
- параметры: table=Basic · position=75% · octave=-1 окт · mix_osc1=90% · table=Basic · mix_osc2=63% · mix_noise=0% · lp_cutoff=2500 Гц · amp_attack=7 мс · amp_decay=71 мс · amp_sustain=88% · amp_release=80 мс
- описания (6): «dubstep-бас» · «воббл-бас» · «вау-вау бас» · «dubstep, ритмично открывается» · «грязный вобл с дисторшном» · «wobble-бас для дабстепа»

### [V5] арп-звук
- цель: **арп-звук** · роль: `pluck` · src: `rules`
- оси: register:mid, brightness:bright, attack:fast, body:pluck, space:room
- параметры: table=Basic · position=67% · octave=+0 окт · mix_osc1=85% · table=Basic · mix_osc2=52% · mix_noise=0% · lp_cutoff=6000 Гц · amp_attack=2 мс · amp_decay=400 мс · amp_sustain=0% · amp_release=300 мс
- описания (6): «яркий арп-плак» · «светлый щипок с эхом» · «бегущий арпеджио серединка» · «быстрая атака с резцом» · «арп-щипок для техно» · «плак, светлый, комнатный»

### [V5] брасс-синт (sync-saw)
- цель: **брасс-синт (sync/saw)** · роль: `brass` · src: `rules`
- оси: register:mid, brightness:bright, attack:fast, filter_motion:gentle_sweep
- параметры: table=Basic · position=62% · octave=+0 окт · mix_osc1=85% · table=Basic · mix_osc2=60% · mix_noise=11% · lp_cutoff=6000 Гц · amp_attack=12 мс · amp_decay=71 мс · amp_sustain=82% · amp_release=250 мс
- описания (6): «80е брасс синтезатор» · «пиловая медь светлая» · «фанфарный синт свип» · «быстрый брасс серединка» · «синт-труба светлая» · «брасс, резкий, свипующий»

### [V5] мэллет-синт (мягкий перкуссивный)
- цель: **мэллет-синт (мягкий перкуссивный)** · роль: `mallet` · src: `rules`
- оси: register:mid, brightness:warm, body:pluck, space:room
- параметры: table=Acoustic · position=15% · octave=+0 окт · mix_osc1=85% · table=Acoustic · mix_osc2=67% · mix_noise=0% · lp_cutoff=850 Гц · amp_attack=1 мс · amp_decay=500 мс · amp_sustain=0% · amp_release=300 мс
- описания (6): «мягкий мэллет» · «колокольчик-синт» · «уютная маримба» · «тёплый щипок с эхом» · «калимба-подобный звук» · «мягкая перкуссия для фонa»

### [V5] мягкий флейтовый лид
- цель: **мягкий флейтовый лид** · роль: `pure_tone` · src: `rules`
- оси: register:high, brightness:warm, attack:soft, movement:vibrato
- параметры: table=Basic · position=0% · octave=+1 окт · mix_osc1=80% · table=Basic · mix_osc2=19% · mix_noise=0% · lp_cutoff=850 Гц · amp_attack=400 мс · amp_decay=71 мс · amp_sustain=85% · amp_release=250 мс
- описания (6): «мягкий флейтовый лид» · «нежный синт-свист» · «плавный тёплый верхний тон» · «флейта с вибрато» · «чистый округлый лид» · «мягкий свистящий синт»

### [V5] пилообразный синт-бас (аналоговый)
- цель: **пилообразный синт-бас (аналоговый)** · роль: `saw_bass` · src: `anchor`
- оси: register:low, brightness:neutral, attack:fast, texture:saturated, space:dry
- параметры: table=Basic · position=69% · octave=-1 окт · mix_osc1=80% · table=Basic · mix_osc2=55% · mix_noise=0% · lp_cutoff=928 Гц · amp_attack=1 мс · amp_decay=350 мс · amp_sustain=84% · amp_release=120 мс
- описания (6): «аналоговый пила-бас» · «moog-бас» · «упругий пилообразный бас» · «синт-бас, тёплый, насыщенный» · «пила-бас с быстрой атакой» · «аналоговый бас для электро»

### [V5] плак (короткий, перкуссивный)
- цель: **плак (короткий, перкуссивный)** · роль: `pluck` · src: `anchor`
- оси: register:mid, brightness:bright, attack:instant, body:pluck, space:room
- параметры: table=Acoustic · position=67% · octave=+0 окт · mix_osc1=80% · table=Acoustic · mix_osc2=52% · mix_noise=3% · lp_cutoff=5432 Гц · amp_attack=1 мс · amp_decay=269 мс · amp_sustain=0% · amp_release=89 мс
- описания (6): «короткий щипок с эхом» · «яркий плак» · «упругий щелчок» · «дзынь-плак для серединки» · «светлый затухающий щипок» · «перкуссивный плак с комнатным ревером»

### [V5] пронзительный соло-лид
- цель: **пронзительный соло-лид** · роль: `saw_lead` · src: `rules`
- оси: register:high, brightness:piercing, movement:vibrato
- параметры: table=Basic · position=71% · octave=+1 окт · mix_osc1=80% · table=Basic · mix_osc2=70% · mix_noise=0% · lp_cutoff=11000 Гц · amp_attack=10 мс · amp_decay=71 мс · amp_sustain=80% · amp_release=250 мс
- описания (6): «пронзительный соло-лид» · «режущий верхний лид с вибрато» · «высокий колющий синт-лид» · «суперпила с колышущимся голосом» · «острый транс-лид для соло» · «соло-пила, пронзительная, вибрирует»

### [V5] пэд эволюционирующий (движение тембра)
- цель: **пэд эволюционирующий (движение тембра)** · роль: `warm_pad` · src: `rules`
- оси: register:mid, brightness:neutral, attack:swell, body:drone, movement:wt_morph, space:vast
- параметры: table=Basic · position=35% · octave=+0 окт · mix_osc1=75% · table=Basic · mix_osc2=55% · mix_noise=0% · lp_cutoff=2500 Гц · amp_attack=1.50 с · amp_decay=71 мс · amp_sustain=85% · amp_release=2.20 с
- описания (6): «дышащий тёплый пэд» · «аналоговый морфинг» · «пэд медленно растёт» · «бесконечный дрон средний» · «тёплый эволюционирующий пэд» · «пэд дышит и меняется»

### [V5] рейв-стэб-орган-хаус-стэб
- цель: **рейв-стэб/орган-хаус-стэб** · роль: `organ` · src: `rules`
- оси: register:mid, brightness:bright, body:staccato, texture:gritty
- параметры: table=Organ · position=45% · octave=+0 окт · mix_osc1=80% · table=Organ · mix_osc2=55% · mix_noise=5% · lp_cutoff=6000 Гц · amp_attack=4 мс · amp_decay=20 мс · amp_sustain=82% · amp_release=30 мс
- описания (6): «грязный рейв-стэб» · «орган из 90х» · «хаус-аккорд с шероховатостью» · «хаммонд-стэб» · «шершавый орган для рейва» · «рейв-орган в стиле 90х»

### [V5] синк-лид (hard sync)
- цель: **синк-лид (hard sync)** · роль: `saw_lead` · src: `rules`
- оси: register:high, brightness:piercing, filter_motion:gentle_sweep, character:aggressive
- параметры: table=Basic · position=71% · octave=+1 окт · mix_osc1=80% · table=Basic · mix_osc2=70% · mix_noise=0% · lp_cutoff=11000 Гц · amp_attack=10 мс · amp_decay=71 мс · amp_sustain=80% · amp_release=250 мс
- описания (6): «жёсткий синк-лид» · «режущий металлический лид» · «агрессивный синт для рейва» · «высокий sync-лид» · «злой верхний лид» · «суперпила с хардсинком, агрессивная»

### [V5] стакато-стэб-хит-чорд
- цель: **стакато-стэб/хит-чорд** · роль: `pluck` · src: `rules`
- оси: register:mid, brightness:bright, attack:instant, body:staccato
- параметры: table=Basic · position=67% · octave=+0 окт · mix_osc1=85% · table=Basic · mix_osc2=52% · mix_noise=0% · lp_cutoff=6000 Гц · amp_attack=2 мс · amp_decay=400 мс · amp_sustain=0% · amp_release=300 мс
- описания (6): «хит-чорд» · «аккордовый стэб» · «стаккато для акцента» · «отрывистый чорд» · «стаб в стиле даунтемпо» · «короткий аккордовый удар»

### [V5] стеклянный-кристаллический пэд
- цель: **стеклянный/кристаллический пэд** · роль: `glass_pad` · src: `anchor`
- оси: register:high, brightness:bright, movement:wt_morph, space:vast
- параметры: table=Metallic · position=18% · octave=+0 окт · mix_osc1=80% · table=Metallic · mix_osc2=62% · mix_noise=0% · lp_cutoff=4490 Гц · amp_attack=581 мс · amp_decay=280 мс · amp_sustain=93% · amp_release=2.45 с
- описания (6): «хрустальный пэд» · «стеклянный шиммер» · «яркий верхний пэд» · «кристаллический космос» · «ледяной пэд ввысь» · «светлый эволюционирующий шиммер»

### [V5] струнный пэд (ensemble)
- цель: **струнный пэд (ensemble)** · роль: `string` · src: `rules`
- оси: register:mid, brightness:warm, attack:soft, body:long, thickness:unison_thick, space:hall
- параметры: table=Acoustic · position=78% · octave=+0 окт · mix_osc1=80% · table=Acoustic · mix_osc2=0% · mix_noise=0% · lp_cutoff=850 Гц · amp_attack=400 мс · amp_decay=71 мс · amp_sustain=81% · amp_release=350 мс
- описания (6): «тёплый струнный пэд» · «скрипки заполняют зал» · «жирный струнный ансамбль» · «плавные струнные» · «мягкая атака, долгий хвост» · «струнные просторно и тепло»

### [V5] суббас (чистый син)
- цель: **суббас (чистый син)** · роль: `sub_bass` · src: `anchor`
- оси: register:sub, brightness:dark, body:sustained, texture:clean
- параметры: table=Basic · position=0% · octave=-2 окт · mix_osc1=100% · table=Basic · mix_osc2=0% · mix_noise=0% · lp_cutoff=1647 Гц · amp_attack=5 мс · amp_decay=300 мс · amp_sustain=85% · amp_release=150 мс
- описания (6): «чистый суббас» · «глубокий низ» · «тёмный саб» · «808 саб, чистый» · «бас-подложка» · «глухой саб»

### [V5] транс-гейт пэд (ритмичный гейт)
- цель: **транс-гейт пэд (ритмичный гейт)** · роль: `warm_pad` · src: `rules`
- оси: register:mid, brightness:bright, body:sustained, movement:tremolo, space:hall
- параметры: table=Basic · position=35% · octave=+0 окт · mix_osc1=75% · table=Basic · mix_osc2=55% · mix_noise=0% · lp_cutoff=6000 Гц · amp_attack=600 мс · amp_decay=71 мс · amp_sustain=85% · amp_release=2.20 с
- описания (6): «ритмичный гейт-пэд» · «рубленый тёплый пэд» · «транс-гейт пульсирует» · «пэд рубится и держится» · «светлый гейт-пэд» · «зальный рубленый пэд»

### [V5] тёплый аналоговый пэд
- цель: **тёплый аналоговый пэд** · роль: `warm_pad` · src: `rules`
- оси: register:mid, brightness:warm, attack:soft, body:long, space:hall
- параметры: table=Basic · position=35% · octave=+0 окт · mix_osc1=75% · table=Basic · mix_osc2=55% · mix_noise=0% · lp_cutoff=850 Гц · amp_attack=400 мс · amp_decay=71 мс · amp_sustain=85% · amp_release=2.20 с
- описания (6): «тёплый аналоговый пэд» · «мягкая подложка» · «плавный обволакивающий синт» · «длинный тёплый хвост» · «аналоговый пэд в зале» · «подложка с ламповым теплом»

### [V5] формантный-токбокс-лид (гласные)
- цель: **формантный/токбокс-лид (гласные)** · роль: `choir_pad` · src: `rules`
- оси: register:mid, brightness:neutral, vowel:e_mid, body:sustained, movement:wt_morph
- параметры: table=Vocal · position=75% · octave=+0 окт · mix_osc1=80% · table=Vocal · mix_osc2=57% · mix_noise=0% · lp_cutoff=2500 Гц · amp_attack=120 мс · amp_decay=71 мс · amp_sustain=90% · amp_release=800 мс
- описания (6): «токбокс 'э'» · «говорящий синт» · «формантный лид хором» · «протяжная гласная 'э'» · «серединка с вокальным вайбом» · «эволюционирующий вокальный пэд»

### [V5] хардстайл-транс-лид
- цель: **хардстайл/транс-лид** · роль: `saw_lead` · src: `rules`
- оси: register:high, brightness:piercing, texture:distorted
- параметры: table=Basic · position=71% · octave=+1 окт · mix_osc1=80% · table=Basic · mix_osc2=70% · mix_noise=0% · lp_cutoff=11000 Гц · amp_attack=10 мс · amp_decay=71 мс · amp_sustain=80% · amp_release=250 мс
- описания (6): «хардстайл-лид» · «энергичный верхний лид» · «перегруженный транс-лид» · «рейв-лид с дисторшном» · «яркий агрессивный синт» · «суперпила, дисторшн, пронзительная»

### [V5] хаус-органный бас
- цель: **хаус-органный бас** · роль: `organ` · src: `rules`
- оси: register:low, brightness:bright, body:staccato, space:room
- параметры: table=Organ · position=45% · octave=-1 окт · mix_osc1=80% · table=Organ · mix_osc2=55% · mix_noise=4% · lp_cutoff=6000 Гц · amp_attack=4 мс · amp_decay=20 мс · amp_sustain=82% · amp_release=30 мс
- описания (6): «органный бас» · «хаус-орган» · «стаккато орган» · «stab organ» · «хаммонд для хауса» · «упругий церковный бас»

### [V5] хоровой пэд
- цель: **хоровой пэд** · роль: `choir_pad` · src: `rules`
- оси: register:mid, brightness:neutral, vowel:o_round, space:hall
- параметры: table=Vocal · position=25% · octave=+0 окт · mix_osc1=80% · table=Vocal · mix_osc2=57% · mix_noise=0% · lp_cutoff=2500 Гц · amp_attack=120 мс · amp_decay=71 мс · amp_sustain=90% · amp_release=800 мс
- описания (6): «хор поёт 'о'» · «ангельский хор в зале» · «голоса поют 'о'» · «вокальный пэд с 'о'» · «хоровой пэд, нейтральный» · «ахи звучат просторно»

### [V5] чиптюн-лид
- цель: **чиптюн-лид** · роль: `square_lead` · src: `anchor`
- оси: register:high, brightness:bright, movement:vibrato
- параметры: table=Digital · position=15% · octave=+0 окт · mix_osc1=76% · table=Digital · mix_osc2=82% · mix_noise=18% · lp_cutoff=5865 Гц · amp_attack=12 мс · amp_decay=180 мс · amp_sustain=85% · amp_release=95 мс
- описания (6): «чиптюн-лид» · «8-бит пиксельный верх» · «яркий ретро-игровой синт» · «пила, высокий, светлый» · «квадратный лид для 8-битки» · «retro game lead»

### [V5] электроклавишные-keys
- цель: **электроклавишные/keys** · роль: `epiano` · src: `rules`
- оси: register:mid, brightness:neutral, texture:clean, space:room
- параметры: table=Acoustic · position=25% · octave=+0 окт · mix_osc1=80% · table=Acoustic · mix_osc2=70% · mix_noise=0% · lp_cutoff=2500 Гц · amp_attack=4 мс · amp_decay=600 мс · amp_sustain=35% · amp_release=400 мс
- описания (6): «электропиано» · «поп-клавиши» · «синт-podes» · «чистый rhodes» · «сбалансированные клавиши» · «keys для поп-трека»


## texture_atmos (24)

### [V5] ангельский хоровой шиммер-дрон
- цель: **ангельский хоровой шиммер-дрон** · роль: `choir_pad` · src: `rules`
- оси: register:high, brightness:bright, vowel:a_open, movement:wt_morph, space:vast
- параметры: table=Vocal · position=50% · octave=+1 окт · mix_osc1=80% · table=Vocal · mix_osc2=57% · mix_noise=0% · lp_cutoff=6000 Гц · amp_attack=120 мс · amp_decay=71 мс · amp_sustain=90% · amp_release=800 мс
- описания (6): «ангельский хор» · «небесные шиммер-ахи» · «хор с сиянием» · «движущийся вокальный пэд» · «светлый хоровой дрон» · «high angelic choir»

### [V5] бесконечный дрон (низкий)
- цель: **бесконечный дрон (низкий)** · роль: `drone` · src: `anchor`
- оси: register:low, brightness:dark, attack:swell, body:drone, space:vast
- параметры: table=Organ · position=38% · octave=-2 окт · mix_osc1=80% · table=Organ · mix_osc2=59% · mix_noise=5% · lp_cutoff=1200 Гц · amp_attack=2.18 с · amp_decay=5.00 с · amp_sustain=99% · amp_release=4.69 с
- описания (6): «низкий дрон-гул» · «бесконечный космический фон» · «медитативный бас» · «тёмный атмосферный дрон» · «гудящий фон глухо» · «бас для эмбиента»

### [V5] ветер-шумовой бриз
- цель: **ветер/шумовой бриз** · роль: `noise_texture` · src: `anchor`
- оси: register:mid, brightness:neutral, attack:swell, body:drone, space:vast
- параметры: table=Metallic · position=80% · octave=-1 окт · mix_osc1=22% · table=Acoustic · mix_osc2=16% · mix_noise=91% · lp_cutoff=3400 Гц · amp_attack=2.56 с · amp_decay=647 мс · amp_sustain=88% · amp_release=3.14 с
- описания (6): «воздушный бриз» · «мягкий сквозняк» · «ветряной шум» · «бриз для эмбиента» · «среднечастотный ветер» · «бескрайний космический бриз»

### [V5] винил-лента-крэкл (lo-fi нойз)
- цель: **винил/лента-крэкл (lo-fi нойз)** · роль: `noise_texture` · src: `rules`
- оси: register:high, brightness:warm, body:drone, texture:noisy
- параметры: table=Basic · position=80% · octave=+1 окт · mix_osc1=20% · table=Basic · mix_osc2=16% · mix_noise=30% · lp_cutoff=850 Гц · amp_attack=800 мс · amp_decay=71 мс · amp_sustain=90% · amp_release=2.50 с
- описания (6): «виниловое потрескивание» · «пыльная пластинка» · «тёплый ло-фай шум» · «крэкл, ветер, океан» · «верхний шум пластинки» · «мягкое потрескивание винила»

### [V5] гранулярная текстура
- цель: **гранулярная текстура** · роль: `noise_texture` · src: `rules`
- оси: register:mid, brightness:neutral, body:drone, movement:wt_morph, space:hall
- параметры: table=Basic · position=80% · octave=+0 окт · mix_osc1=20% · table=Basic · mix_osc2=16% · mix_noise=91% · lp_cutoff=2500 Гц · amp_attack=800 мс · amp_decay=71 мс · amp_sustain=90% · amp_release=2.50 с
- описания (6): «зернистая текстура» · «гранулярный шум» · «облако крупиц» · «нейтральный дрон» · «эволюционирующий шум» · «просторное зерно»

### [V5] диссонансный хоррор-дрон
- цель: **диссонансный хоррор-дрон** · роль: `drone` · src: `rules`
- оси: register:low, brightness:dark, body:drone, thickness:unison_thick, character:anxious, space:vast
- параметры: table=Basic · position=40% · octave=-1 окт · mix_osc1=78% · table=Basic · mix_osc2=59% · mix_noise=0% · lp_cutoff=400 Гц · amp_attack=1.20 с · amp_decay=71 мс · amp_sustain=100% · amp_release=4.00 с
- описания (6): «тёмный хоррор-дрон» · «зловещий глухой гул» · «саспенс-бас, диссонансный» · «низкий тревожный дрон» · «хоррор, толстый и жирный» · «дрон для саспенса в фильме»

### [V5] дождь-гроза
- цель: **дождь/гроза** · роль: `noise_texture` · src: `rules`
- оси: register:mid, brightness:neutral, body:drone, space:hall
- параметры: table=Basic · position=80% · octave=+0 окт · mix_osc1=20% · table=Basic · mix_osc2=16% · mix_noise=91% · lp_cutoff=2500 Гц · amp_attack=800 мс · amp_decay=71 мс · amp_sustain=90% · amp_release=2.50 с
- описания (6): «ливневый шум» · «дождь стихия» · «просторный дождь» · «серединка дождя» · «зальный ливень» · «шум стихии»

### [V5] индустриальный гул
- цель: **индустриальный гул** · роль: `drone` · src: `rules`
- оси: register:low, brightness:dark, body:drone, texture:distorted, space:hall
- параметры: table=Basic · position=40% · octave=-1 окт · mix_osc1=78% · table=Basic · mix_osc2=59% · mix_noise=0% · lp_cutoff=400 Гц · amp_attack=1.20 с · amp_decay=71 мс · amp_sustain=100% · amp_release=4.00 с
- описания (6): «индустриальный гул» · «ржавый заводской дрон» · «глухой механический низ» · «тёмный зальный фон» · «перегруженный бесконечный гул» · «дрон с ржавым дисторшном»

### [V5] космическая текстура
- цель: **космическая текстура** · роль: `drone` · src: `rules`
- оси: register:mid, brightness:neutral, body:drone, movement:wt_morph, space:vast
- параметры: table=Basic · position=40% · octave=+0 окт · mix_osc1=78% · table=Basic · mix_osc2=59% · mix_noise=0% · lp_cutoff=2500 Гц · amp_attack=1.20 с · amp_decay=71 мс · amp_sustain=100% · amp_release=4.00 с
- описания (6): «космическая текстура» · «sci-fi эмбиент-фон» · «средний регистр как космос» · «нейтральный космический дрон» · «атмосфера глубокого космоса» · «cosmic ambient texture»

### [V5] ледяной-арктический эмбиент
- цель: **ледяной/арктический эмбиент** · роль: `glass_pad` · src: `rules`
- оси: register:high, brightness:bright, body:drone, character:cold_metallic, space:vast
- параметры: table=Metallic · position=20% · octave=+1 окт · mix_osc1=75% · table=Metallic · mix_osc2=62% · mix_noise=0% · lp_cutoff=6000 Гц · amp_attack=500 мс · amp_decay=71 мс · amp_sustain=80% · amp_release=2.50 с
- описания (6): «ледяной пэд» · «арктический стеклянный пэд» · «кристаллический шиммер» · «морозный верхний дрон» · «холодный стеклянный эмбиент» · «icy glass pad»

### [V5] медленно открывающийся пэд-наплыв
- цель: **медленно открывающийся пэд-наплыв** · роль: `warm_pad` · src: `rules`
- оси: register:mid, brightness:warm, attack:swell, body:drone, space:vast
- параметры: table=Basic · position=35% · octave=+0 окт · mix_osc1=75% · table=Basic · mix_osc2=55% · mix_noise=0% · lp_cutoff=850 Гц · amp_attack=1.50 с · amp_decay=71 мс · amp_sustain=85% · amp_release=2.20 с
- описания (6): «мягкий пэд-наплыв» · «вырастающий свелл» · «плавный тёплый вход» · «пэд медленно открывается» · «аналоговый наплыв, тёплый» · «подложка со свеллом»

### [V5] металлический резонансный дрон
- цель: **металлический резонансный дрон** · роль: `drone` · src: `rules`
- оси: register:low, brightness:neutral, body:drone, texture:gritty, space:vast
- параметры: table=Basic · position=40% · octave=-1 окт · mix_osc1=78% · table=Basic · mix_osc2=59% · mix_noise=5% · lp_cutoff=2500 Гц · amp_attack=1.20 с · amp_decay=71 мс · amp_sustain=100% · amp_release=4.00 с
- описания (6): «металлический индустриальный гул» · «грязный резонанс-фон» · «шершавый холодный дрон» · «резонансный низ для эмбиента» · «дрон, гулкий, шершавый» · «индустриальный фон серединка»

### [V5] мрачный подвальный гул
- цель: **мрачный подвальный гул** · роль: `drone` · src: `rules`
- оси: register:sub, brightness:dark, body:drone, character:anxious, space:vast
- параметры: table=Basic · position=40% · octave=-2 окт · mix_osc1=78% · table=Basic · mix_osc2=59% · mix_noise=0% · lp_cutoff=400 Гц · amp_attack=1.20 с · amp_decay=71 мс · amp_sustain=100% · amp_release=4.00 с
- описания (6): «мрачный подвальный дрон» · «зловещий низкий гул» · «подземелье, суббас, бескрайний» · «тревожный глухой фон» · «космический подвал» · «дрон из тёмных глубин»

### [V5] океан-волны (шум прибоя)
- цель: **океан/волны (шум прибоя)** · роль: `noise_texture` · src: `rules`
- оси: register:low, brightness:warm, attack:swell, body:drone, movement:tremolo, space:vast
- параметры: table=Basic · position=80% · octave=-1 окт · mix_osc1=20% · table=Basic · mix_osc2=16% · mix_noise=91% · lp_cutoff=850 Гц · amp_attack=1.50 с · amp_decay=71 мс · amp_sustain=90% · amp_release=2.50 с
- описания (6): «пульсирующий прибой» · «тёплые волны» · «морской дрон с тремоло» · «басовый прибой» · «тёплый океанский шум» · «пульсирующее море»

### [V5] подводная текстура
- цель: **подводная текстура** · роль: `noise_texture` · src: `rules`
- оси: register:low, brightness:dark, body:drone, movement:filter_wobble, space:vast
- параметры: table=Basic · position=80% · octave=-1 окт · mix_osc1=20% · table=Basic · mix_osc2=16% · mix_noise=91% · lp_cutoff=400 Гц · amp_attack=800 мс · amp_decay=71 мс · amp_sustain=90% · amp_release=2.50 с
- описания (6): «подводный вобл» · «глухое погружение» · «басовый воббл» · «толща воды» · «глухой подводный шум» · «тёмный вобл»

### [V5] пульсирующая ритмичная текстура (гейт-чоппер)
- цель: **пульсирующая ритмичная текстура (гейт/чоппер)** · роль: `warm_pad` · src: `rules`
- оси: register:mid, brightness:neutral, body:drone, movement:tremolo, space:hall
- параметры: table=Basic · position=35% · octave=+0 окт · mix_osc1=75% · table=Basic · mix_osc2=55% · mix_noise=0% · lp_cutoff=2500 Гц · amp_attack=600 мс · amp_decay=71 мс · amp_sustain=85% · amp_release=2.20 с
- описания (6): «тёплый чоппер» · «пульсирующий пэд» · «ритмичный рубленый фон» · «зальный пэд с гейтом» · «аналоговая пульсация, ровная» · «серединка, нейтрально»

### [V5] радиопомехи-статика
- цель: **радиопомехи/статика** · роль: `noise_texture` · src: `rules`
- оси: register:high, brightness:bright, body:drone, texture:noisy
- параметры: table=Basic · position=80% · octave=+1 окт · mix_osc1=20% · table=Basic · mix_osc2=16% · mix_noise=30% · lp_cutoff=6000 Гц · amp_attack=800 мс · amp_decay=71 мс · amp_sustain=90% · amp_release=2.50 с
- описания (6): «радиостатика» · «яркий эфирный треск» · «белый шум с придыханием» · «высокий шум, ветер» · «статика, светлый верх» · «треск эфира, яркий»

### [V5] реверс-шиммер свелл
- цель: **реверс-шиммер свелл** · роль: `glass_pad` · src: `rules`
- оси: register:high, brightness:bright, attack:swell, movement:wt_morph, space:vast
- параметры: table=Metallic · position=20% · octave=+1 окт · mix_osc1=75% · table=Metallic · mix_osc2=62% · mix_noise=0% · lp_cutoff=6000 Гц · amp_attack=500 мс · amp_decay=71 мс · amp_sustain=80% · amp_release=2.50 с
- описания (6): «реверс-шиммер свелл» · «втягивающийся стеклянный пэд» · «обратный шиммер» · «стеклянный наплыв» · «кристаллический свелл» · «выммер в космосе»

### [V5] рой насекомых-живой органик
- цель: **рой насекомых/живой органик** · роль: `noise_texture` · src: `rules`
- оси: register:high, brightness:bright, body:drone, movement:tremolo, texture:noisy
- параметры: table=Basic · position=80% · octave=+1 окт · mix_osc1=20% · table=Basic · mix_osc2=16% · mix_noise=30% · lp_cutoff=6000 Гц · amp_attack=800 мс · amp_decay=71 мс · amp_sustain=90% · amp_release=2.50 с
- описания (6): «рой насекомых» · «пульсирующий стрёкот» · «живой органический шум» · «яркое стрекотание роя» · «тремоло природы» · «стрёкот, светлый, живой»

### [V5] светлый воздушный амбиент-пэд
- цель: **светлый воздушный амбиент-пэд** · роль: `warm_pad` · src: `rules`
- оси: register:high, brightness:bright, attack:swell, body:drone, space:vast
- параметры: table=Basic · position=35% · octave=+1 окт · mix_osc1=75% · table=Basic · mix_osc2=55% · mix_noise=0% · lp_cutoff=6000 Гц · amp_attack=1.50 с · amp_decay=71 мс · amp_sustain=85% · amp_release=2.20 с
- описания (6): «светлый воздушный пэд» · «парящий эмбиент-пэд» · «невесомый верхний регистр» · «пэд для наплыва» · «яркий аналоговый пэд» · «light ambient pad»

### [V5] сновидческая дымка
- цель: **сновидческая дымка** · роль: `warm_pad` · src: `rules`
- оси: register:mid, brightness:warm, attack:swell, body:drone, character:dreamy, space:vast
- параметры: table=Basic · position=35% · octave=+0 окт · mix_osc1=75% · table=Basic · mix_osc2=55% · mix_noise=0% · lp_cutoff=850 Гц · amp_attack=1.50 с · amp_decay=71 мс · amp_sustain=85% · amp_release=2.20 с
- описания (6): «тёплый пэд» · «мечтательный туман» · «аналоговая дымка» · «мягкий сновидческий пэд» · «размытый тёплый дрон» · «пэд как сон, медленно вырастает из тишины»

### [V5] стеклянный шиммер
- цель: **стеклянный шиммер** · роль: `glass_pad` · src: `rules`
- оси: register:high, brightness:piercing, movement:wt_morph, space:vast
- параметры: table=Metallic · position=20% · octave=+1 окт · mix_osc1=75% · table=Metallic · mix_osc2=62% · mix_noise=0% · lp_cutoff=11000 Гц · amp_attack=500 мс · amp_decay=71 мс · amp_sustain=80% · amp_release=2.50 с
- описания (6): «стеклянный шиммер» · «хрустальное мерцание» · «блестящий верхний пэд» · «кристаллический пэд» · «переливы стекла» · «высокий эволюционирующий шиммер»

### [V5] формантная вокальная текстура (движение гласных)
- цель: **формантная вокальная текстура (движение гласных)** · роль: `choir_pad` · src: `rules`
- оси: register:mid, brightness:neutral, vowel:u_dark, movement:wt_morph, space:hall
- параметры: table=Vocal · position=0% · octave=+0 окт · mix_osc1=80% · table=Vocal · mix_osc2=57% · mix_noise=0% · lp_cutoff=2500 Гц · amp_attack=120 мс · amp_decay=71 мс · amp_sustain=90% · amp_release=800 мс
- описания (6): «пропевание на у» · «хоровой вокальный пэд» · «поющий пэд среднего регистра» · «у-гласная в хоре» · «движущийся вокальный морф» · «зальный вокальный пэд с эхом»

### [V5] шёпот-придыхание
- цель: **шёпот/придыхание** · роль: `noise_texture` · src: `rules`
- оси: register:mid, brightness:neutral, attack:soft, body:drone, space:hall
- параметры: table=Basic · position=80% · octave=+0 окт · mix_osc1=20% · table=Basic · mix_osc2=16% · mix_noise=91% · lp_cutoff=2500 Гц · amp_attack=400 мс · amp_decay=71 мс · amp_sustain=90% · amp_release=2.50 с
- описания (6): «бесконечный шёпот» · «мягкое придыхание» · «океанский шум» · «дышащий пэд» · «плавное придыхание, нет атаки» · «зальный шёпот»


## percussive_fx (24)

### [V5] DTMF-телефонные тоны
- цель: **DTMF/телефонные тоны** · роль: `digital_fx` · src: `rules`
- оси: register:mid, brightness:neutral, body:sustained, texture:clean
- параметры: table=Digital · position=0% · octave=+0 окт · mix_osc1=80% · table=Digital · mix_osc2=0% · mix_noise=0% · lp_cutoff=2500 Гц · amp_attack=1 мс · amp_decay=300 мс · amp_sustain=80% · amp_release=450 мс
- описания (6): «DTMF тон» · «телефонный набор» · «пищащий тон» · «чистый телефонный звук» · «набор номера» · «нейтральный цифровой тон»

### [V5] UI-boot-звук интерфейса
- цель: **UI/boot-звук интерфейса** · роль: `digital_fx` · src: `rules`
- оси: register:high, brightness:bright, attack:fast, body:pluck, texture:clean
- параметры: table=Digital · position=0% · octave=+1 окт · mix_osc1=80% · table=Digital · mix_osc2=0% · mix_noise=0% · lp_cutoff=6000 Гц · amp_attack=12 мс · amp_decay=500 мс · amp_sustain=0% · amp_release=300 мс
- описания (6): «ui-блип интерфейса» · «звук загрузки» · «чистый ui-щипок» · «boot-звук блип» · «гладкий пик высокий» · «уведомление блип»

### [V5] downlifter (нисходящий свип)
- цель: **downlifter (нисходящий свип)** · роль: `riser_fx` · src: `rules`
- оси: register:mid, brightness:neutral, filter_motion:strong_sweep, space:hall
- параметры: table=Digital · position=85% · octave=+0 окт · mix_osc1=70% · table=Digital · mix_osc2=67% · mix_noise=86% · lp_cutoff=2500 Гц · amp_attack=1.50 с · amp_decay=71 мс · amp_sustain=90% · amp_release=300 мс
- описания (6): «нисходящий свип» · «райзер вниз» · «зальный downlifter» · «просторный свипующий переход» · «среднечастотный спуск» · «свип, зальный, просторный»

### [V5] whoosh-transition
- цель: **whoosh/transition** · роль: `noise_texture` · src: `rules`
- оси: register:mid, brightness:neutral, attack:swell, filter_motion:strong_sweep, space:hall
- параметры: table=Basic · position=80% · octave=+0 окт · mix_osc1=20% · table=Basic · mix_osc2=16% · mix_noise=91% · lp_cutoff=2500 Гц · amp_attack=1.50 с · amp_decay=71 мс · amp_sustain=90% · amp_release=2.50 с
- описания (6): «whoosh переход» · «зальный вууш» · «просвист» · «ветряной переход» · «просторный шумовой свип» · «whoosh, ветер, океан»

### [V5] взлёт-ризер (медленный подъём)
- цель: **взлёт/ризер (медленный подъём)** · роль: `riser_fx` · src: `anchor`
- оси: register:high, brightness:bright, attack:swell, filter_motion:strong_sweep, space:hall
- параметры: table=Digital · position=85% · octave=+0 окт · mix_osc1=71% · table=Digital · mix_osc2=67% · mix_noise=86% · lp_cutoff=206 Гц · amp_attack=4.06 с · amp_decay=100 мс · amp_sustain=100% · amp_release=234 мс
- описания (6): «ризер нарастающий» · «взлёт вверх» · «райзер просторный» · «наплыв светлый» · «riser для перехода» · «зальный свип»

### [V5] глитч-артефакт
- цель: **глитч/артефакт** · роль: `digital_fx` · src: `anchor`
- оси: register:high, brightness:bright, attack:instant, body:staccato, texture:distorted
- параметры: table=Digital · position=86% · octave=+0 окт · mix_osc1=84% · table=Digital · mix_osc2=81% · mix_noise=21% · lp_cutoff=12000 Гц · amp_attack=0 мс · amp_decay=1.45 с · amp_sustain=0% · amp_release=1.52 с
- описания (6): «глитч-лазер» · «высокий цифровой сбой» · «артефакт данных» · «дребезг данных» · «яркий глитч» · «цифровой сбой, верх»

### [V5] каменный-металлический клац
- цель: **каменный/металлический клац** · роль: `mallet` · src: `rules`
- оси: register:mid, brightness:bright, attack:instant, body:staccato, texture:gritty
- параметры: table=Metallic · position=15% · octave=+0 окт · mix_osc1=85% · table=Metallic · mix_osc2=67% · mix_noise=5% · lp_cutoff=6000 Гц · amp_attack=1 мс · amp_decay=120 мс · amp_sustain=0% · amp_release=80 мс
- описания (6): «каменный клац» · «сухой щелчок маримбы» · «ксилофон с грязью» · «шершавый металлический удар» · «отрывистый калимба-клац» · «стук камня по металлу»

### [V5] карильон-курантовый удар
- цель: **карильон/курантовый удар** · роль: `bell` · src: `rules`
- оси: register:high, brightness:bright, body:long, space:hall
- параметры: table=Metallic · position=10% · octave=+1 окт · mix_osc1=85% · table=Metallic · mix_osc2=0% · mix_noise=0% · lp_cutoff=6000 Гц · amp_attack=1 мс · amp_decay=400 мс · amp_sustain=2% · amp_release=2.50 с
- описания (6): «башенный перезвон» · «яркий курант» · «карильон в просторном зале» · «высокий звон с долгим хвостом» · «светлый колокольный удар» · «колокол, высокий, зальный»

### [V5] клаве-деревянный клик
- цель: **клаве/деревянный клик** · роль: `mallet` · src: `rules`
- оси: register:high, brightness:bright, attack:instant, body:staccato, texture:clean
- параметры: table=Acoustic · position=15% · octave=+1 окт · mix_osc1=85% · table=Acoustic · mix_osc2=67% · mix_noise=0% · lp_cutoff=6000 Гц · amp_attack=1 мс · amp_decay=120 мс · amp_sustain=0% · amp_release=80 мс
- описания (6): «клаве» · «деревянный клик» · «маримба» · «яркий щелчок» · «сухой тук» · «ксилофон»

### [V5] колокол (длинный затухающий)
- цель: **колокол (длинный затухающий)** · роль: `bell` · src: `rules`
- оси: register:mid, brightness:bright, body:long, space:hall
- параметры: table=Metallic · position=10% · octave=+0 окт · mix_osc1=85% · table=Metallic · mix_osc2=0% · mix_noise=0% · lp_cutoff=6000 Гц · amp_attack=1 мс · amp_decay=400 мс · amp_sustain=2% · amp_release=2.50 с
- описания (6): «длинный колокол» · «затухающий церковный звон» · «яркий колокольчик» · «длинный светлый звон» · «колокол в зале» · «глокеншпиль с хвостом»

### [V5] колокольчик-стик (короткий)
- цель: **колокольчик-стик (короткий)** · роль: `bell` · src: `rules`
- оси: register:very_high, brightness:bright, body:pluck, space:room
- параметры: table=Metallic · position=10% · octave=+2 окт · mix_osc1=85% · table=Metallic · mix_osc2=0% · mix_noise=0% · lp_cutoff=6000 Гц · amp_attack=1 мс · amp_decay=500 мс · amp_sustain=0% · amp_release=300 мс
- описания (6): «колокольчик-стик» · «короткий дзинь» · «высокий звоночек с эхом» · «щипковый глокеншпиль» · «комнатный дзинь» · «яркий колокольчик»

### [V5] лазер-sci-fi свип (фильтр-свип - LFO)
- цель: **лазер/sci-fi свип (фильтр-свип / LFO)** · роль: `digital_fx` · src: `rules`
- оси: register:high, brightness:piercing, filter_motion:strong_sweep, body:staccato
- параметры: table=Digital · position=0% · octave=+1 окт · mix_osc1=80% · table=Digital · mix_osc2=0% · mix_noise=0% · lp_cutoff=11000 Гц · amp_attack=1 мс · amp_decay=120 мс · amp_sustain=0% · amp_release=80 мс
- описания (6): «лазер-бластер» · «sci-fi свип» · «лазерный выстрел» · «космический бластер» · «лазер распахивается» · «высокий лазерный свип»

### [V5] металлический удар-анвил
- цель: **металлический удар/анвил** · роль: `gong` · src: `rules`
- оси: register:mid, brightness:bright, body:pluck, texture:gritty
- параметры: table=Metallic · position=0% · octave=+0 окт · mix_osc1=85% · table=Metallic · mix_osc2=81% · mix_noise=5% · lp_cutoff=6000 Гц · amp_attack=1 мс · amp_decay=500 мс · amp_sustain=0% · amp_release=300 мс
- описания (6): «наковальня» · «кузнечный удар» · «грязный анвил» · «серединка металл» · «шершавый кузнечный звон» · «анвил, щипковый, затухающий»

### [V5] перевёрнутый-реверс-наплыв (имитация long attack)
- цель: **перевёрнутый/реверс-наплыв (имитация long attack)** · роль: `warm_pad` · src: `rules`
- оси: register:mid, brightness:neutral, attack:swell, body:pluck, space:hall
- параметры: table=Basic · position=35% · octave=+0 окт · mix_osc1=75% · table=Basic · mix_osc2=55% · mix_noise=0% · lp_cutoff=2500 Гц · amp_attack=1.50 с · amp_decay=71 мс · amp_sustain=85% · amp_release=2.20 с
- описания (6): «тёплый реверс-пэд» · «обратный наплыв, серединка» · «мягкий аналоговый пэд с наплывом» · «перевёрнутая подложка, нейтрально» · «реверс-втягивание, пэд» · «пэд-подложка, тёплый, зальный»

### [V5] поющая чаша (singing bowl)
- цель: **поющая чаша (singing bowl)** · роль: `gong` · src: `rules`
- оси: register:mid, brightness:warm, body:long, movement:tremolo, space:hall
- параметры: table=Metallic · position=0% · octave=+0 окт · mix_osc1=85% · table=Metallic · mix_osc2=81% · mix_noise=27% · lp_cutoff=850 Гц · amp_attack=1 мс · amp_decay=400 мс · amp_sustain=2% · amp_release=2.50 с
- описания (6): «поющая чаша» · «тибетская чаша с обертонами» · «медитативный обертоновый гул» · «чаша пульсирует» · «тёплый звон поющей чаши» · «обертоны тибетской чаши»

### [V5] ретро-аркадный sfx
- цель: **ретро-аркадный sfx** · роль: `digital_fx` · src: `rules`
- оси: register:high, brightness:bright, attack:instant, body:pluck
- параметры: table=Digital · position=0% · octave=+1 окт · mix_osc1=80% · table=Digital · mix_osc2=0% · mix_noise=0% · lp_cutoff=6000 Гц · amp_attack=1 мс · amp_decay=500 мс · amp_sustain=0% · amp_release=300 мс
- описания (6): «ретро 8-бит блип» · «пиксельный звук игры» · «аркадный sfx» · «чиптюн блип» · «игра блип старый» · «пиксельный ui»

### [V5] саб-дроп импакт
- цель: **саб-дроп импакт** · роль: `kick` · src: `rules`
- оси: register:sub, brightness:dark, attack:instant, body:long, texture:saturated
- параметры: table=Basic · position=0% · octave=-2 окт · mix_osc1=80% · table=Basic · mix_osc2=22% · mix_noise=0% · lp_cutoff=400 Гц · amp_attack=1 мс · amp_decay=250 мс · amp_sustain=0% · amp_release=100 мс
- описания (6): «808 кик» · «саб-дроп удар» · «тёмный насыщенный кик» · «длинный саб» · «бас-удар с глубиной» · «подогретый 808»

### [V5] спарк-электроразряд
- цель: **спарк/электроразряд** · роль: `digital_fx` · src: `rules`
- оси: register:high, brightness:piercing, attack:instant, body:staccato, texture:noisy
- параметры: table=Digital · position=0% · octave=+1 окт · mix_osc1=80% · table=Digital · mix_osc2=0% · mix_noise=30% · lp_cutoff=11000 Гц · amp_attack=1 мс · amp_decay=120 мс · amp_sustain=0% · amp_release=80 мс
- описания (6): «искра электрическая» · «спарк-эффект глитч» · «треск тока в воздухе» · «высокий щелчок-искра» · «цифровой разряд, верх» · «отрывистая искра с шумом»

### [V5] стеклянная капля воды
- цель: **стеклянная капля воды** · роль: `bell` · src: `rules`
- оси: register:very_high, brightness:bright, attack:instant, body:pluck, space:room
- параметры: table=Metallic · position=10% · octave=+2 окт · mix_osc1=85% · table=Metallic · mix_osc2=0% · mix_noise=0% · lp_cutoff=6000 Гц · amp_attack=1 мс · amp_decay=500 мс · amp_sustain=0% · amp_release=300 мс
- описания (6): «стеклянная капля» · «высокая капля воды» · «бульк колокольчика» · «яркий звоночек» · «пронзительная капля» · «отрывистая капля, светлая»

### [V5] треугольник
- цель: **треугольник** · роль: `bell` · src: `rules`
- оси: register:very_high, brightness:piercing, body:long, space:room
- параметры: table=Metallic · position=10% · octave=+2 окт · mix_osc1=85% · table=Metallic · mix_osc2=0% · mix_noise=0% · lp_cutoff=11000 Гц · amp_attack=1 мс · amp_decay=400 мс · amp_sustain=2% · amp_release=2.50 с
- описания (6): «треугольник» · «тонкий тинь» · «пронзительный треугольник» · «металлический звон в комнате» · «высокий треугольник с эхом» · «оркестровый тинь»

### [V5] удар-импакт (тёмный)
- цель: **удар/импакт (тёмный)** · роль: `gong` · src: `rules`
- оси: register:low, brightness:dark, attack:instant, body:long, texture:distorted, space:hall
- параметры: table=Metallic · position=0% · octave=-1 окт · mix_osc1=85% · table=Metallic · mix_osc2=81% · mix_noise=0% · lp_cutoff=400 Гц · amp_attack=1 мс · amp_decay=400 мс · amp_sustain=2% · amp_release=2.50 с
- описания (6): «тёмный импакт» · «басовый гонг» · «кинематографичный удар» · «глухой дисторшн-удар» · «длинный тёмный хвост» · «импакт с перегрузом»

### [V5] храмовый гонг
- цель: **храмовый гонг** · роль: `gong` · src: `anchor`
- оси: register:low, brightness:neutral, body:long, space:hall
- параметры: table=Metallic · position=0% · octave=-2 окт · mix_osc1=78% · table=Metallic · mix_osc2=81% · mix_noise=27% · lp_cutoff=1771 Гц · amp_attack=15 мс · amp_decay=5.00 с · amp_sustain=0% · amp_release=3.90 с
- описания (6): «храмовый гонг» · «басовый металлический гонг» · «ракетный удар в зале» · «низкий гонг с хвостом» · «ритуальный металлический удар» · «гонг, низко, долго»

### [V5] хрустальный звон
- цель: **хрустальный звон** · роль: `bell` · src: `rules`
- оси: register:very_high, brightness:piercing, body:long, space:hall
- параметры: table=Metallic · position=10% · octave=+2 окт · mix_osc1=85% · table=Metallic · mix_osc2=0% · mix_noise=0% · lp_cutoff=11000 Гц · amp_attack=1 мс · amp_decay=400 мс · amp_sustain=2% · amp_release=2.50 с
- описания (6): «хрустальный звон» · «ледяной перезвон» · «магический стеклянный звон» · «пронзительный хрусталь» · «звенящее стекло в зале» · «магический верхний звон»

### [V5] цифровой бит-краш стэб
- цель: **цифровой бит-краш стэб** · роль: `digital_fx` · src: `rules`
- оси: register:mid, brightness:bright, attack:instant, body:staccato, texture:distorted
- параметры: table=Digital · position=0% · octave=+0 окт · mix_osc1=80% · table=Digital · mix_osc2=0% · mix_noise=0% · lp_cutoff=6000 Гц · amp_attack=1 мс · amp_decay=120 мс · amp_sustain=0% · amp_release=80 мс
- описания (6): «глитч-краш» · «грязный пиксель-удар» · «цифровой стэб с дисторшном» · «крашенный бит-краш» · «пиксельный стаккато» · «бит-краш для чиптюна»


## drums (14)

### [V5] каубел (металлический)
- цель: **каубел (металлический)** · роль: `mallet` · src: `rules`
- оси: register:high, brightness:bright, attack:instant, body:staccato, texture:gritty
- параметры: table=Metallic · position=15% · octave=+1 окт · mix_osc1=85% · table=Metallic · mix_osc2=67% · mix_noise=5% · lp_cutoff=6000 Гц · amp_attack=1 мс · amp_decay=120 мс · amp_sustain=0% · amp_release=80 мс
- описания (6): «каубел» · «коровий колокольчик» · «металлический каубел» · «латинский каубел, яркий» · «калимба-каубел» · «высокий металлический тук»

### [V5] клэп
- цель: **клэп** · роль: `snare_clap` · src: `anchor`
- оси: register:mid, brightness:bright, attack:instant, body:staccato, texture:noisy, space:room
- параметры: table=Basic · position=8% · octave=-2 окт · mix_osc1=29% · table=Basic · mix_osc2=25% · mix_noise=98% · lp_cutoff=1200 Гц · amp_attack=0 мс · amp_decay=180 мс · amp_sustain=0% · amp_release=80 мс
- описания (6): «клэп, светлый» · «808-клэп, яркий» · «хлопок с эхом» · «рукоплескание, комнатное» · «снэр-клэп, светлый» · «клэп, с придыханием»

### [V5] конга-бонго (тон-перкуссия)
- цель: **конга/бонго (тон-перкуссия)** · роль: `tom` · src: `rules`
- оси: register:mid, brightness:warm, attack:instant, body:pluck
- параметры: table=Basic · position=20% · octave=+0 окт · mix_osc1=88% · table=Basic · mix_osc2=65% · mix_noise=8% · lp_cutoff=850 Гц · amp_attack=1 мс · amp_decay=500 мс · amp_sustain=0% · amp_release=300 мс
- описания (6): «тёплая конга» · «мягкий бонго» · «серединка литавра» · «настроенный том» · «щёлочек конга» · «конга для латины»

### [V5] крэш-райд (металл+нойз)
- цель: **крэш/райд (металл+нойз)** · роль: `cymbal` · src: `anchor`
- оси: register:very_high, brightness:piercing, attack:instant, body:long, texture:noisy, space:room
- параметры: table=Metallic · position=20% · octave=+0 окт · mix_osc1=86% · table=Basic · mix_osc2=0% · mix_noise=48% · lp_cutoff=9448 Гц · amp_attack=1 мс · amp_decay=651 мс · amp_sustain=0% · amp_release=544 мс
- описания (6): «крэш тарелка» · «длинный райд» · «разлив металла» · «пронзительный хвост крэша» · «шипящий хай-хэт» · «хвостатый райд»

### [V5] пальцевый щелчок-snap
- цель: **пальцевый щелчок/snap** · роль: `snare_clap` · src: `rules`
- оси: register:mid, brightness:bright, attack:instant, body:staccato, texture:noisy, space:dry
- параметры: table=Basic · position=14% · octave=+0 окт · mix_osc1=50% · table=Basic · mix_osc2=13% · mix_noise=30% · lp_cutoff=6000 Гц · amp_attack=1 мс · amp_decay=200 мс · amp_sustain=0% · amp_release=150 мс
- описания (6): «щелчок пальцами» · «snap сухой» · «пальцевый клик» · «отрывистый снэр» · «яркий щелчок» · «сухой акцент»

### [V5] рим-шот-клик
- цель: **рим-шот/клик** · роль: `snare_clap` · src: `rules`
- оси: register:high, brightness:bright, attack:instant, body:staccato, texture:noisy
- параметры: table=Basic · position=14% · octave=+1 окт · mix_osc1=50% · table=Basic · mix_osc2=13% · mix_noise=30% · lp_cutoff=6000 Гц · amp_attack=1 мс · amp_decay=200 мс · amp_sustain=0% · amp_release=150 мс
- описания (6): «рим-шот» · «яркий клик по ободу» · «снэр-клик светлый» · «сухой рим-шот, звонкий» · «высокий тик снэра» · «рим, пронзительный щелчок»

### [V5] синт-кик (808, сабовый синус)
- цель: **синт-кик (808, сабовый синус)** · роль: `kick` · src: `anchor`
- оси: register:sub, brightness:dark, attack:instant, body:pluck, texture:clean
- параметры: table=Basic · position=0% · octave=-2 окт · mix_osc1=80% · table=Basic · mix_osc2=22% · mix_noise=5% · lp_cutoff=1181 Гц · amp_attack=1 мс · amp_decay=350 мс · amp_sustain=0% · amp_release=304 мс
- описания (6): «808 кик, сабовый» · «глубокий трэп-кик» · «суб-кик, чистый» · «808 бочка, тёмная» · «сабовый синус-кик» · «глубокий кик без хвоста»

### [V5] синт-кик (909, жёсткий)
- цель: **синт-кик (909, жёсткий)** · роль: `kick` · src: `rules`
- оси: register:low, brightness:warm, attack:instant, body:staccato, texture:gritty
- параметры: table=Basic · position=0% · octave=-1 окт · mix_osc1=80% · table=Basic · mix_osc2=22% · mix_noise=5% · lp_cutoff=850 Гц · amp_attack=1 мс · amp_decay=250 мс · amp_sustain=0% · amp_release=100 мс
- описания (6): «909-кик, жёсткий» · «техно-бочка, грязная» · «панчевый кик, тёплый» · «шершавый 909» · «жёсткая бочка для техно» · «909 кик, отрывистый, грязный»

### [V5] снэр (нойз+тон)
- цель: **снэр (нойз+тон)** · роль: `snare_clap` · src: `anchor`
- оси: register:mid, brightness:bright, attack:instant, body:staccato, texture:noisy
- параметры: table=Basic · position=20% · octave=-1 окт · mix_osc1=83% · table=Basic · mix_osc2=0% · mix_noise=100% · lp_cutoff=3307 Гц · amp_attack=0 мс · amp_decay=180 мс · amp_sustain=0% · amp_release=65 мс
- описания (6): «яркий снэр» · «снэр с придыханием» · «малый барабан, светлый» · «шумный снейр, резкий» · «снэр+клэп, серединка» · «отрывистый снэр, яркий»

### [V5] тамбурин
- цель: **тамбурин** · роль: `hihat` · src: `rules`
- оси: register:very_high, brightness:bright, attack:instant, body:pluck, texture:noisy
- параметры: table=Metallic · position=75% · octave=+2 окт · mix_osc1=91% · table=Metallic · mix_osc2=26% · mix_noise=65% · lp_cutoff=6000 Гц · amp_attack=1 мс · amp_decay=500 мс · amp_sustain=0% · amp_release=300 мс
- описания (6): «тамбурин звон» · «яркий бубен» · «джингл тамбурин» · «металлический шорох бубна» · «светлый хай-хэт бубен» · «тарелочка тамбурин»

### [V5] том (настроенный, питч-дроп)
- цель: **том (настроенный, питч-дроп)** · роль: `tom` · src: `anchor`
- оси: register:low, brightness:warm, attack:instant, body:pluck
- параметры: table=Basic · position=14% · octave=-1 окт · mix_osc1=80% · table=Basic · mix_osc2=61% · mix_noise=98% · lp_cutoff=325 Гц · amp_attack=1 мс · amp_decay=519 мс · amp_sustain=0% · amp_release=307 мс
- описания (6): «тёплый том» · «раскатистый том с питч-дропом» · «настроенный том, низкий» · «мягкий том для подложки» · «басовый том с затуханием» · «том, падающий по частоте»

### [V5] хай-хэт закрытый (короткий)
- цель: **хай-хэт закрытый (короткий)** · роль: `hihat` · src: `anchor`
- оси: register:very_high, brightness:piercing, attack:instant, body:staccato, texture:noisy
- параметры: table=Metallic · position=75% · octave=+1 окт · mix_osc1=91% · table=Basic · mix_osc2=26% · mix_noise=33% · lp_cutoff=11000 Гц · amp_attack=0 мс · amp_decay=80 мс · amp_sustain=0% · amp_release=60 мс
- описания (6): «закрытый хэт» · «цыкающий хай-хэт» · «пронзительная тарелочка» · «острый металлический щёлк» · «хай-хэт, короткий, резкий» · «звонкий щетчатый хэт»

### [V5] хай-хэт открытый
- цель: **хай-хэт открытый** · роль: `hihat` · src: `rules`
- оси: register:very_high, brightness:piercing, attack:instant, body:pluck, texture:noisy
- параметры: table=Metallic · position=75% · octave=+2 окт · mix_osc1=91% · table=Metallic · mix_osc2=26% · mix_noise=65% · lp_cutoff=11000 Гц · amp_attack=1 мс · amp_decay=500 мс · amp_sustain=0% · amp_release=300 мс
- описания (6): «открытый хай-хэт» · «шипящий хэт» · «длинный хай-хэт с сибиляцией» · «открытая тарелочка с придыханием» · «хэт, долго затухающий» · «хай-хэт открытый, пронзительный»

### [V5] шейкер-маракас (нойз)
- цель: **шейкер/маракас (нойз)** · роль: `hihat` · src: `rules`
- оси: register:very_high, brightness:bright, attack:fast, body:staccato, texture:noisy
- параметры: table=Metallic · position=75% · octave=+2 окт · mix_osc1=91% · table=Metallic · mix_osc2=26% · mix_noise=65% · lp_cutoff=6000 Гц · amp_attack=1 мс · amp_decay=120 мс · amp_sustain=0% · amp_release=80 мс
- описания (6): «шейкер с песком» · «яркий маракас» · «маракас хай-хэт» · «звонкий шуршащий звук» · «лёгкий шейкер для хай-хэта» · «пронзительный шейкер»
