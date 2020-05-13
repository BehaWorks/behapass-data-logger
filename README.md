# Behapass Data Logger - Client
Aplikácia na zbieranie údajov z VR ovládačov a ich odosielanie na server. Súčasť projektu [BehaPass](http://labss2.fiit.stuba.sk/TeamProject/2019/team12/).

## Inštalácia
Podporovaná verzia Python 3.5+.  
Pre správne fungovanie treba mať nainštalované [SteamVR](https://store.steampowered.com/app/250820/SteamVR/). Bez toho aplikácia len pošle ukážkové dáta na server (test API).  

1. Naklonovať tento repozitár (`git clone https://github.com/BehaWorks/behapass-data-logger.git`).  
2. V priečinku repozitára nainštalovať závislosti: `pip install -r requirements.txt`.  
3. Do priečinka repozitára manuálne stiahnuť knižnicu [Triad OpenVR](https://github.com/TriadSemi/triad_openvr). Stačí stiahnuť súbor `triad_openvr.py`.  
4. Pri prvej inštalácii treba vytvoriť súbor `config/config.json`, forma podľa `config/example_config.json` (stačí skopírovať a premenovať).
5. Aplikácia sa spúšťa súborom `logger.py`.

## Fungovanie
1. Logger zistí počet pripojených ovládačov.  
2. Logger čaká na vstup od používateľa.
3. Akonáhle používateľ stlačí tlačidlo nahrávania (nastaviteľné v konfigurácii), začne sa zaznamenávať pohyb. Pohyb sa zaznamenáva kým je dané tlačidlo stlačené.
4. Akonáhle používateľ pustí tlačidlo, nahrávanie skončí a zaznamenané údaje sa odošlú na server.  

Pokiaľ sa nepodarí načítať VR rozhranie (môže byť nepripojený headset, prípadne vypnuté SteamVR), aplikácia iba načíta skôr nalogované dáta zo súboru a pokúsi sa odoslať ich na server. Toto slúži na otestovanie odosielania na server bez potreby mať pripojený VR headset.

## Konfigurácia  
Konfiguračný súbor `config/config.json`obsahuje nasledovné polia:  

* `sid_length` - Dĺžka session ID stringu,  
* `sample_rate` - Vzorkovacia frekvencia snímaného pohybu,  
* `api_host` - URL, kde sa nachádza logovacie API,  
* `button` - Tlačidlo, ktorým sa ovláda nahrávanie pohybu. Pokiaľ sa zadá neplatná hodnota, používa sa `trigger`,  
* `button_options` - **Nemeniť.** Možnosti pre pole `button` (opisy pre ovládače HTC Vive):  
    * `trigger` - spúšť na spodnej strane ovládača, to čo sa dá spojito stláčať,
    * `ulButtonPressed` - stlačenie hociktorého tlačidla,  
    * `ulButtonTouched` - dotyk hociktorého tlačidla (trigger a trackpad),  
    * `trackpad_pressed` - stlačenie trackpadu (kruhová plocha na vrchu ovládača),  
    * `trackpad_touched` - dotyk trackpadu,   
    * `menu_button` - tlačidlo nad trackpadom,  
    * `grip_button` - tlačidlo na boku.
