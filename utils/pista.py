from utils.posicao import Posicao


class Pista:
    """Classe usada para representar uma pista.

    Attributes
    ----------
    id : str
        Identificador da pista.
    posicao : Posicao
        Posição da pista.
    free : bool
        Boolean que nos indica que se a pista está livre ou não.
    """

    def __init__(self, id:str, posicao:Posicao, free:bool):
        self.id = id
        self.free = free
        self.posicao = posicao
    
    def __eq__(self, pista):
        return self.id == pista.id
    
    def getId(self):
        return self.id

    def getFree(self):
        return self.free
    
    def getPosicao(self):
        return self.posicao

    def setId(self, id:str):
        self.id = id
    
    def setFree(self, free:bool):
        self.free = free
    
    def setPosicao(self, posicao:Posicao):
        self.posicao = posicao
    
    def toString(self):
        return "Pista [ID=" + self.id + " Posicao=" + self.posicao.toString() + " Free=" + str(self.free) + "]"