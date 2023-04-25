import asyncio
import jsonpickle

from spade import agent
from spade.message import Message
from spade.behaviour import OneShotBehaviour
from spade.behaviour import CyclicBehaviour


T1 = 20 # tempo de operação entre o avião e a pista de aterragem
T2 = 10 # tempo de circulação na pista
T3 = 10 # tempo de deslocação entre a pista e a gare
T4 = 60 # tempo de espera para voltar a realizar pedido de descolagem/aterragem


class AviaoAgent(agent.Agent):
    
    async def setup(self):
        print("Agent {}".format(str(self.jid)) + " starting...")

        ## Estado

        ## Behaviours
        self.request = self.RequestLandingOrTakeOff()
        self.response = self.AwaitLandingOrTakeOff()
        
        self.add_behaviour(self.request)
        self.add_behaviour(self.response)
    

    class RequestLandingOrTakeOff(OneShotBehaviour):
        async def run(self):
            operation = self.get('aviao').getOperation()
            performative = 'landing_request' if operation == 'aterrar' else 'takeoff_request'
            receiver = self.get('TorreControloID') if operation == 'aterrar' else self.get('GestorGaresID')

            msg = Message(to=receiver)
            msg.set_metadata('performative', performative)
            msg.body = jsonpickle.encode(self.get('aviao'))

            await self.send(msg)


    class AwaitLandingOrTakeOff(CyclicBehaviour):
        async def run(self):
            ## esperar pela resposta da torre ou do gestor de gares
            msg = await self.receive(timeout=120)

            if msg:
                performative = msg.get_metadata('performative')
                print('Aviao: ' + performative)
                received = jsonpickle.decode(msg.body)
                
                
                ## resposta positiva para aterrar e estacionar
                if performative == 'positive_landing':
                    pista = received.get('pista')
                    gare = received.get('gare')
                    
                    ## sleep - simular o tempo de aterragem
                    await asyncio.sleep(T1+T2)
                    ## informar a torre que a pista esta livre
                    msg1 = Message(to=self.get('TorreControloID'))
                    msg1.set_metadata('performative', 'inform_free_lane')
                    msg1.body = jsonpickle.encode({'aviao':self.get('aviao'), 'pista':pista})
                    await self.send(msg1)

                    ## sleep - simular o tempo de estacionamento
                    await asyncio.sleep(T3)
                    ## informar o gestor de gares que a gare esta ocupada
                    msg2 = Message(to=self.get('GestorGaresID'))
                    msg2.set_metadata('performative', 'inform_occupied_gare')
                    msg2.body = jsonpickle.encode({'gare':gare, 'aviao':self.get('aviao')})
                    await self.send(msg2)

                    self.kill()
                

                ## resposta negativa para aterrar
                elif performative == 'negative_landing':
                    status = received.get('status')
                    
                    ## dirigir-se para outro aeroporto
                    if status == 'aeroporto':
                        print("Agent {}".format(self.agent.jid) + ": vou dirigir-me para outro aeroporto.")
                        self.kill()
                    ## aguardar
                    elif status == 'aguardar':
                        await asyncio.sleep(T4)
                        self.agent.add_behaviour(self.agent.RequestLandingOrTakeOff())
                
                
                ## resposta positiva para descolar
                elif performative == 'positive_takeoff':
                    pista = received.get('pista')   # pista livre para descolar
                    gare = received.get('gare')     # gare onde o aviao está
                    
                    ## sleep - simular o tempo gare-pista
                    await asyncio.sleep(T3)
                    ## informar o gestor de gares que a gare esta livre
                    msg1 = Message(to=self.get('GestorGaresID'))
                    msg1.set_metadata('performative', 'inform_free_gare')
                    msg1.body = jsonpickle.encode(gare)
                    await self.send(msg1)

                    ## sleep - simular o tempo de descolagem
                    await asyncio.sleep(T1+T2)
                    ## informar a torre que a pista esta livre
                    msg2 = Message(to=self.get('TorreControloID'))
                    msg2.set_metadata('performative', 'inform_free_lane')
                    msg2.body = jsonpickle.encode({'aviao':self.get('aviao'), 'pista':pista})
                    await self.send(msg2)

                    self.kill()
                

                ## resposta negativa para descolar
                elif performative == 'negative_takeoff':
                    status = received.get('status')
                    
                    ## aguardar e voltar a mandar pedido
                    if status == 'aguardar':
                        await asyncio.sleep(T4)
                        self.agent.add_behaviour(self.agent.RequestLandingOrTakeOff())
            
            
            else:
                ## informar torre que irá aterrar noutro aeroporto
                if self.get('aviao').getOperation() == 'aterrar':
                    msg = Message(to=self.get('TorreControloID'))
                    msg.body = jsonpickle.encode(self.get('aviao'))
                    msg.set_metadata('performative', 'aviao_inform')
                    await self.send(msg)
                    self.kill()