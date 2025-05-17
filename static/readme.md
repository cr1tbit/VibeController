# Instrukcja wprowadzenia ESP32 w tryb programowania

Aby wprowadzić moduł **ESP32** w tryb programowania (flash), wykonaj następujące kroki:

1. Przytrzymaj przycisk **IO0 (GPIO0)** w stanie wciśniętym.
2. Nadal trzymając **IO0**, naciśnij i przytrzymaj przycisk **BOOT / EN**.
3. Zwolnij **BOOT / EN**, pozostawiając **IO0** wciśnięty jeszcze przez około sekundę.
4. Zwolnij **IO0**. Układ powinien przejść w tryb programowania i być gotowy do flashowania przez USB/UART.

---

## Łączność z Internetem

### Konsola UART
Najprostszą metodą jest użycie konsoli portu szeregowego (opis powyżej)

w oknie wpisać możemy "help" - wylistuje to nam dostępne komendy.

Wpisać możemy wifi `nazwa_wifi` `hasło_wifi` - kontroler powinien to zapisać i się zresetować,


### hotspot ESP32
Projekt korzysta z biblioteki `WifiSettings`, która w przypadku braku poprawnej konfiguracji Wi‑Fi uruchamia hotspot. Po wpisaniu danych logowania należy ponownie uruchomić płytkę, korzystając z przycisku na stronie WWW.

### Filesystem na płytce

Użytkownik może zaprogramować dane logowania z wyprzedzeniem, tworząc dwa pliki w katalogu `data/`:

* `wifi-ssid` — z nazwą sieci,
* `wifi-password` — z hasłem.

> **Uwaga:** przechowywanie danych dostępowych w niezaszyfrowanym pliku — zarówno na komputerze, jak i w pamięci flash ESP32 (zewnętrzna i niezaszyfrowana!) — stanowi potencjalne zagrożenie bezpieczeństwa. Jak zawsze, „S” w IoT oznacza **security**.

Po pomyślnym połączeniu z siecią można odczytać adres IP urządzenia z logów na porcie szeregowym lub z górnego paska na ekranie OLED (jeśli jest dostępny).



 ---


## Konfiguracja IO

Konfiguracja wyjść antenowych jest przechowywana w pliku `buttons.conf`. Ma składnię TOML, ale edytor SPIFFS nie obsługuje plików `.toml`, dlatego nazwa pliku musi brzmieć `buttons.conf`.

Przyciski są podzielone na grupy — tylko jeden przycisk w danej grupie może być aktywny; grupę można też ustawić w stan `OFF`.

### Wczytywanie konfiguracji

Domyślna konfiguracja znajduje się w katalogu `/data`. Po edycji (lub przy pierwszym programowaniu) należy wgrać partycję systemu plików, korzystając z opcji **Project tasks → Platform → Upload Filesystem Image** w panelu PlatformIO.

### Edycja presetów przez WebServer

Konfigurację można edytować, przechodząc pod adres `http://<IP_ADDR>/edit`; domyślne dane logowania to `test` / `test`. Płytka zawsze ładuje plik `button.conf` podczas uruchamiania — jeśli go zabraknie, konfiguracja się nie powiedzie.

> **Uwaga:** funkcjonalność dostarcza `ESPAsyncWebServer`, który bywa niestabilny.

### Opis pliku konfiguracyjnego

W pliku występują dwa rodzaje obiektów:

```toml
[[pin]]
sch     = "Z2-7"    # niestandardowy identyfikator oparty na schemacie
antctrl = "SINK1"   # nazwa w antcontrollerze: SINKx, RLx, OCx, TTLx lub INPx
name    = "QROS"    # funkcja tego pinu
descr   = ""        # opcjonalny opis
```

```toml
[[buttons.a]]            # buttons.<grupa>
name  = "160m VERTICAL"  # wywoływane przez /BUT/<name>
descr = ""               # opcjonalny opis
pins  = [ "Z2-7", "Z1-1" ]       # piny aktywowane przez przycisk
disable_on_low  = ["Z2-2"]       # automatyczne wyłączenie, gdy pin jest niski
disable_on_high = ["Z2-3"]       # automatyczne wyłączenie, gdy pin jest wysoki
```

Konfiguracja jest analizowana przy starcie urządzenia — jeśli zawiera błędy, przyciski nie zadziałają.

## Mechanizmy ochrony przed błędnymi presetami

Antcontroller udostępnia metody zapobiegające niepożądanym konfiguracjom systemu (np. ustawieniom, które mogą uszkodzić wzmacniacz przy nieodpowiedniej antenie).

1. **Grupy przycisków** – tylko jeden przycisk w grupie może być aktywny; przełączanie odbywa się na zasadzie *break‑before‑make* (najczęściej przerwa < 1 ms).
2. **pinGuard** – dodanie `disable_on_low` lub `disable_on_high` pozwala zablokować preset, gdy dany pin znajduje się w określonym stanie.

### pinGuardy

Na początku programu, w trakcie analizy konfiguracji, zbierane są wszystkie piny z `disable_on_low/high`, a następnie przypisuje się do nich „guardy”.

Po wczytaniu konfiguracji każdy pin może „pilnować” jednego lub więcej przycisków. Struktura:

```c
typedef struct {
    bool onHigh;
    std::string guardedButton;
} pinGuard_t;
```

**Wyzwalanie pinGuardu**

1. System uniemożliwia aktywację przycisku, jeśli blokuje go pinGuard.  
2. *Planowane* (jeszcze niezaimplementowane): przed włączeniem przycisku zostaną wyłączone przyciski kolidujące (`break‑before‑make`).  
3. Po zmianie stanu dowolnego pinu wejściowego pinGuardy są ponownie oceniane; kolidujące przyciski wyłączają się natychmiast.

#### Ograniczenia

* `disable_on_low` nie działa prawidłowo z pinami wyjściowymi (wymaga przebudowy).
* Stan wejść odczytywany co 25 ms – krótsze sygnały mogą zostać przeoczone.
* Nieoptymalna obsługa szybkozmiennych lub „pływających” wejść może spowolnić lub zawiesić urządzenie.

#### Dlaczego potrzebna jest przebudowa

1. Komunikacja między grupami/pinami/guardami oparta o napisy (`string`) → wiele `strcmp`.  
2. Struktury danych zdefiniowane chaotycznie (TODO).  
3. Nieoptymalne trójpoziomowe pętle.  
4. Brak programowego *debounce* wejść.

### Specjalne wejścia

| Pin | Funkcja | Aktywny stan |
|-----|---------|--------------|
| **IO15 (INP2)** | tryb *lock* – blokuje przyciski | wysoki |
| **IO16 (INP3)** | tryb *panic* – resetuje presety | niski |


 ---


## Podgląd na logi

Logi można odczytać przez terminal szeregowy lub na wyświetlaczu OLED.

Aby zobaczyć dane na porcie szeregowym, można użyć:

* Tej strony - po wciśnięciu dowolnego przycisku "connect" możemy podejrzeć logi. 
* wbudowanego monitora szeregowego w PlatformIO (ikona gniazdka na dolnym pasku VS Code),
* **putty** (Windows),
* **picocom** (Linux) — `picocom /dev/ttyUSB0 -b115200`, wyjście przez `Ctrl + A`, następnie `X`.





---




## Budowanie firmware'u

Ten projekt wykorzystuje platformę **PlatformIO IDE**, którą można uzyskać poprzez pobranie rozszerzenia PlatformIO dla Visual Studio Code.

Konfiguracja projektu znajduje się w pliku `platformio.ini`. Aby PlatformIO go rozpoznało, należy otworzyć katalog, który go zawiera. Wtedy wszystkie zależności powinny zostać automatycznie zainstalowane, a projekt powinien zbudować się bez problemów.

Aby uruchomić płytkę, użytkownik musi wgrać zarówno firmware, jak i partycję systemu plików.

Można to zrobić za pomocą graficznego interfejsu PlatformIO. Do tworzenia binarnej wersji „release” dołączono prosty skrypt pomocniczy. Użytkownik musi wykonać trzy polecenia w terminalu PlatformIO:

```bash
# zbuduj obraz systemu plików z plików w katalogu data/
pio run -e antcontroller -t buildfs
# połącz plik binarny firmware z systemem plików – powstanie merged-flash.bin
pio run -e antcontroller -t mergebin
# wgraj merged-flash.bin do ESP
pio run -e antcontroller -t flashall
```

Użytkownik może również wgrać gotowy plik binarny artefaktu, dostępny w zakładce **Actions** w repozytorium:

```bash
esptool.py write_flash 0x0 merged-flash.bin
```

© 2025 antController-fw – tłumaczenie PL
