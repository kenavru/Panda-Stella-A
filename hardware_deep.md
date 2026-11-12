# Hardware deep-dive: `PWM_DIM` i wentylatory

← [Powrót do README](README.md)

Notatki projektowe, nie instrukcja „zrób tak i będzie działać". Wszystko poniżej
zakłada, że **najpierw zmierzymy**, co faktycznie siedzi na `PWM_DIM` i na
przetwornicach `FAN0` / `FAN1` — bo od tego zależy cała reszta. Wartości elementów
są przykładowe; podstaw swoje.

## 0. Najpierw pomiary

| Co | Czym | Po co |
| --- | --- | --- |
| `PWM_DIM` przy jasności 100 / 50 / 10 % | oscyloskop albo analizator stanów | czy to PWM do pinu DIM sterownika LED, czy już przefiltrowane DC; Poznasz częstotliwość i mapowanie wypełnienia |
| Napięcie na `FB` / `ADJ` przetwornic `FAN0` i `FAN1` w obu stanach | multimetr | czy stockowy firmware **już** reguluje obroty; jeśli tak, wystarczy przejąć węzeł, a nie budować drugiej pętli |
| `NTC1` / `NTC2` w temperaturze pokojowej | multimetr (rezystancja) | dobór dzielnika do ADC |
| `Counter1` (GPIO4) — czy pojawiają się impulsy przy kręcącym się wentylatorze | oscyloskop / `Counter` w Tasmocie | czy to już tacho i mamy RPM za darmo |
| Prąd wentylatora i prąd LED | zasilacz z pomiarem / INA219 | dobór MOSFET-a i zakresu pomiaru |

> Uwaga: kondensatory po stronie LED potrafią trzymać ładunek po odłączeniu zasilania.
> Nie lutuj przy włączonym projektorze i nie zwieraj sondą dwóch nóżek „na wszelki wypadek".

## 1. `PWM_DIM`

### 1.1 Częstotliwość PWM — konfiguracja, zero lutowania

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
piszczenia sterownika przy niskich jasnościach. Do tego potrzebny jest punkt 1.2.

### 1.2 Filtr RC → analogowe DC

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

### 1.3 Prawdziwy DAC

- **MCP4725** (I²C, 12 bitów) — pewniak, ~1 €, działa z ESP8266 i ESP32.
- **ESP32** ma 2 wewnętrzne DAC-i 8-bit (GPIO25/26, na S3 GPIO17/18) — wygodne,
  ale 256 kroków to mało na dół zakresu; gamma to maskuje.
- ESP32-C3 **nie ma** DAC-a.

### 1.4 Telemetria prądu

INA219 (bocznik 0,1 Ω) na szynie LED daje realne mA i V. Tasmota ma natywny
sterownik. Wtedy suwak można wyskalować do **zmierzonego** światła, a nie do
wypełnienia PWM, i dostajesz gratis wykrywanie starzenia LED.

## 2. Wentylatory

Oba siedzą za własną przetwornicą o stałym wyjściu (7 V / 10 V), więc nie można
PWM-ować samej szyny — kondensatory na wyjściu przetwornicy tego nie lubią.

### 2.1 Wstrzyknięcie prądu w węzeł FB (najlepsze)

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

### 2.2 PWM na masie, ~25 kHz (najprostsze)

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

### 2.3 Liniowo — raczej nie

Tranzystor jako opornik sterowany: cicho i prosto, ale wydziela
`P = (Vin − Vfan) · I`. Dla `(12−7) V · 0,15 A = 0,75 W` w obudowie SOT-23 robi się
gorąco, a w projektorze i tak jest ciepło. Sensowne tylko dla bardzo małych
wentylatorów.

### 2.4 Pętla termiczna

Na płycie są `NTC1` i `NTC2` — wystarczy dzielnik i ADC, a krzywą można trzymać
w Rules albo w Berry. Uwaga: **ESP8266 ma tylko jeden ADC** (A0), więc jeśli
chcesz dwa NTC *i* INA219, to już jest argument za ESP32. Sprawdź w dokumentacji,
czy wbudowane typy ADC w Tasmocie obsługują NTC, czy trzeba mapować krzywą ręcznie.

`Counter1` na GPIO4 — jeśli to tacho (typowo 2 impulsy na obrót), masz RPM
i detekcję zatrzymanego wentylatora bez dodatkowego sprzętu.

### 2.5 Fail-safe

Projektuj tak, żeby **awaria kontrolera = maksymalne obroty**, nie zero:

- przy starcie GPIO jest wejściem → pull-up powinien dawać pełne napięcie,
- watchdog i szybki boot Tasmoty,
- twarde zabezpieczenie na końcu: termik (np. KSD9700 70 °C, NC) w szeregu
  z zasilaniem LED. Kosztuje grosze i ratuje diodę, gdy sterownik padnie.

Projektor z martwym kontrolerem i zatrzymanymi wentylatorami to piekarnik.

## 3. Platforma

Jeśli i tak ruszamy sprzęt, **ESP32-S3** (albo klasyczny ESP32) zastępuje ESP8266
i daje wszystko w jednym: 16 kanałów sprzętowego PWM (ledc), kilka 12-bitowych
ADC, 2 DAC-i, RMT do IR i dość flasha na Berry. Tasmota to obsługuje, a kanały
niezależne włącza `SetOption68 1`.

| | ESP8266 | ESP32-C3 | ESP32 / S3 |
| --- | --- | --- | --- |
| PWM (ledc) | do 4 kHz | 6 kanałów | 16 kanałów, do 50 kHz |
| ADC | 1 kanał | kilka | kilka, 12 bit |
| DAC | brak | brak | 2 × 8 bit |
| IR / RMT | software | RMT | RMT |

Mapa GPIO z [`tasmota/`](tasmota/) przenosi się 1:1 — to nadal te same funkcje,
tylko na innym pinie.

## 4. Inne pomysły

- `POWER1` / `POWER2` wciąż nie są wyjaśnione. Jeśli któryś to przycisk projektora,
  przekaźnik można zastąpić optotriakiem/optoizolatorem równolegle do przycisku
  i mieć ciche włączanie bez klikania.
- Na `SerBr Tx/Rx` wisi coś od projektora. Tasmota ma dedykowany sterownik
  [LCD/DLP Projector Control](https://tasmota.github.io/docs/Projector/) — dla
  Androida prawie na pewno nie zadziała, ale samo **nasłuchiwanie tej linii**
  przez kilka sekund jest darmowe i może pokazać prawdziwy protokół sterowania.
- INA219 na całą linię 12 V daje pobór mocy projektora — ładne uzupełnienie telemetrii.
- Odbiornik IR (TSOP) + Tasmota IR daje pilota od projektora w HA.

## 5. BHP

- Nie dotykaj strony pierwotnej zasilacza. Kondensatory trzymają ładunek.
- Masa oscyloskopu do masy urządzenia, nigdy do przewodu fazowego.
- Po każdej zmianie w torze wentylatorów: test „odłącz kontroler, wentylatory
  muszą wystartować na maksa".
- Pierwszy test LED zawsze przez żarówkę albo zasilacz laboratoryjny z limitem prądu.
