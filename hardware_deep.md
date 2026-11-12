# Hardware deep-dive: `PWM_DIM` i wentylatory

← [Powrót do README](README.md)

Notatki projektowe, nie instrukcja „zrób tak i będzie działać". Wszystko poniżej
zakłada, że **najpierw zmierzymy**, co faktycznie siedzi na `PWM_DIM` i na
przetwornicach `FAN0` / `FAN1` — bo od tego zależy cała reszta. Wartości elementów
są przykładowe; podstaw swoje.

## 0. Mapa płyt i etykiet (odczyt ze zdjęć)

Zanim cokolwiek zmierzysz, warto wiedzieć, co jest czym. Poniżej tylko to, co da się
odczytać z silkscreenu na zdjęciach — **to nadal hipotezy, nie schemat**. Poziom
pewności zaznaczony przy każdej pozycji.

W środku są dwie płytki, które łatwo pomylić:

| Płytka | Oznaczenie | Rola |
| --- | --- | --- |
| Główna | `OD.P.CRED16PRO.MT9269 (N)`, `CQC P157 2338-1`, `UL 94V-0 BLD-B E203840` | SoC, DDR3L, eMMC, audio, złącza LED i wentylatorów, USB, IR |
| Sterownik LED | `OD.P.SCSD36.LED`, `B22322`, `P184 2325-2` | dwa tory LED (`LED1±`, `LED2±`) z pętlą prądową |

### 0.1 Tor LED — driver nie siedzi na płycie głównej

`PWM_DIM` z płyty głównej **nie steruje diodą bezpośrednio**. Przez taśmę idzie do
osobnej płytki sterownika razem z `VBL` (zasilanie) i parą `NTC_OUT1` / `NTC_GND1`.

Na płytce sterownika są: `PWM` / `PWM_DIM1` (wejście jasności), `VBL+` ×4 (zasilanie),
`LED1+`, `LED1-`, `LED2+`, `LED2-` oraz pętla pomiarowa `LED_FB1…LED_FB3` — czyli
sterownik jest **prądowy**, a nie napięciowy. Wypełnienie PWM na `DIM` ustawia prąd
diody, nie jej napięcie.

Wniosek praktyczny: PWM z ESP wchodzi w gotową pętlę prądową. To dobrze (nie ruszamy
toru mocy) i to źle (nie przeskoczysz fabrycznego minimum/maksimum prądu — sterownik
ma swoje limity i próg odcięcia).

**Uwaga na NTC.** `NTC1` leży na tej samej taśmie co `VBL` i `PWM_DIM`, więc prawie
na pewno mierzy temperaturę diody/radiatora i jest częścią zabezpieczenia sterownika.
Po odpięciu go sterownik może wejść w protection i zgasić LED.
*[pewne: etykiety; prawdopodobne: rola `NTC1`]*

### 0.2 Wentylatory — jest tacho

Przy złączach widać cztery rzeczy, nie dwie:

```
JFA0 / FAN0      FAN_FG0 / 12V-FAN
JFA1 / FAN1      FAN_FG2 / 12V/FAN1
JFA2 / FAN2      FAN_FG1 / 12V-FAN
```

`FG` to standardowo tachometr wentylatora (open-collector, typowo 2 impulsy na obrót).
Każdy wentylator ma też **własną przetwornicę**: induktor `2R2` (2,2 µH) + układ w SOP-8
(`UD8` / `UD9`), czyli 12 V → 7 V / 10 V.

Dwa wnioski:

- obroty da się **czytać** bez dodatkowego sprzętu — Tasmota ma `Counter`,
- skoro jest tacho, pętla może być zamknięta: mierzysz RPM i dopiero potem ruszasz FB.

Płyta przewiduje też trzeci wentylator (`JFA2` / `FAN2`) — nie wiem, czy w tej wersji
jest obsadzony. Uwaga: numeracja `FG` nie idzie parami z `FAN` (`FAN1` → `FAN_FG2`,
`FAN2` → `FAN_FG1`) — tak to wygląda na zdjęciu, więc przed podłączeniem `Counter`
sprawdź, który pad faktycznie daje impulsy. *[pewne: etykiety i `2R2`; prawdopodobne: `FG` = tacho]*

### 0.3 Zasilanie i przycisk

- `12V` wchodzi z zasilacza zewnętrznego, a `5V_STB` to szyna standby — czyli jest
  również wtedy, gdy projektor „śpi”. Dobre miejsce na zasilenie ESP, żeby było
  osiągalne bez włączania projektora. **Sprawdź multimetrem**, czy naprawdę nie znika.
- `SYS_PWR` / `SYS_PWR1` to dwa pady w sekcji przycisku, obok `复位开关` (reset).
  Wyglądają na wyprowadzenie przycisku zasilania — jeśli tak, to właśnie tam należy
  równolegle wpiąć przekaźnik z `POWER2`, a nie w dowolne miejsce na płycie.
- Pozostałe szyny widoczne na zdjęciach: `DDR_1.8V`, `VCC_1.8V`, `EMMC_1.8V` (LDO),
  `3V3`, `5VM`, `VODC`, `VGG`, `VDD_TEST1/2`. Czyli eMMC (nie goły NAND) + DDR3L.
  *[prawdopodobne]*

### 0.4 UART i Wi-Fi

Na górnej krawędzi siedzą pady `UART1` / `UART2` (oraz `TXD1` / `RXD1`) i grupa
`12V` / `GND` / `VCC` — to wygląda na fabryczne miejsce na moduł Wi-Fi. Fabryczny
moduł to `SKI.W…` (dwa pigtaile u.FL, `GL1` / `GL2`, MAC `20:…`, CMIIT ID), więc
**to nie jest** ESP8266.

Skoro Tasmota siedzi na ESP8266 (MAC `18:FE:34:…`), a w profilu włączony jest
`SerialBridge` na GPIO13/16, najbardziej prawdopodobny scenariusz jest taki, że
**ESP jest wpięty w UART płyty głównej** i gada z SoC po szeregu. Jeśli to prawda,
to oprócz jasności da się prawdopodobnie wysyłać komendy (źródło, głośność, standby) —
trzeba tylko podsłuchać protokół. *[hipoteza, do potwierdzenia oscyloskopem]*

### 0.5 Reszta etykiet, które mogą się przydać

| Etykieta | Co to prawdopodobnie jest |
| --- | --- |
| `步进电机`, `AOUT` / `BOUT` / `GOUT`, `12V`, `5V` | złącze i sterowanie silnika krokowego (ostrzenie / zoom); obok SOP-16 `UA1` |
| `EXT_MIC&KEY`, `CN81`, `CNW1 WIFI`, `CNW2` | zewnętrzny mikrofon + klawiatura, gniazda modułów radiowych |
| `EXT_IR`, `IR_OUT1`, `IR_Board` | zewnętrzny odbiornik / nadajnik IR |
| `USB-DP2` / `USB-DM2` / `USB-2`, `5V_USB` | drugi port USB (host / OTG) — najpewniej tu siedzi „androidowa” część |
| `LOUT1±`, `ROUT1±`, `EAR_DET`, `AV_CVBS` | wyjścia audio (różnicowe, czyli klasa D) i composite |
| `QR1` | naklejka z QR — numer seryjny płytki, przydatny przy szukaniu ODM |

Czego **nie** wiadomo: co to za układ w SOP-16 `UA1` (kandydat na driver silnika
krokowego, bo obok jest legenda `AOUT` / `BOUT`), czy `5V_STB` faktycznie nie
znika w standby i który pin taśmy LED odpowiada za co. To trzeba zmierzyć, nie zgadnąć.

## 1. Najpierw pomiary

| Co | Czym | Po co |
| --- | --- | --- |
| `PWM_DIM` przy jasności 100 / 50 / 10 % | oscyloskop albo analizator stanów | czy to PWM do pinu DIM sterownika LED, czy już przefiltrowane DC; poznasz częstotliwość i mapowanie wypełnienia |
| Napięcie na `FB` / `ADJ` przetwornic `FAN0` i `FAN1` w obu stanach | multimetr | czy stockowy firmware **już** reguluje obroty; jeśli tak, wystarczy przejąć węzeł, a nie budować drugiej pętli |
| `NTC1` / `NTC2` w temperaturze pokojowej | multimetr (rezystancja) | dobór dzielnika do ADC; `NTC1` prawdopodobnie mierzy LED, nie powietrze (patrz §0.1) |
| `FAN_FG0` / `FAN_FG1` / `FAN_FG2` — czy pojawiają się impulsy przy kręcącym się wentylatorze | oscyloskop / `Counter` w Tasmocie | potwierdzenie, że `FG` to tacho, i ile impulsów na obrót (patrz §0.2) |
| `5V_STB` przy wyłączonym i włączonym projektorze | multimetr | czy da się z tego zasilić ESP na stałe (patrz §0.3) |
| Prąd wentylatora i prąd LED | zasilacz z pomiarem / INA219 | dobór MOSFET-a i zakresu pomiaru |

> Uwaga: kondensatory po stronie LED potrafią trzymać ładunek po odłączeniu zasilania.
> Nie lutuj przy włączonym projektorze i nie zwieraj sondą dwóch nóżek „na wszelki wypadek".

## 2. `PWM_DIM`

### 2.1 Częstotliwość PWM — konfiguracja, zero lutowania

Domyślnie Tasmota jedzie na **977 Hz**, czyli w paśmie słyszalnym: cewka sterownika
LED potrafi brzęczeć, a kamera łapie paski. Na ESP8266 `PWMFrequency` kończy się na
**4 kHz**, na ESP32 idzie do **50 kHz**.

```
PWMFrequency 4000      // ESP8266: maks.
PWMRange 1023          // 10 bitów
LedTable 1             // gamma (domyślnie włączona)
DimmerRange 40,100     // jeśli dół zakresu jest bezużyteczny
```

Dokumentacja: [Commands → PWMFrequency](https://tasmota.github.io/docs/Commands/#pwmfrequency),
[Lights → Gamma Correction](https://tasmota.github.io/docs/Lights/#gamma-correction).

To jest najtańsza poprawa jakości, jaką można zrobić — ale na ESP8266 nie wyleczy
piszczenia sterownika przy niskich jasnościach. Do tego potrzebny jest punkt 2.2.

### 2.2 Filtr RC → analogowe DC

Jeśli pin DIM sterownika przyjmuje napięcie analogowe (tak robi większość
kontrolerów backlightu), z PWM robimy DC:

```
GPIO ──[10k]──┬──[100R]── DIM
              │
            [4u7]
              │
             GND
```

- stała czasowa: `τ = R·C = 47 ms`, `fc ≈ 3,4 Hz`
- tętnienia przy 4 kHz: `T/τ ≈ 0,5 %` (przy domyślnym 977 Hz byłoby ~2 %)
- czas ustalania do 1 %: `≈ 4,6τ ≈ 220 ms` — czyli fade ma być wolny, i tak ma być

Wzory:

```
fc   = 1 / (2π·R·C)
ripple_pp/Vcc ≈ T_pwm / (R·C)      // dla R·C >> T
```

Jeśli pin DIM pobiera prąd albo ma pull-up, wstaw bufor rail-to-rail (MCP6001)
między filtr a pin. Bez tego cała charakterystyka ucieka.

**Czego nie robić:** nie podawaj 5 V na pin, który jest logiką 3,3 V, i nie zakładaj,
że sterownik schodzi do 0 %. Wiele driverów backlightu odcina się gdzieś przy
5–10 % wypełnienia i poniżej przestaje regulować — trzeba to zmierzyć i ustawić
`DimmerRange` na realną podłogę.

### 2.3 Prawdziwy DAC

- **MCP4725** (I²C, 12 bitów) — pewniak, ~1 €, działa z ESP8266 i ESP32.
- **ESP32** ma 2 wewnętrzne DAC-i 8-bit (GPIO25/26, na S3 GPIO17/18) — wygodne,
  ale 256 kroków to mało na dół zakresu; gamma to maskuje.
- ESP32-C3 **nie ma** DAC-a.

### 2.4 Telemetria prądu

INA219 (bocznik 0,1 Ω) na szynie LED daje realne mA i V. Tasmota ma natywny
sterownik. Wtedy suwak można wyskalować do **zmierzonego** światła, a nie do
wypełnienia PWM, i dostajesz gratis wykrywanie starzenia LED.

## 3. Wentylatory

Oba siedzą za własną przetwornicą o stałym wyjściu (7 V / 10 V), więc nie można
PWM-ować samej szyny — kondensatory na wyjściu przetwornicy tego nie lubią.

### 3.1 Wstrzyknięcie prądu w węzeł FB (najlepsze)

Dzielnik: `Vout ──R1── FB ──R2── GND`, na FB panuje `Vref` (typowo 0,6–0,8 V).

Podanie prądu w FB **obniża** wyjście:

```
Vout = Vref · (1 + R1/R2) − R1 · I_inj
I_inj = (Vdac − Vref) / Rinj
```

czyli:

```
Vout = Vref · (1 + R1/R2) − R1 · (Vdac − Vref) / Rinj
```

Dobór `Rinj` pod żądane minimum:

```
Rinj = R1 · (Vdac_max − Vref) / (Vout_nom − Vout_min)
```

Przykład (liczby zmyślone, podstaw swoje): `Vref = 0,8 V`, `R1 = 100k`, `R2 = 12k`
→ `Vout_nom ≈ 7,5 V`; dla `Vdac_max = 3,3 V` i `Vout_min = 4 V` wychodzi `Rinj ≈ 72k`.

Zalety: czyste DC, zero piszczenia, wentylator nie staje. Wady: trzeba namierzyć
dzielnik i wlutować się w FB — czyli fizyczna ingerencja w przetwornicę.

**Pułapka:** przy `Vdac = 0 V` (martwy MCU) wyjście idzie **w górę**, nie w dół.
Trzeba albo zbiasować węzeł sterujący do `Vref` (żeby brak sygnału = napięcie
nominalne), albo świadomie zaakceptować ~10–15 % nadnapięcia i sprawdzić, czy
wentylator to znosi.

### 3.2 PWM na masie, ~25 kHz (najprostsze)

N-MOSFET (AO3400 / IRLML6344) w szereg z masą wentylatora:

```
FAN− ── D ─┐
           │  AO3400
FAN+ ──────┴── (zworka do zasilania)   // dioda SS14 równolegle do wentylatora, katoda na +
```

- bramka: 100 Ω + 10k do masy
- **dioda kołowa obowiązkowa** — wentylator jest indukcyjny
- 20–25 kHz to standard, powyżej słyszalności
- trzymaj minimalne wypełnienie (~30 %) i rampuj powoli, żeby nie wpadać w rezonans

Na ESP8266 z limitem 4 kHz część wentylatorów będzie gwizdać. To jest główny
argument za ESP32.

### 3.3 Liniowo — raczej nie

Tranzystor jako opornik sterowany: cicho i prosto, ale wydziela
`P = (Vin − Vfan) · I`. Dla `(12−7) V · 0,15 A = 0,75 W` w obudowie SOT-23 robi się
gorąco, a w projektorze i tak jest ciepło. Sensowne tylko dla bardzo małych
wentylatorów.

### 3.4 Pętla termiczna

Na płycie są `NTC1` i `NTC2` — wystarczy dzielnik i ADC, a krzywą można trzymać
w Rules albo w Berry. Z silkscreenu wynika jednak, że **`NTC1` siedzi na taśmie LED**
razem z `VBL` i `PWM_DIM` (patrz §0.1), więc mierzy diodę/radiator, a nie powietrze
w obudowie. Do pętli „czy się nie przegrzewa” to nawet lepsze — ale nie odpinaj go
„na chwilę”, bo sterownik LED może to potraktować jak awarię.

Uwaga: **ESP8266 ma tylko jeden ADC** (A0), więc jeśli chcesz dwa NTC *i* INA219,
to już jest argument za ESP32. Sprawdź w dokumentacji, czy wbudowane typy ADC
w Tasmocie obsługują NTC, czy trzeba mapować krzywą ręcznie.

`Counter1` na GPIO4 — jeśli to tacho (a `FAN_FG*` sugeruje, że tacho jest), masz RPM
i detekcję zatrzymanego wentylatora bez dodatkowego sprzętu. Dwa wentylatory to dwa
liczniki, więc przy przejściu na ESP32 warto od razu zaplanować oba.

### 3.5 Fail-safe

Projektuj tak, żeby **awaria kontrolera = maksymalne obroty**, nie zero:

- przy starcie GPIO jest wejściem → pull-up powinien dawać pełne napięcie,
- watchdog i szybki boot Tasmoty,
- twarde zabezpieczenie na końcu: termik (np. KSD9700 70 °C, NC) w szeregu
  z zasilaniem LED. Kosztuje grosze i ratuje diodę, gdy sterownik padnie.

Projektor z martwym kontrolerem i zatrzymanymi wentylatorami to piekarnik.

## 4. Platforma

Jeśli i tak ruszamy sprzęt, **ESP32-S3** (albo klasyczny ESP32) zastępuje ESP8266
i daje wszystko w jednym: 16 kanałów sprzętowego PWM (ledc), kilka 12-bitowych
ADC, 2 DAC-i, RMT do IR i dość flasha na Berry. Tasmota to obsługuje, a kanały
niezależne włącza `SetOption68 1`.

| | ESP8266 | ESP32-C3 | ESP32 / S3 |
| --- | --- | --- | --- |
| PWM (ledc) | software, do 4 kHz | 6 kanałów, do 50 kHz | 16 kanałów, do 50 kHz |
| ADC | 1 kanał (A0), 10 bit | 5 użytecznych (GPIO0–4), 12 bit | 8 kanałów ADC1, 12 bit |
| DAC | brak | **brak** | 2 × 8 bit |
| IR / RMT | software | 2 × TX + 2 × RX | 8 kanałów |
| Flashowanie | UART | USB-Serial-JTAG | USB |
| Rdzeń | 80 MHz | 160 MHz RISC-V | 240 MHz, 2 rdzenie |

Mapa GPIO z [`tasmota/`](tasmota/) przenosi się 1:1 — to nadal te same funkcje,
tylko na innym pinie.

### A co z ESP32-C3?

C3 to najlepszy stosunek ceny do możliwości w tym projekcie — pod warunkiem, że
zaakceptujesz zewnętrzny DAC.

**Co dostajesz:** 6 kanałów ledc (do 50 kHz, czyli koniec piszczenia), 5 użytecznych
ADC 12-bit, RISC-V 160 MHz, USB-Serial-JTAG (flashowanie bez adaptera UART),
flash w obudowie i oficjalne binarki `tasmota32c3-*`. SuperMini kosztuje ~2 €.

**Czego brakuje:** DAC-a — analogowy dim tylko przez MCP4725 na I²C. Drugi rdzeń
i BT Classic nie są tu do niczego potrzebne, więc to nie boli.

**Wąskim gardłem są piny, nie CPU.** Na module C3-MINI-1 wystawione jest
GPIO0–10 i 18–21, czyli ~15 pinów, z czego 2, 8 i 9 to strapping (8 bywa zajęte
przez RGB LED, 9 to BOOT), a 18/19 to USB. Do tego ADC jest **tylko** na GPIO0–4,
więc oba NTC muszą tam trafić — i to jest realne ograniczenie, nie liczba kanałów PWM.

Budżet pinów dla tego projektu:

| Funkcja | Pinów |
| --- | --- |
| `PWM_DIM` (PWM lub MCP4725) | 1 |
| `FAN0` + `FAN1` PWM | 2 |
| `NTC1` + `NTC2` (ADC) | 2 (GPIO0–4) |
| I²C: MCP4725 + INA219 | 2 |
| IR / tacho / przycisk | 3 |
| **razem** | **10** |

Czyli 10 z ~14 — da się, ale bez zapasu na eksperymenty.

**Kiedy C3, a kiedy S3:** C3, jeśli dim idzie przez filtr RC albo MCP4725 i nie
planujesz wyświetlacza ani UI w Berry. S3, jeśli chcesz wszystko na jednym chipie
(2 DAC-i, 16 kanałów PWM, więcej GPIO) i nie przeszkadza ci ~2× cena.

## 5. Inne pomysły

- `POWER1` = przekaźnik odcinający zasilanie LED (`GPIO5`, odwrócony). `POWER2` ma
  docelowo wciskać przycisk projektora przez pady `SYS_PWR` / `SYS_PWR1` (patrz §0.3),
  ale drugie wyjście nie trafiło jeszcze do profilu Tasmoty — jest tylko jeden
  `Relay_i1`. Jeśli uda się potwierdzić, że `SYS_PWR` to faktycznie przycisk, można
  zamiast przekaźnika użyć optoizolatora równolegle do niego i mieć ciche włączanie
  bez klikania.
- Na `SerBr Tx/Rx` wisi coś od projektora. Tasmota ma dedykowany sterownik
  [LCD/DLP Projector Control](https://tasmota.github.io/docs/Projector/) — dla
  Androida prawie na pewno nie zadziała, ale samo **nasłuchiwanie tej linii**
  przez kilka sekund jest darmowe i może pokazać prawdziwy protokół sterowania
  (patrz §0.4).
- INA219 na całą linię 12 V daje pobór mocy projektora — ładne uzupełnienie telemetrii.
- Odbiornik IR (TSOP) + Tasmota IR daje pilota od projektora w HA.

## 6. BHP

- Nie dotykaj strony pierwotnej zasilacza. Kondensatory trzymają ładunek.
- Masa oscyloskopu do masy urządzenia, nigdy do przewodu fazowego.
- Po każdej zmianie w torze wentylatorów: test „odłącz kontroler, wentylatory
  muszą wystartować na maksa".
- Pierwszy test LED zawsze przez żarówkę albo zasilacz laboratoryjny z limitem prądu.
