#define Trigpin 6
#define Echopin 7
#define led_0 9
#define led_1 10
#define led_2 11
#include <LiquidCrystal.h>
#include <Servo.h>

float distance;   //variabili per sensore ultrasonic
int duration;
int pos = 0;    //servo position
String data = "";    //stringa per leggere dati
LiquidCrystal lcd(13, 12, 5, 4, 3, 2);    //schermo lcd
Servo myservo;    //servomotore

void setup() {
  pinMode (Trigpin, OUTPUT);
  pinMode (led_0, OUTPUT);
  pinMode (led_1, OUTPUT);
  pinMode (led_2, OUTPUT);
  pinMode (Echopin, INPUT);
  
  //Accendo solo il led verde, posto libero
  digitalWrite (led_0, HIGH);
  digitalWrite (led_1, LOW);
  digitalWrite (led_2, LOW);

  myservo.attach(8);
  myservo.write(90);
  Serial.begin(9600);
  lcd.begin(16, 2); 
}

void loop() {
  lcd.setCursor(0,0);          
  lcd.print("   Benvenuto!    "); 
 
  //calcolo distanza
  digitalWrite(Trigpin, LOW);
  delay(2);
  digitalWrite(Trigpin, HIGH);
  delay(10);
  digitalWrite(Trigpin, LOW);
  duration = pulseIn(Echopin, HIGH);
  distance = duration * 0.034 / 2;
  
  //ricevo dati da raspberry
  if (Serial.available() > 0) {
    data = Serial.readStringUntil('\n');

    //2->Postazione prenotata
    if (data=="2"){
      digitalWrite (led_0, LOW);
      digitalWrite (led_1, LOW);
      digitalWrite (led_2, HIGH);
    }
    //3->Sbarra da alzare
    else if (data=="3")
    {
      lcd.setCursor(0,1);           
  	  lcd.print("  ID corretto  "); 

      for (pos = 90; pos >= 0; pos -= 1) {   //alzo la sbarra
        myservo.write(pos);              
        delay(15);                       
      }
      delay(3000);
      for (pos = 0; pos <= 90; pos += 1) {   //abbasso la sbarra
        myservo.write(pos);              
        delay(15);                       
      }

      //cancello la riga dell'ID
      lcd.setCursor(0,1); 
      lcd.print("                          ");
      data = "2";    //metto a 2 cosi non entro nell'if della distanza superiore a 5 cm, quindi il posto rimane arancione finchè non mi ci metto davanti
    }

    //Disponibilità parcheggi
    else if(data == "-0") 
    {
      lcd.setCursor(0,1);
      lcd.print("Parcheggio pieno");
    }
    else if (data == "-1")  
    {
      lcd.setCursor(0,1);
      lcd.print("    Posti: 1    ");
    }
    else if (data == "-2")  
    {
      lcd.setCursor(0,1);
      lcd.print("    Posti: 2    ");
    }
    else if (data == "-3")  
    {
      lcd.setCursor(0,3);
      lcd.print("    Posti: 3    ");
    }
    //Se è altro-> Id da stampare
    else    
    {
      lcd.setCursor(0,1);  
      lcd.print("                       ");   
      lcd.setCursor(0,1);        
  	  lcd.print("     ID:      "); 
      lcd.setCursor(9,1);
      lcd.print(data);
    }
  }

  if (distance>=5 && data != "2")
  {
    //aspetto 1 secondo e ricalcolo la distanza per assicurarmi che sia davvero libero
    delay(1000);
    digitalWrite(Trigpin, LOW);
    delay(2);
    digitalWrite(Trigpin, HIGH);
    delay(10);
    digitalWrite(Trigpin, LOW);
    duration = pulseIn(Echopin, HIGH);
    distance = duration * 0.034 / 2;

    if (distance>=5){
      digitalWrite (led_0, HIGH);
      digitalWrite (led_1, LOW);
      digitalWrite (led_2, LOW);
      Serial.write ("0\n");
      }
  }
  if (distance<5)
  {
    //aspetto 1 secondo e ricalcolo la distanza per assicurarmi che sia davvero occupato
    delay(1000);
    digitalWrite(Trigpin, LOW);
    delay(2);
    digitalWrite(Trigpin, HIGH);
    delay(10);
    digitalWrite(Trigpin, LOW);
    duration = pulseIn(Echopin, HIGH);
    distance = duration * 0.034 / 2;

    if (distance<5)
    {
      data = "";
      digitalWrite (led_0, LOW);
      digitalWrite (led_1, HIGH);
      digitalWrite (led_2, LOW);
      Serial.write ("1\n");
      }
  }
}