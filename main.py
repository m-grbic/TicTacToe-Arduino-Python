from PyQt5.QtWidgets import QApplication, QPushButton, QLineEdit, QWidget,QLabel
from PyQt5.QtGui import QPainter, QPen
from PyQt5.QtCore import Qt
import sys
import numpy as np
import serial
import time
import datetime
import threading

# otvarajne serijske komunikacije
ser = serial.Serial('COM3', 9600)
# inicijalne vrednosti primljene poruke i poruke za slanje
vrednost = 'x' # inicijalna primljena vrednost sa Arduino platforme
poruka = "21020\n" # inicijalna poruka koja se salje ka Arduino platformi (prva cifra: 0 - drugi igrac, 1 - prvi igrac, 2 - nijedan igrac)
pocetak = 0 # dobija vrednost 1 pri pokretanju igre
prijem  = 1 # obezbedjuje da se primljeni podatak ne menja u toku obrade
end = 0 # koristi se kraj aplikacije
a = 100 # sirina kvadrata za graficki interfejs
#  inidikatori mesta pobede
pob_v = 0
pob_k = 0 
pob_d = 0
polje = [] # izabrano polje



class App(QWidget):
    def __init__(self):
        super().__init__()
        self.title = 'Igra IKS-OKS'
        self.left = 383
        self.top = 164
        self.width = 600
        self.height = 440
        # inicijalizacija broja poena
        self.p1 = 0
        self.p2 = 0
        self.status = 10 * np.ones((3, 3)) # matrica za igru
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.igrac1 = QLineEdit('Ime prvog igraca', self) # polje za unos imena prvog igraca
        self.igrac1.resize(100, 50)
        self.igrac1.move(10, 10)

        self.igrac2 = QLineEdit('Ime drugog igraca', self) # polje za unos imena drugog igraca
        self.igrac2.resize(100, 50)
        self.igrac2.move(10, 70)

        self.ime_datoteke = QLineEdit('Ime datoteke', self) # polje za unos imena datoteke
        self.ime_datoteke.resize(100, 50)
        self.ime_datoteke.move(10, 140)

        self.start_button = QPushButton('Pokreni igru', self) # taster za pokretanje igre
        self.start_button.resize(100, 50)
        self.start_button.move(self.width - 120, 20)
        self.start_button.clicked.connect(self.pocetak)

        self.reset_button = QPushButton('Reset', self) # taster za resetovanje rezultata
        self.reset_button.resize(50, 50)
        self.reset_button.move(self.width - 95, self.height / 2 - 25)
        self.reset_button.clicked.connect(self.reset)

        self.end_button = QPushButton('Izlaz', self) # taster za izlazak iz igre (ukoliko igra nije u toku)
        self.end_button.resize(100, 50)
        self.end_button.move(self.width - 120, self.height - 70)
        self.end_button.clicked.connect(self.kraj)

        self.text_za_polje = QLabel('Trenutno izabrano polje : ', self) # ispis trenutno izabranog polja
        self.text_za_polje.resize(200, 100)
        self.text_za_polje.move(20, self.height - 150 )

        self.show()

    def paintEvent(self, event):

        sablon = QPainter(self)

        # crtanje osnovne matrice za X-O igru

        sablon.setPen(QPen(Qt.black, 2, Qt.SolidLine))
        sablon.drawLine((self.width-3*a)/2,(self.height+a)/2,(self.width+3*a)/2,(self.height+a)/2)
        sablon.drawLine((self.width-3*a)/2,(self.height-a)/2,(self.width+3*a)/2,(self.height-a)/2)
        sablon.drawLine((self.width-a)/2,(self.height-3*a)/2,(self.width-a)/2,(self.height+3*a)/2)
        sablon.drawLine((self.width+a)/2,(self.height-3*a)/2,(self.width+a)/2,(self.height+3*a)/2)
        
        for i in range(3):
            for j in range(3):
                if (self.status[i][j] != 10):
                    if (self.status[i][j] == 1):
                        self.iks(p=[j,i])
                    else:
                        self.oks(p=[j,i])

        self.pob_linija()


    def iks(self,p):
        # funkcija za crtanje iks simbola na izabranom mestu
        iks = QPainter(self)
        A = [(self.width-3*a)/2 + p[0]*a,(self.height-3*a)/2 + p[1]*a]
        
        # crtanje znaka x
        
        iks.setPen(QPen(Qt.black, 1.5, Qt.SolidLine))
        iks.drawLine(A[0],A[1],A[0]+a,A[1]+a)
        iks.drawLine(A[0],A[1]+a,A[0]+a,A[1])
    
    def oks(self,p):
        # funkcija za crtanje oks simbola na izabranom mestu
        oks = QPainter(self)
        A = [(self.width-3*a)/2 + p[0]*a,(self.height-3*a)/2 + p[1]*a]
        
        # crtanje znaka o
        
        oks.setPen(QPen(Qt.black, 1.5, Qt.SolidLine))
        oks.drawEllipse(A[0],A[1],a,a)


    def text_polje(self):
        # ispis na interfejsu o trenutno izabranoj vrsti i koloni
        if(len(polje) == 1 ):
            self.text_za_polje.setText('Trenutno izabrano polje : \nVrsta: ' + str(polje[0]+1))
        if(len(polje) == 2):
            self.text_za_polje.setText('Trenutno izabrano polje : \nVrsta: ' + str(polje[0] + 1)+ '\nKolona : ' +str(polje[1] + 1) )
            time.sleep(1)
            self.text_za_polje.setText('Trenutno izabrano polje : ')

    def pob_linija(self):
        # crtanje pobednicke linije
        linija = QPainter(self)
        linija.setPen(QPen(Qt.red, 5, Qt.SolidLine))
        if pob_v:
            linija.drawLine((self.width-3*a)/2,self.height/2-a+a*(pob_v-1),(self.width+3*a)/2,self.height/2-a+a*(pob_v-1))
        if pob_k:
            linija.drawLine(self.width/2-a+a*(pob_k-1),(self.height-3*a)/2,self.width/2-a+a*(pob_k-1),(self.height+3*a)/2)
        if pob_d==1:
            # glavna dijagonala
            linija.drawLine((self.width-3*a)/2,(self.height-3*a)/2,(self.width+3*a)/2,(self.height+3*a)/2)
        if pob_d==2:
            # sporedna dijagonala
            linija.drawLine((self.width-3*a)/2,(self.height+3*a)/2,(self.width+3*a)/2,(self.height-3*a)/2)    

    def pocetak(self):
        t4 = threading.Thread(target=self.igra) # stavaranje i pokretanje niti za samo igru
        t4.start()
        
    def igra(self):
        global pocetak
        global poruka
        global vrednost
        global prijem
        global pob_v
        global pob_k
        global pob_d
        global polje
        pob_v = 0
        pob_k = 0
        pob_d = 0
        self.end_button.setDisabled(True) # dugme za izlaz je onemoguceno u toku igre
        self.status = 10 * np.ones((3, 3)) # inicijalizacija matrice na pocetku svake igre
        print(self.status) # ispis pocetne matrice
        brojac = 0 # brojac sluzi za raspoznavanje igrac1/igrac2 i vrsta/kolona
        polje = [] # u listi polje se cuvaju izabrane pozicije na tabli pristigle sa Arduina
        pocetak = 1
        datoteka = open(self.ime_datoteke.text() + ".txt", 'a') # otvaranje datoteke i upis o pocetku igre
        datoteka.write("Nova igra je zapoceta! (Vreme: " + str(datetime.datetime.now()) + ')\n') 
        poruka =  str(int(brojac % 4 < 2)) + '1' + str((self.p1) % 10) + '2' + str((self.p2) % 10) + '\n' # poruka da je prvi igrac na potezu i trenutni rezultat
        while end==0:
            # proverava se da li je podatak pristigao i ako jeste koja vrsta/kolona je izabrana
            if (vrednost != 'x'):
                if (vrednost[0] == '0'):
                    polje.append(0)
                    brojac += 1
                    vrednost = 'x'  # resetovanje ulazne vrednosti na default-nu

                if (vrednost[0] == '1'):
                    polje.append(1)
                    brojac += 1
                    vrednost = 'x'

                if (vrednost[0] == '2'):
                    polje.append(2)
                    brojac += 1
                    vrednost = 'x'

                if (vrednost[0] == '3'):
                    # indikator greske pri merenju udaljenosti (>30cm)
                    vrednost = 'x'
                    if (brojac % 2):
                        print("GRESKA! Udaljenost je veca od 30cm. Ponoviti unos kolone.")
                    else:
                        print("GRESKA! Udaljenost je veca od 30cm. Ponoviti unos vrste.")
                else:
                    # na kraju svakog drugog ucitanog podatka se menja igrac i  prethodno se upisuju u matricu podaci
                    if (brojac%2):
                        print("\nIzabrano polje:\n" + "    vrsta:   ",polje[0]+1)
                    else:
                        print("    kolona:  ",polje[1]+1)
                        print('\n')

                    self.text_polje() # izabrano polje se ispisuje na grafickom interfejsu

                    if ((brojac % 2) == 0 and polje != []):
                        if (self.status[polje[0]][polje[1]] != 10):
                          # trenutno polje je zauzeto, brojac se vraca unazad za 2, kako bi igrac ponovo uneo polje
                            print("GRESKA! Trenutno polje je zauzeto. Ponoviti unos vrste i kolone.")
                            brojac -= 2
                        else:
                            self.status[polje[0]][polje[1]] = int(brojac % 4 == 2) # izabrano polje dobija vrednost - 1/0
                            print(self.status) # novodobijena matrice se ispisuje u konzoli
                        polje = [] # polje se prazni i u slucaju greske i u slucaju validnog izbora polja

                    poruka = str(int(brojac % 4 < 2)) + '1' + str((self.p1) % 10) + '2' + str((self.p2) % 10) + '\n' 
                    rezultat = self.provera() # provera uslova gotove igre (nema praznih polja ili je neki od igraca pobedio)

                    if (not (any(10 in x for x in self.status)) or rezultat[0] or rezultat[1]):
                        # dodaje se 1 u slucaju pobede i 0 u slucaju neresenog rezultata ili gubitka
                        self.p1 += int(rezultat[0])
                        self.p2 += int(rezultat[1])
                        brojac = 0 # na kraju igre, brojac se resetuje
                        # novi rezultati se upisuju u poruku koja se prosledjuje Arduinu i upisuju se u datoteku
                        poruka = '21' + str((self.p1) % 10) + '2' + str((self.p2) % 10) + '\n'
                        datoteka.write(self.igrac1.text() + "   " + str(self.p1) + '\n' + self.igrac2.text() + "   " + str(self.p2) + '\n' + '\n')
                        datoteka.close()
                        self.update()
                        print("\nIgra je zavrsena")
                        self.end_button.setEnabled(True) # omogucava se izlaz iz igrice
                        break
            prijem = 1
            self.update()
            time.sleep(.1)
        pocetak = 2
    def provera(self):
        # pomocne promenljive za proveru pobednika
        pom1 = [1, 1, 1]
        pom2 = [0, 0, 0]
        # pocetni trenutni rezultat
        x1 = 0
        x2 = 0
        global pob_v
        global pob_k
        global pob_d
        # provera za prvog igraca
        for i in range(3):
            # provera po vrstama
            x1 += np.prod((pom1 == self.status[i])) * (not x1)
            if (x1 and not(pob_k) and not(pob_v) and not(pob_d)):
                pob_v=i+1
            # provera po kolonama
            x1 += np.prod((pom1 == self.status[:, i])) * (not x1)
            if (x1 and not(pob_k) and not(pob_v) and not(pob_d)):
                pob_k=i+1
        # provera glavne dijagonale
        x1 += (not x1) * ((1 == self.status[0, 0] and (1 == self.status[1, 1]) and (1 == self.status[2, 2])))
        if (x1 and not(pob_k) and not(pob_v) and not(pob_d)):
                pob_d=1
        # provera sporedne dijagonale
        x1 += (not x1) * ((1 == self.status[2, 0] and (1 == self.status[1, 1]) and (1 == self.status[0, 2])))
        if (x1 and not(pob_k) and not(pob_v) and not(pob_d)):
                pob_d=2
        # analogno, provera za 2. igraca
        for i in range(3):
            x2 += np.prod((pom2 == self.status[i])) * (not x2)
            if (x2 and not(pob_k) and not(pob_v) and not(pob_d)):
                pob_v=i+1
            x2 += np.prod((pom2 == self.status[:, i])) * (not x2)
            if (x2 and not(pob_k) and not(pob_v) and not(pob_d)):
                pob_k=i+1
        x2 += (not x2) * ((0 == self.status[0, 0] and (0 == self.status[1, 1]) and (0 == self.status[2, 2])))
        if (x2 and not(pob_k) and not(pob_v) and not(pob_d)):
                pob_d=1
        x2 += (not x2) * ((0 == self.status[2, 0] and (0 == self.status[1, 1]) and (0 == self.status[0, 2])))
        if (x2 and not(pob_k) and not(pob_v) and not(pob_d)):
                pob_d=2
        return [x1, x2]

    def kraj(self):
        global end
        # end = 1 => prekidaju se while petlje za serijsku komunikaciju
        end = 1
        self.close()

    def reset(self):
        global poruka
        self.p1 = 0
        self.p2 = 0
        poruka = '21020\n' # reset rezultata


def aplikacija():
    app = QApplication(sys.argv)
    ex = App()
    app.exec_()


def serijsko_citanje():
    global vrednost
    global prijem
    pomocna = 'x'
    while True:
        if (pocetak==1):
            # pocinje serijska komunikacija
            pomocna = str(ser.readline().decode())
            if prijem:
                # promenljiva 'vrednost' menja vrednost ukoliko obrada nije u toku
                vrednost = pomocna
                prijem = 0
                ser.flushInput()
        else:
            ser.flushInput() # brise se serijski ulaz ukoliko igra jos nije zapoceta
        if (end):
            # kraj aplikacije
            break


def serijsko_pisanje():
    global pocetak
    global poruka
    while True:
        if (pocetak==1):
            # pocinje serijska komunikacija
            ser.write(poruka.encode())
        if (pocetak==2):
            # na kraju aplikacije salje se poruka o konacnom rezultatu
            ser.write(poruka.encode())
            pocetak=0
        if (end):
            # kraj aplikacije
            break


# stvaranje i pokretanje niti
t1 = threading.Thread(target=aplikacija)
t2 = threading.Thread(target=serijsko_citanje)
t3 = threading.Thread(target=serijsko_pisanje)
t1.start()
t2.start()
t3.start()


while True:
    if not t1.isAlive():
        end = 1
        ser.close()
        break
