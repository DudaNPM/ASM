import time

from tkinter import *

from utils.functions import generate_gares
from utils.functions import generate_pistas
from utils.functions import generate_avioes
from utils.functions import get_avioes_descolar

from agents.InfoAgent import Info
from agents.AviaoAgent import AviaoAgent
from agents.GestorGaresAgent import GestorGares
from agents.TorreControloAgent import TorreControlo

GARES = 0
PISTAS = 0
ATERRAGENS = 0
DESCOLAGENS = 0

def initialize():
    global GARES
    global PISTAS
    global ATERRAGENS
    global DESCOLAGENS

    GARES = int(e1.get())
    PISTAS = int(e2.get())
    ATERRAGENS = int(e3.get())
    DESCOLAGENS = int(e4.get())
    
    root.destroy()


root = Tk()
root.title("G6 AIRPORT")

Label(master=root, text='Número de gares do aeroporto').grid(row=0)
Label(master=root, text='Número de pistas do aeroporto').grid(row=1)
Label(master=root, text='Número de aviões a aterrar').grid(row=2)
Label(master=root, text='Número de aviões a descolar').grid(row=3)

e1 = Entry(root)
e2 = Entry(root)
e3 = Entry(root)
e4 = Entry(root)

e1.grid(row=0, column=1)
e2.grid(row=1, column=1)
e3.grid(row=2, column=1)
e4.grid(row=3, column=1)

Button(master=root, text='Start', command=initialize).grid(row=4, column=2, sticky=W, pady=4)

root.mainloop()


password  = "admin"
infoID = 'info@desktop-jh2ka3p'
gestorgaresID = 'gestorgares@desktop-jh2ka3p'
torrecontroloID = 'torrecontrolo@desktop-jh2ka3p'



pistas = generate_pistas(PISTAS)
avioes = generate_avioes(ATERRAGENS,DESCOLAGENS)
gares = generate_gares(GARES,avioes[ATERRAGENS:])
avioes = avioes[:ATERRAGENS] + get_avioes_descolar(gares)



## INFO AGENT
info = Info(infoID, password)
future = info.start()
future.result()



## TORRE CONTROLO AGENT
torrecontrolo = TorreControlo(torrecontroloID, password)
torrecontrolo.set('GestorGaresID', gestorgaresID)
torrecontrolo.set('pistas', pistas)
torrecontrolo.set('InfoID', infoID)
future = torrecontrolo.start()
future.result()



## GESTOR DE GARES AGENT
gestorgares = GestorGares(gestorgaresID, password)
gestorgares.set('TorreControloID', torrecontroloID)
gestorgares.set('gares', gares)
future = gestorgares.start()
future.result()



## AVIOES AGENT
for aviao in avioes:
    agent = AviaoAgent(aviao.getId(), password)
    agent.set('aviao', aviao)
    agent.set('GestorGaresID', gestorgaresID)
    agent.set('TorreControloID', torrecontroloID)
    agent.start()



while gestorgares.is_alive() and gestorgares.is_alive():
    try:
        time.sleep(1)
    except KeyboardInterrupt:
        info.stop()
        gestorgares.stop()
        torrecontrolo.stop()
        break