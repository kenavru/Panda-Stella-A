# Mods / inspiracje

← [Powrót do README](README.md)

Zacznijmy od smutnej wiadomości: **dla samej Pandy Stelli A nie ma żadnych modów.**
Model występuje w sieci praktycznie tylko jako fiński rebrand (ogłoszenie na tori.fi,
~200 €) — zero wątków na forach, zero dumpów firmware'u, zero 4PDA. README w tym
repo jest chyba jedynym publicznym źródłem o tym sprzęcie xD

Ale nie jesteśmy sami. `MT9269` to to samo co **MSTAR MT9255** (4×A53, Android 9,
1 + 8 GB, 1080p LCD) — potwierdza to m.in.
[datasheet FreeSun IMC450A](http://freesuntech.com/html/Products/LCDProjectors/20230926/43.html).
Ten sam SoC siedzi w Wanbo T4, Emotn H1, PiPO AP-481/551, HP CC500 czy ET32, więc
jeśli ktoś kiedyś zrobi roota pod MT9269, będzie pasował także tutaj.

Poniższe projekty są na **innych SoC-ach** (Allwinner, Rockchip) — nie są
drop-in, ale sposobem działania nadają się do podkradzenia:

| Projekt | Platforma | Co ciekawe |
| --- | --- | --- |
| [gniax/magcubic-hy300-root](https://github.com/gniax/magcubic-hy300-root) | Allwinner | Magisk, nadpisywanie klawiszy pilota IR, auto-przełączanie na HDMI |
| [BruBread/ProjectorRoot](https://github.com/BruBread/ProjectorRoot) | Rockchip RK3326 | Jak odzyskać ADB, gdy producent wyciął opcje programisty + ślad RE firmware'u |
| [adrbn/nt30-airplay-guide](https://github.com/adrbn/nt30-airplay-guide) | budżetowy Android | Root przez podstawienie `su` jako `/system/bin/wifi`, potem AirPlay |
| [asakue/android-projector-optimizer](https://github.com/asakue/android-projector-optimizer) | generyczny | GUI do odchudzania po ADB (port 5555) — ma szansę działać bez zmian |
| [tqhit/cleanyourprojector](https://github.com/tqhit/cleanyourprojector) | generyczny | Odchudzanie + audyt backdoorów |
| [harshonedev/cleanbeam](https://github.com/harshonedev/cleanbeam) | generyczny | To samo, tylko w CLI |
| Projectivy Launcher + `pm disable-user --user 0` | generyczny | Klasyczne „zróbmy stockowy launcher znośny” |

## Co z tego wynika

1. **Odchudzanie / UX** — najtańsza wygrana. ADB po 5555 + Projectivy +
   `pm disable-user` nie wymaga roota ani grzebania w firmware.
2. **Root** — na MT9269 nie ma publicznego exploita. Realna droga to ta, którą
   poszły powyższe projekty: znaleźć UART SoC i dostać shell. Przy ESP8266 mamy
   `SerBr Tx/Rx` na GPIO13/16 — *jeśli* są podłączone do debugowego UART-u
   projektora, to jest nasze wejście. Niepotwierdzone, do sprawdzenia miernikiem
   albo analizatorem stanów.
3. **Rebuild firmware'u** — na MT9269 nikt tego publicznie nie zrobił. Byłby to
   naprawdę nowy teren.
