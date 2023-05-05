import time

from utils.functions import generate_gares
from utils.functions import generate_pistas
from utils.functions import generate_avioes
from utils.functions import get_avioes_descolar

from agents.InfoAgent import Info
from agents.AviaoAgent import AviaoAgent
from agents.GestorGaresAgent import GestorGares
from agents.TorreControloAgent import TorreControlo



GARES = 5
PISTAS = 2
ATERRAGENS = 5
DESCOLAGENS = 4



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
## torrecontrolo.web.start(hostname="127.0.0.1", port="10000") ## http://127.0.0.1:10000/spade
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