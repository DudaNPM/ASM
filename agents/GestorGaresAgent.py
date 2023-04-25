import jsonpickle

from spade import agent
from spade.message import Message
from spade.behaviour import CyclicBehaviour
from spade.behaviour import OneShotBehaviour

from utils.functions import get_free_gares
from utils.functions import get_occupied_gare



class GestorGares(agent.Agent):

    async def setup(self):
        print("Agent {}".format(str(self.jid)) + " starting...")

        ## Estado

        ## Behaviours
        self.info = self.GaresInfo()
        self.control = self.Control()
        self.add_behaviour(self.info)
        self.add_behaviour(self.control)


    class GaresInfo(OneShotBehaviour):
        async def run(self):
            gares = self.get('gares')
            msg = Message(to=self.get('TorreControloID'))
            msg.set_metadata('performative', 'gares_info')
            msg.body = jsonpickle.encode(gares)
            await self.send(msg)
    

    class Control(CyclicBehaviour):
        async def run(self):
            ## esperar por pedidos
            msg = await self.receive(timeout=10)
            
            if msg:
                performative = msg.get_metadata('performative')
                print('GestorGares: ' + str(performative))
                received = jsonpickle.decode(msg.body)

                
                ## pedido de descolagem por parte de um aviao
                if performative == 'takeoff_request':
                    gare = get_occupied_gare(self.get('gares'), received)   # gare onde o aviao está estacionado

                    ## pedir à torre uma pista livre
                    msg = Message(to=self.get('TorreControloID'))
                    msg.set_metadata('performative', 'lane_request')
                    msg.body = jsonpickle.encode(gare)

                    await self.send(msg)
                
                
                ## pedido de gare livre por parte da torre de controlo
                elif performative == 'gare_request':
                    aviao = received
                    gares = get_free_gares(self.get('gares'), aviao)

                    performative = 'positive_gare' if len(gares) > 0 else 'negative_gare'
                    body = {'aviao':aviao, 'gares':gares} if len(gares) > 0 else aviao

                    ## enviar mensagem para a torre de controlo com as gares livres mais próximas
                    msg = Message(to=self.get('TorreControloID'))
                    msg.set_metadata('performative', performative)
                    msg.body = jsonpickle.encode(body)

                    await self.send(msg)
                
                
                ## resposta positiva por parte da torre
                elif performative == 'positive_lane':
                    aviao = received.get('aviao')                       # aviao que quer descolar
                    pista = received.get('pista')                       # pista para descolar
                    gare = get_occupied_gare(self.get('gares'), aviao)  # gare onde o avião está estacionado
                    
                    ## enviar mensagem para o aviao com a pista livre
                    msg = Message(to=aviao.getId())
                    msg.set_metadata('performative', 'positive_takeoff')
                    msg.body = jsonpickle.encode({'pista':pista, 'gare':gare})

                    await self.send(msg)
                
                
                ## resposta negativa por parte da torre
                elif performative == 'negative_lane':
                    ## enviar mensagem para o aviao a informar que não há pista livre                    
                    msg = Message(to=received.getId())
                    msg.set_metadata('performative', 'negative_takeoff')
                    msg.body = jsonpickle.encode({'status':'aguardar'})

                    await self.send(msg)
                

                ## mensagem do aviao a informar a ocupação da gare
                elif performative == 'inform_occupied_gare':
                    gare = received.get('gare')     # gare que acababou de ser ocupada
                    aviao = received.get('aviao')   # avião que acabou de aterrar

                    gare.setFree(False)
                    gare.setAviao(aviao)
                    self.set('gares', [gare if item == gare else item for item in self.get('gares')])
                

                ## mensagem do aviao a informar a desocupação da gare
                elif performative == 'inform_free_gare':
                    received.setFree(True)
                    received.setAviao(None)
                    self.set('gares', [received if item == received else item for item in self.get('gares')])