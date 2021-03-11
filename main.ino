#include <TimerOne.h>
#include <TM1637Display.h>
// definicija promenljivih za ultrazvucni senzor rastojanja

long vreme = 0;
int rastojanje = 0;
int trigPin = 11;
int echoPin = 10;
volatile byte stanje = 0; // menja vrednost na 100ms

// definicija promenljivih za kapacitivni senzor dodira

int touchPin = 2;
volatile byte stanjedodir = 0;

// diode za indikaciju igraca

int prvi = 4;
int drugi = 7;

// TM1637

int CLK = 9;
int DIO = 8;

// promenljive za za prijem podataka

String inputString = "";
String operation = "21020"; // prva jedinica - 1.igrac, ako je tu nula - 2.igrac

TM1637Display display(CLK, DIO);


void setup() {
  
  // inicijalizacija senzora rastojanja
  
  pinMode(trigPin,OUTPUT);
  pinMode(echoPin,INPUT);
  
  // inicijalizacija dioda
  
  pinMode(prvi,OUTPUT);
  pinMode(drugi,OUTPUT);
  
  //serijska komunikacija
  
  Serial.begin(9600);
  
  // inicijalizacija senzora dodira
  
  pinMode(touchPin,INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(touchPin), slanje_rezultata, CHANGE);
  
  // inicijalizacija tajmera
  
  Timer1.initialize(100000); // 100ms (meri u mikrosekundama)
  Timer1.attachInterrupt(timerIsr); // poziva se funkcija na 100ms
  
}

void loop() {
  
  if(stanje) {
    
    // merenje rastojanja
    
    digitalWrite(trigPin,LOW);
    delayMicroseconds(2);
    digitalWrite(trigPin,HIGH);
    delayMicroseconds(10);
    digitalWrite(trigPin,LOW);
    vreme = pulseIn(echoPin,HIGH);
    rastojanje = 340*vreme/(2*10000); //rastojanje u centimetrima
    stanje = 0;
    
  }


  // ukljucivanje dioda u zavisnosti od toga da li je prvi ili drugi igrac na potezu
  
  if (operation.toInt()>10000 and operation.toInt() < 20000) {
    digitalWrite(prvi,HIGH);
    digitalWrite(drugi,LOW);
  }
  if (operation.toInt() < 10000){
    digitalWrite(prvi,LOW);
    digitalWrite(drugi,HIGH);
  }
  if (operation.toInt() > 20000){
    digitalWrite(prvi,LOW);
    digitalWrite(drugi,LOW);
  }
  
  // prikaz na sedmosegmentnom displeju
  
  display.setBrightness(0x0f);
  display.showNumberDec(operation.toInt()%10000, true);

  // omogucava slanje jednog podatka za jedan dodir sa Arduino platforme
  
  if(stanjedodir==1){
    delay(1000);
    stanjedodir=0;
  }
}

// komunikacija Arduino -> Python

void slanje_rezultata() {
  if (stanjedodir==0) {
    if (rastojanje < 10){ // 1. red/kolona
        Serial.println(0);
    }
    else if ((rastojanje > 10) and (rastojanje < 20)) { // 2. red/kolona
        Serial.println(1);
    }
    else if ((rastojanje > 20) and (rastojanje < 30)) { // 3. red/kolona
        Serial.println(2);
    }
    else { // greska
        Serial.println(3);
    }
    stanjedodir=1;
  }
}


// komunikacija Arduino <- Python

void serialEvent() {
  while (Serial.available()) {
    char inChar = (char)Serial.read();
    if (inChar == '\n') {
      operation = inputString;
      inputString = "";
    }
    else {
      inputString += inChar;
    }
  }
}


void timerIsr() {
  stanje=1;
}
