#include <Servo.h>

const int buttonPin = 2; // Buton 2 numaralı pine bağlı
int buttonState = 0;
int lastButtonState = HIGH; // Önceki buton durumu
const int ledPins[] = {3, 4, 5, 6}; // LED pinleri
const int servoPin = 7; // Servo motor pin
const int buzzerPin = 8; // Buzzer pini

Servo myServo; // Servo nesnesi
String inputString = "";      // Seri porttan gelen string
boolean stringComplete = false;  // String tamamlandı mı?

void setupButton();
void setupLEDs();
void setupServo();
void setupBuzzer();
void checkButtonAndPotentiometer();
void processSerialCommands();

void setup() {
  setupButton();
  setupLEDs();
  setupServo();
  setupBuzzer();
  
  // Seri port iletişimi başlatılıyor
  Serial.begin(9600);
  inputString.reserve(200); // Seri port için bellek ayrılıyor
}

void loop() {
  checkButtonAndPotentiometer();
  // runLEDSequence(); // Otomatik LED animasyonu kaldırıldı
  processSerialCommands();
}

void setupButton() {
  pinMode(buttonPin, INPUT_PULLUP); // Dahili pull-up aktif
}

void setupLEDs() {
  for (int i = 0; i < 4; i++) {
    pinMode(ledPins[i], OUTPUT);
    digitalWrite(ledPins[i], LOW); // Başlangıçta tüm LED'ler sönük
  }
}

void setupServo() {
  myServo.attach(servoPin); // Servo motoru 7. pine bağla
  myServo.write(0); // Başlangıç pozisyonu
}

void setupBuzzer() {
  pinMode(buzzerPin, OUTPUT);
}

void checkButtonAndPotentiometer() {
  buttonState = digitalRead(buttonPin);
  if (buttonState == LOW && lastButtonState == HIGH) { // Sadece ilk basışta
    // Zil sesi çal
    tone(buzzerPin, 1000, 500); // 1000 Hz frekansında 500ms çal
    
    // Zil sesi bittikten sonra butona basıldığını bildir
    delay(500); // Zil sesinin çalma süresi kadar bekle
    
    // Butona basıldığında GUI'ye bildir, kamerayı açmak için
    Serial.println("BUTTON_PRESSED");
    
    delay(500); // Debounce için kısa bekleme
  }
  lastButtonState = buttonState;
}

void runLEDSequence() {
  // static unsigned long previousMillis = 0;
  // const long interval = 400; // LED'ler arası geçiş süresi (ms)
  // static int currentLED = 0;
  
  // unsigned long currentMillis = millis();
  
  // if (currentMillis - previousMillis >= interval) {
  //   previousMillis = currentMillis;
    
  //   // Tüm LED'leri söndür
  //   for (int i = 0; i < 4; i++) {
  //     digitalWrite(ledPins[i], LOW);
  //   }
    
  //   // Sadece mevcut LED'i yak
  //   digitalWrite(ledPins[currentLED], HIGH);
    
  //   // LED durumunu Python arayüzüne gönder
  //   // Serial.print("LED:"); // Bu satır GUI'de karışıklığa neden olabilir, kaldırıldı.
  //   // Serial.println(currentLED); 
    
  //   // Sonraki LED'e geç
  //   currentLED = (currentLED + 1) % 4; // 0,1,2,3,0,1,2,3...
  // }
}

// Seri porttan gelen veriyi işle
void serialEvent() {
  while (Serial.available()) {
    char inChar = (char)Serial.read();
    if (inChar == '\n') {
      stringComplete = true;
    } else {
      inputString += inChar;
    }
  }
}

// Seri porttan gelen komutları işle
void processSerialCommands() {
  if (stringComplete) {
    // LED kontrolü
    if (inputString.startsWith("LED:")) {
      int ledNum = inputString.substring(4).toInt();
      if (ledNum >= 0 && ledNum < 4) {
        // LED'in mevcut durumunu oku ve tersine çevir (toggle)
        int currentState = digitalRead(ledPins[ledNum]);
        digitalWrite(ledPins[ledNum], !currentState); // Yeni durumu yaz
        
        Serial.print("LED_OK:");
        Serial.println(ledNum); // Hangi LED'in durumu değiştiğini GUI'ye bildir
      }
    }
    // Servo kontrolü - kapı açma
    else if (inputString.startsWith("OPEN_DOOR")) {
      myServo.write(90); // Kapıyı aç - 90 derece döndür
      Serial.println("DOOR_OPENED");
    }
    // Servo kontrolü - kapı kapama
    else if (inputString.startsWith("CLOSE_DOOR")) {
      myServo.write(0); // Kapıyı kapat - başlangıç pozisyonuna dön
      Serial.println("DOOR_CLOSED");
    }
    // Potansiyometre değerini oku
    else if (inputString.equals("GET_POT")) {
      int potValue = analogRead(A0);
      Serial.print("POT:");
      Serial.println(potValue);
    }
    
    // Komut işlendikten sonra temizle
    inputString = "";
    stringComplete = false;
  }
}
