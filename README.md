# Panda Stella A — 1080p Android projector

Hobbystyczna dokumentacja taniego projektora 1080p z Androidem: co siedzi w środku,
co da się z nim zrobić i nad czym jeszcze trzeba popracować.

[![Prezentacja projektu na YouTube](https://img.youtube.com/vi/j7VabG2wWTw/maxresdefault.jpg)](https://www.youtube.com/watch?v=j7VabG2wWTw)

> **Status:** projekt w toku. Działa sterowanie LED przez PWM, trwa walka z siecią.

## Spis treści

- [O projekcie](#o-projekcie)
- [Co działa, a co nie](#co-działa-a-co-nie)
- [Mod: PWM dla LED (ESP8266 + Tasmota)](#mod-pwm-dla-led-esp8266--tasmota)
  - [Sterownik Tasmota](#sterownik-tasmota)
- [Wentylatory FAN0 / FAN1](#wentylatory-fan0--fan1)
- [Środek obudowy](#środek-obudowy)
- [Znane problemy](#znane-problemy)
- [Roadmapa](#roadmapa)

## O projekcie

Tadam — z cyklu *Panda Stella* i *sterownik PWM*. Dlaczego producent nie dał tego
w oprogramowaniu? Nie wiem xD

Standardowo projektor nie pozwala sterować jasnością LED ani odciąć jej zupełnie.
Po rozebraniu obudowy okazało się, że na płycie głównej jest wyprowadzone `PWM_DIM` —
wystarczyło podać tam sygnał z zewnątrz.

Płyta główna: **OD.P.CRED16PRO.MT9269 (N)** (oznaczenie widoczne na PCB).

## Co działa, a co nie

| Funkcja | Stan | Uwagi |
| --- | --- | --- |
| USB — karty dźwiękowe | ✅ działa | da się mocno poprawić jakość dźwięku |
| USB — dyski i pendrive'y | ✅ działa | |
| USB — pady i kontrolery | ✅ działa | |
| Karta Ethernet | ❌ nie działa | prawdopodobnie problem kernela / okrojona aplikacja Settings |
| Karta Wi-Fi (USB) | ❌ nie działa | jw. |
| Moonlight (streaming) | ⚠️ działa, ale… | wąskim gardłem jest Wi-Fi — 7–26 Mbps, niestabilnie |

## Mod: PWM dla LED (ESP8266 + Tasmota)

Na ten moment do płyty podłączony jest **ESP8266 z Tasmotą**, a pilotem jest telefon.

Co można zrobić z telefonu:

- wcisnąć przycisk włącznika projektora,
- włączyć / wyłączyć LED,
- regulować jasność w zakresie **0–100%**.

Szczegóły montażu i podłączenia — patrz [film](https://www.youtube.com/watch?v=j7VabG2wWTw).

### Sterownik Tasmota

Na płycie siedzi ESP8266 z **Tasmotą 14.2.0**, dostępny w sieci lokalnej jako
[`http://pandastella.lan/`](http://pandastella.lan/) (mDNS, `PandaStella`).

| GPIO | Funkcja | Rola |
| --- | --- | --- |
| GPIO4 | `Counter1` | licznik impulsów |
| GPIO5 | `Relay_i1` | przekaźnik (odwrócony) |
| GPIO13 | `SerBr Tx` | serial bridge 115200 8N1 |
| GPIO14 | `PWM1` | `PWM_DIM` — jasność LED |
| GPIO16 | `SerBr Rx` | serial bridge 115200 8N1 |

Kanały: 2 × `Power`, `Dimmer` (0–100%), `Counter`. Cały profil — łącznie z szablonem
do importu i skryptem eksportującym — jest w katalogu [`tasmota/`](tasmota/).

Pełna kopia zapasowa (`/dl`) zawiera hasło Wi-Fi, więc świadomie nie trafia do repo.

## Wentylatory FAN0 / FAN1

Chciałbym dorzucić regulację obrotów, ale nie jest to proste: oba wentylatory są
sterowane **napięciowo**, każdy przez własną przetworniczkę. Będzie sporo grzebania.

| Złącze | Chłodzi | Domyślne napięcie |
| --- | --- | --- |
| `FAN1` | LED | 7 V |
| `FAN0` | LCD | 10 V |

## Środek obudowy

| | |
| --- | --- |
| ![Głośniki i radiator](1726082130443.jpg) | ![Płyta główna pod układem optycznym](1726082130446.jpg) |
| Głośniki, radiator i złącza z tyłu obudowy | Płyta główna pod układem optycznym |
| ![Silnik optyczny](1726082130449.jpg) | ![Płyta główna, zbliżenie](1726082130451.jpg) |
| Silnik optyczny i okablowanie | Płyta główna — sekcja LED i przetwornic |
| ![Etykiety na płycie](1726082130456.jpg) | ![Płyta główna z góry](1726082130464.jpg) |
| Złącza `FAN0` / `FAN1`, `PWM_DIM`, `LED_OUT` | Cała płyta: `OD.P.CRED16PRO.MT9269 (N)` |
| ![Radiator i ciepłowody](1726083367515.jpg) | |
| Radiator, ciepłowody i zasilanie zewnętrzne | |

## Znane problemy

- **Sieć to wąskie gardło.** Mimo pełnego zasięgu łącze kręci się w okolicach
  7–26 Mbps i jest niestabilne — to psuje Moonlighta i wszystko inne, co wymaga
  przepustowości.
- Brak działających kart sieciowych USB (Ethernet / Wi-Fi).
- Sterowanie wentylatorami wymaga ingerencji w tor napięciowy.

## Roadmapa

- [x] Sterowanie LED przez PWM (ESP8266 + Tasmota)
- [x] Włącznik projektora z telefonu
- [x] Profil Tasmota w repo ([`tasmota/`](tasmota/))
- [ ] Regulacja `FAN1` (LED)
- [ ] Regulacja `FAN0` (LCD)
- [ ] **Lepsze łącze sieciowe — top prio**
- [ ] Schemat połączeń (pinout GPIO jest już w [`tasmota/`](tasmota/))

## Uwaga

Wszystko robisz na własną odpowiedzialność. Rozbieranie projektora i ingerencja
w zasilanie LED / wentylatorów może go uszkodzić albo skończyć się pożarem.
Jeśli nie wiesz, co robisz — nie rób tego.
