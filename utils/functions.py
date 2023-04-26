import math
import random

from utils.gare import Gare
from utils.aviao import Aviao
from utils.pista import Pista
from utils.posicao import Posicao



tipos = ['comercial', 'mercadorias']
companhias = ['AEGEAN', 'AIR EUROPA', 'easyJet', 'EMIRATES', 'EUROWINGS', 'FLYDUBAI', 'PEGASUS AIRLINES', 'RYANAIR', 'Saudia Airlines', 'SMART WINGS', 'SWISS AIR', 'TAP']
aeroportos = ['Lulea Kallax', 'Helsinquia Vantaa', 'Estrasburgo', 'Altay', 'International Falls', 'Tarakan', 'Dillingham', 'Wolf Point', 'Temuco', 'Coral Harbour', 'Mandalay', 'Ulyanovsk Baratayevka', 'Ponce', 'Tiksi', 'Tiksi', 'Elim', 'Fuzhou', 'Brisbane', 'Istambul', 'Quebec', 'Jabalpur', 'Bastia', 'Damasco', 'Chifeng', 'Villahermosa', 'Akureyri', 'Nyagan', 'Tambov', 'Misurata', 'Chiang Rai']



def distance(pos1:Posicao,pos2:Posicao):
    """Calcula a distância entre dois pontos, `pos1` e `pos2`.

    Parameters
    ----------
    pos1 : Posicao
        Posição 1.
    pos2 : Posicao
        Posição 2.
    
    Returns
    -------
    var : float
        Distância entre `pos1` e `pos2`.
    """
    p1 = [pos1.x,pos1.y]
    p2 = [pos2.x,pos2.y]
    return math.dist(p1,p2)


def get_closest_lane_and_gare(pistas:list[Pista], gares:list[Gare]):
    """Calcula a `pista` e `gare` mais próximos um do outro.

    Parameters
    ----------
    pistas : array_like
        Lista de todas as pistas.
    gares : array_like
        Lista de todas as gares livres.
    
    Returns
    -------
    pista : Pista
        Pista mais próxima de `gare`.
    gare : Gare
        Gare mais próxima de `pista`.
    """
    pista = gare = None
    menor_distancia = float('inf')
    
    for p in pistas:
        if p.getFree():
            for g in gares:
                d = distance(p.getPosicao(), g.getPosicao())
                if d < menor_distancia:
                    menor_distancia = d
                    pista, gare = p, g
    
    return pista,gare


def get_closest_lane_to_gare(pistas:list[Pista], gare:Gare):
    """Calcula a pista livre mais próxima de uma `gare`.

    Parameters
    ----------
    pistas : array_like
        Lista de todas as pistas.
    gare : Gare
        Gare em questão.
    
    Returns
    -------
    closest : Pista
        Pista mais próxima da `gare`.
    """
    closest = None
    menor_distancia = float('inf')

    for pista in pistas:
        if pista.getFree():
            d = distance(pista.getPosicao(), gare.getPosicao())
            if d < menor_distancia:
                menor_distancia = d
                closest = pista
    
    return closest


def get_avioes_descolar(gares:list[Gare]):
    """Calcula uma lista com todos os aviões que querem descolar.

    Parameters
    ----------
    gares : array_like
        Lista de todas as gares.
    
    Returns
    -------
    avioes : array_like
        Lista de todos os aviões que querem descolar.
    """
    avioes = list[Aviao]()

    for gare in gares:
        if not gare.getFree() and gare.getAviao():
            if gare.getAviao().getOperation() == 'descolar':
                avioes.append(gare.getAviao())
    
    return avioes



def get_occupied_gare(gares:list[Gare], aviao:Aviao):
    """Calcula a gare onde um avião está estacionado.

    Parameters
    ----------
    gares : array_like
        Lista de todas as gares.
    aviao : Aviao
        Avião em questão.
    
    Returns
    -------
    gare : Gare
        A gare onde o `aviao` está estacionado.
    """
    for gare in gares:
        if not gare.getFree() and gare.getAviao():
            if gare.getAviao().getId() == aviao.getId():
                return gare



def get_free_gares(gares:list[Gare], aviao:Aviao):
    """Calcula as gares disponíveis para um avião estacionar, tendo em conta o seu tipo (comercial ou de mercadorias).

    Parameters
    ----------
    gares : array_like
        Lista de todas as gares.
    aviao : Aviao
        Aviao que quer estacionar.

    Returns
    -------
    free_gares : array_like
        Gares disponíveis para o `aviao` estacionar.
    """
    free_gares = list[Gare]()

    for gare in gares:
        if gare.getTipo() == aviao.getTipo() and gare.getFree():
            free_gares.append(gare)
    
    return free_gares



def generate_avioes(aterrar:int, descolar:int):
    """Cria uma lista de `n` aviões de acordo com as propriedades pedidas.

    Parameters
    ----------
    aterrar : int
        Número de aviões a criar para aterrar.
    descolar : int
        Número de aviões a criar para descolar.

    Returns
    -------
    lista : array_like
        Lista de aviões com os requisitos pedidos.
    """
    lista = list[Aviao]()

    for i in range(1,aterrar+descolar+1):
        operacao = 'aterrar' if i <= aterrar else 'descolar'
        id = 'aviao' + str(i) + '@desktop-jh2ka3p'
        companhia = random.choice(companhias)
        tipo = random.choice(tipos)
        origemEdestino = random.choices(aeroportos, k=2)
        origem = origemEdestino[0]
        destino = origemEdestino[1]
        lista.append(Aviao(operacao, id, companhia, tipo, origem, destino))
    
    return lista



def generate_gares(n:int, avioes:list[Aviao]):
    """Cria uma lista de `n` gares de acordo com uma lista de aviões que pretendem descolar.

    Parameters
    ----------
    n : int
        Número de gares a criar.
    avioes : array_like
        Lista de aviões estacionados nas gares.

    Returns
    -------
    lista : array_like
        Lista de gares com os requisitos pedidos.
    """
    lista = list[Gare]()

    for i in range(1,n+1):
        id = 'gare' + str(i)
        pos = Posicao(random.randint(0,100), random.randint(0,100))
        tipo = 'comercial' if i <= n/2 else 'mercadorias'
        lista.append(Gare(id,pos,True,tipo))
    
    for aviao in avioes:
        for gare in lista:
            if gare.getFree() and gare.getTipo() == aviao.getTipo():
                gare.setFree(False)
                gare.setAviao(aviao)
                break

    return lista



def generate_pistas(n:int):
    """Cria uma lista de `n` pistas.

    Parameters
    ----------
    n : int
        Número de pistas a criar.

    Returns
    -------
    lista : array_like
        Lista de `n` pistas.
    """
    lista = list[Pista]()

    for i in range(1,n+1):
        id = 'pista' + str(i) + '@desktop-jh2ka3p'
        pos = Posicao(random.randint(0,100), random.randint(0,100))
        lista.append(Pista(id,pos,True))
    
    return lista