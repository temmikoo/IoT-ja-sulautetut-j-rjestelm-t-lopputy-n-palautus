# Lämpötila- ja Vuotovahti (Raspberry Pi Pico W)

Tämä projekti mittaa **lämpötilaa** ja **havaitsee vesivuotoja** Raspberry Pi Pico W -mikrokontrollerilla.  
Datan voi nähdä reaaliajassa web-sivulla, ja siinä on myös yksinkertainen ohjauspaneeli laitteen asetuksille.

## Toiminnot
- Mittaa lämpötilan lusikasta rakennetulla anturilla  
- Havaitsee vuodon foliosta rakennetulla anturilla  
- Näyttää arvot ThingSpeakissä ja piirtää kaavion Google Chartsilla  
- LEDit näyttävät lämpötilan ja vuototilanteen  
- LCD-näyttö näyttää lämpötilan ja varoituksen  
- Web-käyttöliittymästä voi:
  - asettaa vuotosensorin raja-arvon  
  - kalibroida anturin kuivana/märkänä  
  - tarkistaa Picon nykyiset asetukset  

## Käyttö
1. Lataa `main.py` Picoon ja täytä WiFi-tiedot tiedoston alkuun.  
2. Käynnistä Pico. Sarjamonitori näyttää laitteen IP-osoitteen.  
3. Avaa `chart.html` selaimessa.  
4. Syötä Picon IP-ohjauspaneeliin, niin sivu voi kommunikoida laitteen kanssa.  
5. Kaavio näyttää ThingSpeakistä haetut lämpötila- ja vuotoarvot.

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
