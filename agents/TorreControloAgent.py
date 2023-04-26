import datetime
import jsonpickle

from utils.gare import Gare
from utils.aviao import Aviao

from spade import agent
from spade.message import Message
from spade.behaviour import CyclicBehaviour
from spade.behaviour import PeriodicBehaviour

from utils.functions import get_avioes_descolar
from utils.functions import get_closest_lane_to_gare
from utils.functions import get_closest_lane_and_gare



MAX = 5 # número máximo de aviões em fila de espera para aterrar



class TorreControlo(agent.Agent):

    ## avioes
    gares = list[Gare]()
    aterragens = list[Aviao]()
    descolagens = list[Aviao]()


    async def setup(self):
        print("Agent {}".format(str(self.jid)) + " starting...")

        ## Estado

        ## Behaviours
        self.info = self.Info(period=10,start_at=datetime.datetime.now() + datetime.timedelta(seconds=2))
        self.control = self.Control()
        self.add_behaviour(self.info)
        self.add_behaviour(self.control)
    

    class Info(PeriodicBehaviour):
        async def run(self):
            body = {'gares':self.agent.gares, 'aterragens':self.agent.aterragens, 'descolagens':self.agent.descolagens}
            msg = Message(to=self.get('InfoID'))
            msg.set_metadata('performative', 'global_info')
            msg.body = jsonpickle.encode(body)
            await self.send(msg)


    class Control(CyclicBehaviour):
        async def run(self):
            ## esperar por pedidos
            msg = await self.receive(timeout=10)
            
            if msg:
                performative = msg.get_metadata('performative')
                print('TorreControlo: ' + str(performative))
                received = jsonpickle.decode(msg.body)

                
                ## pedido de aterragem por parte de um aviao
                if performative == 'landing_request':
                    ## verificar se o avião já está na fila de espera
                    if received in self.agent.aterragens:
                        ## questionar o gestor de gares por uma gare livre
                        msg = Message(to=self.get('GestorGaresID'))
                        msg.set_metadata('performative', 'gare_request')
                        msg.body = jsonpickle.encode(received)
                    
                    ## verificar o limite de avioes em fila de espera para aterrar
                    elif len(self.agent.aterragens) < MAX:
                        ## adcionar o aviao à fila de espera para aterrar
                        self.agent.aterragens.append(received)
                        
                        ## questionar o gestor de gares por uma gare livre
                        msg = Message(to=self.get('GestorGaresID'))
                        msg.set_metadata('performative', 'gare_request')
                        msg.body = jsonpickle.encode(received)
                    
                    ## fila de espera cheia e o avião não se encontra nela
                    else:
                        ## mandar o aviao aterrar noutro aeroporto
                        msg = Message(to=received.getId())
                        msg.set_metadata('performative', 'negative_landing')
                        msg.body = jsonpickle.encode({'status':'aeroporto'})
                    
                    await self.send(msg)

                
                ## resposta positiva por parte do gestor de gares
                elif performative == 'positive_gare':
                    aviao = received.get('aviao')                                       # aviao
                    gares = received.get('gares')                                       # gares livres para o aviao estacionar
                    pista, gare = get_closest_lane_and_gare(self.get('pistas'), gares)  # pista e gare mais próximas
                    
                    if pista and gare:
                        pista.setFree(False)    # alterar a pista para ocupada
                        gare.setFree(False)     # alterar a gare para ocupada

                        ## informar o gestor de gares que a gare esta reservada
                        msg = Message(to=self.get('GestorGaresID'))
                        msg.set_metadata('performative', 'inform_reserved_gare')
                        msg.body = jsonpickle.encode(gare)
                        await self.send(msg)


                        ## comunicar ao aviao a pista e a gare
                        msg = Message(to=aviao.getId())
                        msg.set_metadata('performative', 'positive_landing')
                        msg.body = jsonpickle.encode({'pista':pista,'gare':gare})
                        await self.send(msg)
                    
                    else:
                        ## comunicar ao aviao para aguardar
                        msg = Message(to=aviao.getId())
                        msg.set_metadata('performative', 'negative_landing')
                        msg.body = jsonpickle.encode({'status':'aguardar'})
                        await self.send(msg)
                
                
                ## resposta negativa por parte do gestor de gares
                elif performative == 'negative_gare':
                    ## comunicar ao aviao para aguardar
                    msg = Message(to=str(received.getId()))
                    msg.set_metadata('performative', 'negative_landing')
                    msg.body = jsonpickle.encode({'status':'aguardar'})

                    await self.send(msg)

                
                ## pedido de pista livre por parte do gestor de gares
                elif performative == 'lane_request':
                    gare = received                                             # gare ocupada pelo aviao
                    aviao = received.getAviao()                                 # aviao que quer descolar
                    pista = get_closest_lane_to_gare(self.get('pistas'), gare)  # pista livre mais proxima para o aviao descolar
                    if pista: pista.setFree(False)                              # alterar a pista para ocupada

                    performative = 'positive_lane' if pista else 'negative_lane'
                    body = {'aviao':aviao, 'pista':pista} if pista else aviao
                    
                    ## comunicar ao gestor de gares se há pista livre ou não
                    msg = Message(to=self.get('GestorGaresID'))
                    msg.set_metadata('performative', performative)
                    msg.body = jsonpickle.encode(body)

                    await self.send(msg)
                
                
                ## mensagem do aviao a informar a desocupação da pista
                elif performative == 'inform_free_lane':
                    aviao = received.get('aviao')
                    pista = received.get('pista')

                    pista.setFree(True)
                    self.set('pistas', [pista if item == pista else item for item in self.get('pistas')])
                    
                    if aviao in self.agent.aterragens:
                        self.agent.aterragens.remove(aviao)
                

                ## mensagem do gestor de gares com informação das gares
                elif performative == 'gares_info':
                    self.agent.gares = received
                    self.agent.descolagens = get_avioes_descolar(received)
                

                ## mensagem de um aviao a informar que vao aterrar noutro aeroporto
                elif performative == 'aviao_inform':
                    if received in self.agent.aterragens:
                        self.agent.aterragens.remove(received)