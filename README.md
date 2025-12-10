# Lämpötila- ja Vuotovahti

Laite mittaa **lämpötilaa** ja **havaitsee vesivuotoja** Raspberry Pi Pico W -mikrokontrollerilla.  
Datan voi nähdä reaaliajassa selainpohjaisessa front endissa, josta löytyy myös ohjauspaneeli laitteen asetuksille.

## Toiminnot
- Mittaa lämpötilan lusikasta rakennetulla anturilla  
- Havaitsee vuodon foliosta rakennetulla anturilla  
- Näyttää arvot ThingSpeakissä ja piirtää kaavion Google Chartsilla  
- LEDit näyttävät lämpötilan ja vuototilanteen  
- LCD-näyttö näyttää lämpötilan ja varoituksen ylikuumenemisesta. 
- Web-käyttöliittymästä voi:
  - Tarkastella laitteen lähettämää dataa 
  - asettaa vuotosensorin raja-arvon  
  - kalibroida anturin kuivana/märkänä  
  - tarkistaa Picon nykyiset asetukset  

## Käyttö
1. Kytke laite virtalähteeseen.  
2. Odota, että laite käynnistyy itsestään. Sarjamonitori näyttää laitteen IP-osoitteen.  
3. Avaa `chart.html` selaimessa.  
4. Syötä Picon IP-ohjauspaneeliin, jotta voit hallita laitteen asetuksia ohjauspaneelin avulla.  
5. Kaavio näyttää ThingSpeakistä haetut lämpötila- ja vuotoarvot.

## LEDien tulkinta

Laitteessa on yhteensä seitsemän LEDiä: viisi lämpötilan ilmaisuun ja kaksi kosteuden havaitsemiseen. LEDien tarkoitus on antaa käyttäjälle nopea visuaalinen tilannekuva laitteen mittaamista arvoista.

### Lämpötilaa ilmaisevat LEDit (5 kpl)

LEDit syttyvät lämpötilan noustessa seuraavien raja-arvojen mukaan:

| Lämpötila | LED-tila |
|-----------|----------|
| 1–10 °C   | 1 LED palaa |
| 11–20 °C  | 2 LEDiä palaa |
| 21–30 °C  | 3 LEDiä palaa |
| 31–40 °C  | 4 LEDiä palaa |
| 41–50 °C  | 5 LEDiä palaa |
| > 50 °C   | 5 LEDiä vilkkuu (ylikuumeneminen) |

Tämän avulla käyttäjä näkee yhdellä silmäyksellä lämpötilan suuntaa antavasti ilman näyttöä tai kaaviota.

### Kosteutta ilmaisevat LEDit (2 kpl)

Kosteusanturi reagoi kosteuden lisääntymiseen niin, että sen ADC-arvo laskee. LEDien toiminta:

| Tila | LED-reaktio |
|------|--------------|
| Ei vuotoa | Vihreä LED palaa |
| Vuoto havaittu (ADC < threshold) | Punainen LED palaa, vihreä sammuu |

Threshold-arvo voidaan säätää ja kalibroida käyttöliittymästä.

## Web-ohjauspaneelin toiminnot
- **Set Threshold**  
  Asettaa vuotoanturin raja-arvon.
- **Reset Threshold**  
  Palauttaa oletusarvon.
- **Calibrate DRY / WET**  
  Tallentaa anturin arvon kuivana tai märkänä.
- **Get Status**  
  Näyttää laitteen raja-arvot ja kalibroidut arvot.

## Tiedostot
- `main.py` – Picon ohjelma (anturit, LEDit, ThingSpeak-lähetys, HTTP-komennot)  
- `chart.html` – web-näkymä  
- `chart.js` – kaavion piirtäminen ja Picon ohjaus  

## Yhteenveto
Projekti havainnollistaa yksinkertaisen IoT-järjestelmän, jossa mikrokontrolleri mittaa ympäristöä ja välittää datan pilveen, ja käyttäjä voi tarkastella tietoja web-selaimen kautta sekä muuttaa asetuksia etänä.


## Testausraportti

Projektin toiminnallisuus testattiin useilla testitapauksilla, jotka varmistivat antureiden, LEDien, LCD-näytön, ThingSpeak-lähetyksen ja käyttöliittymän toiminnan. Kaikki testit läpäistiin onnistuneesti.

### Testitulokset

| Testitapaus | Kuvaus | Odotettu toiminta | Tulos |
|-------------|--------|-------------------|--------|
| Jännitteen mittaus | Lämpötilan muutos muuttaa mitattua jännitettä | Jännite reagoi lämpötilaan | ✔️ Pass |
| Lämpötilan laskenta | Jännite muunnetaan lämpötilaksi siirtofunktion avulla | Lämpötila lasketaan oikein | ✔️ Pass |
| Lämpötilan näyttö LCD:ssä | Lämpötila näkyy reaaliajassa | Lämpötila päivittyy LCD:lle | ✔️ Pass |
| Lämpötilaledien toiminta | Ledit syttyvät/vilkkuvat oikeissa lämpötiloissa | LED-palkki vastaa lämpötilaa | ✔️ Pass |
| Kosteusledit | Vihreä = kuiva, punainen = vuoto | LEDit vaihtuvat tilan mukaan | ✔️ Pass |
| Datan lähetys ThingSpeakiin | Laite lähettää mittausarvot pilveen | Data näkyy ThingSpeakissä | ✔️ Pass |
| Datan visualisointi UI:ssa | Mittausdata piirtyy kaavioon | Kaavio näkyy käyttöliittymässä | ✔️ Pass |
| Anturin ohjaus käyttöliittymästä | Threshold ja kalibrointi toimivat | Arvot säädettävissä frontista | ✔️ Pass |

### Yhteenveto

Testauksen perusteella:

- Lämpötila-anturi reagoi johdonmukaisesti lämpötilan muutoksiin  
- LEDit toimivat suunnitellun lämpötila- ja kosteuskartan mukaan  
- LCD päivittyy reaaliajassa ja varoitukset näkyvät selkeästi  
- Vuotoanturi tunnistaa märän/kuivan tilan luotettavasti  
- ThingSpeak-yhteys ja käyttöliittymän kaaviot toimivat vakaasti  
- Käyttöliittymä ohjaa Picoa onnistuneesti (threshold + kalibrointi)

Kaikki projektin keskeiset toiminnallisuudet toimivat suunnitellusti.

