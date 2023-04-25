import time

from utils.functions import generate_gares
from utils.functions import generate_pistas
from utils.functions import generate_avioes
from utils.functions import get_avioes_estacionados

from agents.InfoAgent import Info
from agents.AviaoAgent import AviaoAgent
from agents.GestorGaresAgent import GestorGares
from agents.TorreControloAgent import TorreControlo



GARES = 10
PISTAS = 4
ATERRAGENS = 20
DESCOLAGENS = 20



password  = "admin"
infoID = 'info@desktop-jh2ka3p'
gestorgaresID = 'gestorgares@desktop-jh2ka3p'
torrecontroloID = 'torrecontrolo@desktop-jh2ka3p'



pistas = generate_pistas(PISTAS)
avioes = generate_avioes(ATERRAGENS,DESCOLAGENS)
gares = generate_gares(GARES,avioes[-DESCOLAGENS:])
avioes = avioes[:ATERRAGENS] + get_avioes_estacionados(gares)



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