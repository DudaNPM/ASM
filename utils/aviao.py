class Aviao:
    """Classe usada para representar um avião.

    Attributes
    ----------
    operation : str
        Inidica-nos a operação que o avião quer executar (aterrar ou descolar).
    id : str
        Identificador do avião.
    companhia : str
        Companhia de voo do avião.
    tipo : str
        Indica-nos o tipo do avião (comercial ou mercadorias).
    origem : str
        Local de origem do avião.
    destino : str
        Local de destino do avião.
    """

    def __init__(self, operation:str, id:str, companhia:str, tipo:str, origem:str, destino:str):
        self.operation = operation
        self.id = id
        self.companhia = companhia
        self.tipo = tipo
        self.origem = origem
        self.destino = destino
    
    def __eq__(self, aviao):
        return self.id == aviao.id

    def getOperation(self):
        return self.operation
    
    def getId(self):
        return self.id
    
    def getCompanhia(self):
        return self.companhia
    
    def getTipo(self):
        return self.tipo
    
    def getOrigem(self):
        return self.origem
    
    def getDestino(self):
        return self.destino
    
    def setOperation(self, op:str):
        self.operation = op
    
    def setId(self, id:str):
        self.id = id

    def setCompanhia(self, companhia:str):
        self.companhia = companhia

    def setTipo(self, tipo:str):
        self.tipo = tipo
    
    def setOrigem(self, origem:str):
        self.origem = origem
    
    def setDestino(self, destino:str):
        self.destino = destino
    
    def toString(self):
        return "Aviao=[ID=" + str(self.id) + " Operação=" + self.operation + " Tipo=" + self.tipo + " Companhia=" + self.companhia + " Origem=" + self.origem + " Destino=" + self.destino + "]"