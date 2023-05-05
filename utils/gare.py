from utils.aviao import Aviao
from utils.posicao import Posicao


class Gare:
    """Classe usada para representar uma gare.

    Attributes
    ----------
    id : str
        Identificador da gare.
    posicao : Posicao
        Posição da gare.
    free : bool
        Boolean que nos indica se a gare está livre ou não.
    tipo : str
        Indica-nos o tipo de gare (comercial ou mercadorias ou privado).
    aviao : Aviao
        Se estiver ocupada, indica o `aviao` que lá se encontra.
    """

    def __init__(self, id:str, posicao:Posicao, free:bool, tipo:str, aviao:Aviao=None):
        self.id = id
        self.free = free
        self.posicao = posicao
        self.tipo = tipo
        self.aviao = aviao
    
    def __eq__(self, gare):
        return self.id == gare.id
    
    def getId(self):
        return self.id
    
    def getFree(self):
        return self.free
    
    def getPosicao(self):
        return self.posicao

    def getTipo(self):
        return self.tipo

    def getAviao(self):
        return self.aviao
    
    def setId(self, id:str):
        self.id = id
    
    def setFree(self, free:bool):
        self.free = free
    
    def setPosicao(self, posicao:Posicao):
        self.posicao = posicao

    def setTipo(self, tipo:str):
        self.tipo = tipo
    
    def setAviao(self, aviao:Aviao):
        self.aviao = aviao
    
    def toString(self):
        return "Gare [ID=" + self.id + " Posicao=" + self.posicao.toString() + " Free=" + str(self.free) + " Tipo=" + self.tipo + (" Aviao=" + str(None) if not self.aviao else ' ' + self.aviao.toString()) + "]"