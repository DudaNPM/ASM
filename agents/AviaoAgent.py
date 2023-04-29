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
            msg = await self.receive(timeout=50)

            if msg:
                performative = msg.get_metadata('performative')
                received = jsonpickle.decode(msg.body)
                print('Aviao: ' + performative)
                
                
                ## DE: torre controlo
                ## CONTEÚDO: pista e gare
                ## DESCRIÇÃO: resposta positiva para aterrar e estacionar
                ## RESPOSTA: alterar a operação do aviao
                ##           aterrar circular na pista e avisar a torre controlo que a pista está livre
                ##           circular da pista à gare e avisar o gestor que a gare está ocupada
                if performative == 'landing_request_accept':
                    pista = received.get('pista')
                    gare = received.get('gare')
                    
                    aviao = self.get('aviao')
                    aviao.setOperation('finalizado')
                    self.set('aviao',aviao)
                    
                    await asyncio.sleep(T1+T2)
                    msg = Message(to=self.get('TorreControloID'))
                    msg.set_metadata('performative', 'free_lane_inform')
                    msg.body = jsonpickle.encode({'aviao':aviao, 'pista':pista})
                    await self.send(msg)

                    await asyncio.sleep(T3)
                    msg = Message(to=self.get('GestorGaresID'))
                    msg.set_metadata('performative', 'occupied_gare_inform')
                    msg.body = jsonpickle.encode({'gare':gare, 'aviao':aviao})
                    await self.send(msg)

                    self.kill()
                
                

                ## DE: torre controlo
                ## CONTEÚDO: status
                ## DESCRIÇÃO: resposta negativa para aterrar
                ## RESPOSTA: status == aeroporto, então sair do sistema
                ##           status ==  aguardar, então voltar a enviar request
                elif performative == 'landing_request_refuse':
                    status = received.get('status')

                    if status == 'aeroporto':
                        print("Agent {}".format(self.agent.jid) + ": vou dirigir-me para outro aeroporto.")
                        self.kill()
                    
                    elif status == 'aguardar':
                        await asyncio.sleep(T4)
                        self.agent.add_behaviour(self.agent.RequestLandingOrTakeOff())
                

                
                ## DE: gestor de gares
                ## CONTEÚDO: pista e gare
                ## DESCRIÇÃO: resposta positiva para descolar
                ## RESPOSTA: circular da gare até à pista e informar o gestor que a gare está livre
                ##           circular na pista para descolar e informar a torre que a pista está livre
                ##           sair do sistema
                elif performative == 'takeoff_request_accept':
                    pista = received.get('pista')
                    gare = received.get('gare')
                    
                    await asyncio.sleep(T3)
                    msg = Message(to=self.get('GestorGaresID'))
                    msg.set_metadata('performative', 'free_gare_inform')
                    msg.body = jsonpickle.encode(gare)
                    await self.send(msg)
                    
                    await asyncio.sleep(T1+T2)
                    msg = Message(to=self.get('TorreControloID'))
                    msg.set_metadata('performative', 'free_lane_inform')
                    msg.body = jsonpickle.encode({'aviao':self.get('aviao'), 'pista':pista})
                    await self.send(msg)

                    self.kill()
                


                ## DE: gestor de gares
                ## CONTEÚDO: status
                ## DESCRIÇÃO: resposta negativa para descolar
                ## RESPOSTA: status ==  aguardar, então voltar a enviar request
                elif performative == 'takeoff_request_refuse':
                    status = received.get('status')
                    
                    if status == 'aguardar':
                        await asyncio.sleep(T4)
                        self.agent.add_behaviour(self.agent.RequestLandingOrTakeOff())
            

            
            else:
                ## PARA: torre controlo
                ## CONTEÚDO: aviao
                ## DESCRIÇÃO: informar torre que irá aterrar noutro aeroporto
                ## RESPOSTA: enviar mensagem
                ##           sair do sistema
                if self.get('aviao').getOperation() == 'aterrar':
                    msg = Message(to=self.get('TorreControloID'))
                    msg.body = jsonpickle.encode(self.get('aviao'))
                    msg.set_metadata('performative', 'aviao_inform')
                    await self.send(msg)
                    
                    self.kill()