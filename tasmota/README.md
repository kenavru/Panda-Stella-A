# Tasmota — konfiguracja sterownika Panda Stella A

Profil zdjęty z działającego urządzenia (`http://pandastella.lan/`, 2026-11-12).

## Urządzenie

| | |
| --- | --- |
| Hostname | `PandaStella` (mDNS: `pandastella.lan`) |
| IP | `10.0.1.219` |
| MAC | `18:FE:34:D3:04:68` |
| Sprzęt | ESP8266EX |
| Firmware | Tasmota 14.2.0 (build 2024-08-14), `tasmota` / Generic |
| Moduł | `0` (Generic, BASE 18) |
| Kanały | 2 × Power, Dimmer, Counter |

## Mapa GPIO

| GPIO | Funkcja | ID | Do czego |
| --- | --- | --- | --- |
| GPIO4 | Counter1 | 352 | licznik impulsów |
| GPIO5 | Relay_i1 | 256 | `POWER1` — przekaźnik odcinający zasilanie LED (odwrócony) |
| GPIO13 | SerBr Tx | 1792 | serial bridge, 115200 8N1 |
| GPIO14 | PWM1 | 416 | `PWM_DIM` — jasność LED |
| GPIO16 | SerBr Rx | 1824 | serial bridge, 115200 8N1 |

Pozostałe piny: `None`.

> `POWER1` = odcięcie zasilania LED (fizyczny przekaźnik na `GPIO5`). `POWER2` ma
> docelowo wciskać przycisk projektora przez pady `SYS_PWR`, ale w tym profilu nie ma
> jeszcze drugiego wyjścia — TODO.

## Pliki

- [`profile.json`](profile.json) — zrzut ustawień (bez haseł Wi-Fi), generowany przez
  [`export-profile.py`](export-profile.py),
- [`panda-stella.template.json`](panda-stella.template.json) — szablon Tasmota do importu,
- [`setup-commands.txt`](setup-commands.txt) — komendy do wklejenia w konsolę.

## Odtworzenie konfiguracji

1. Wgraj Tasmotę na ESP8266 i połącz się z siecią.
2. Otwórz *Configuration → Configure Template* i wklej zawartość
   `panda-stella.template.json`, albo wklej w konsoli:

   ```
   Template {"NAME":"PandaStella","GPIO":[0,0,0,0,352,256,0,0,0,1792,416,0,1824,0],"FLAG":0,"BASE":18}
   Module 0
   ```

3. Ustaw zachowanie kanałów (patrz `setup-commands.txt`).
4. Sprawdź `http://<ip>/cm?cmnd=Gpio` — mapa pinów musi się zgadzać z tabelą wyżej.

## Kopia zapasowa

Pełny backup robi się przez *Consoles → Backup Configuration*
(`http://<ip>/dl`, plik `Config_<hostname>_<wersja>.dmp`).

**Uwaga:** ten plik zawiera dane sieci Wi-Fi (SSID i hasło) oraz inne sekrety.
Nie wrzucaj go do repozytorium — dlatego `*.dmp` jest w `.gitignore`,
a w repo leży tylko oczyszczony `profile.json`.

## Eksport profilu

```bash
python3 export-profile.py
```

Skrypt czyta `http://pandastella.lan/` i nadpisuje `profile.json` oraz
`panda-stella.template.json`. Adres można zmienić w stałej `BASE`.
