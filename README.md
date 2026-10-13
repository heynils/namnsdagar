# Namnsdagar

Svenska namnsdagar som en kalenderfeed (iCalendar) du kan prenumerera på i Apple Kalender, Google Kalender, Outlook med flera.

**Webbsida:** https://heynils.github.io/namnsdagar/

## Prenumerera

| Kalender | Gör så här |
| --- | --- |
| Apple Kalender (Mac, iPhone, iPad) | Öppna [webcal://heynils.github.io/namnsdagar/namnsdagar.ics](webcal://heynils.github.io/namnsdagar/namnsdagar.ics) |
| Google Kalender | [Lägg till via länk](https://calendar.google.com/calendar/r?cid=webcal%3A%2F%2Fheynils.github.io%2Fnamnsdagar%2Fnamnsdagar.ics) |
| Övriga | Lägg till kalender från internet med adressen `https://heynils.github.io/namnsdagar/namnsdagar.ics` |

Varje dag med namnsdag är en heldagshändelse, till exempel *Berit, Birgit*. Händelserna upprepas årligen och är markerade som lediga, så de blockerar inte din tid. Dagar utan namnsdag (till exempel juldagen och skottdagen) saknar händelse.

## Uppdatera data

Namnlängden ändras sällan, senast 2022. Generera om filerna så här:

```sh
python3 scripts/generate.py
```

Skriptet använder bara Pythons standardbibliotek. Det hämtar [Lista över namnsdagar i Sverige i datumordning](https://sv.wikipedia.org/wiki/Lista_%C3%B6ver_namnsdagar_i_Sverige_i_datumordning) från Wikipedia, kontrollerar att alla 359 dagar finns med och skriver sedan:

- `data/namnsdagar.json` och `docs/namnsdagar.json` med namnen per datum
- `docs/namnsdagar.ics` med kalenderfeeden

Granska diffen innan du committar, eftersom Wikipedia kan innehålla tillfällig vandalism.

## Källa och licens

Namnen kommer från svenska Wikipedia ([CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)). Wikipedia bygger i sin tur på Svenska Akademiens namnlängd.
