import random
import asyncio
import jsonpickle

from spade import agent
from spade.message import Message
from spade.behaviour import OneShotBehaviour
from spade.behaviour import CyclicBehaviour

from utils.functions import AEROPORTOS


T1 = 20 # tempo de operação entre o avião e a pista de aterragem
T2 = 10 # tempo de circulação na pista
T3 = 10 # tempo de deslocação entre a pista e a gare
T4 = 40 # tempo de espera para voltar a realizar pedido de descolagem/aterragem
T5 =  5 # tempo que um avião privado está na gare
T6 = 15 # tempo que um aviao não privado está na gare


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
            if operation != 'finalizado':
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
                ## CONTEÚDO: pista, gare e metereologia
                ## DESCRIÇÃO: resposta positiva para aterrar e estacionar
                ## RESPOSTA: alterar a operação do aviao
                ##           aterrar circular na pista e avisar a torre controlo que a pista está livre
                ##           circular da pista à gare e avisar o gestor que a gare está ocupada
                ##           se for privado, simular tempo de saída da gare, avisar o gestor e sair do sistema
                ##           caso contrário, após um tempo de espera altera-se o estado do avião e realiza-se um pedido de takeoff
                if performative == 'landing_request_accept':
                    pista = received.get('pista')
                    gare = received.get('gare')
                    metereologia = received.get('metereologia')
                    print('LANDING -> METEREOLOGIA: ' + str(metereologia) + ' Valor: ' + str(metereologia.value))
                    
                    aviao = self.get('aviao')
                    aviao.setOperation('finalizado')
                    self.set('aviao',aviao)

                    gare.setFree(False)
                    gare.setAviao(aviao)
                    
                    pista.setFree(True)

                    await asyncio.sleep((T1+T2)*metereologia.value)
                    msg = Message(to=self.get('TorreControloID'))
                    msg.set_metadata('performative', 'free_lane_inform')
                    msg.body = jsonpickle.encode({'aviao':aviao, 'pista':pista})
                    await self.send(msg)

                    await asyncio.sleep(T3*metereologia.value)
                    msg = Message(to=self.get('GestorGaresID'))
                    msg.set_metadata('performative', 'occupied_gare_inform')
                    msg.body = jsonpickle.encode(gare)
                    await self.send(msg)

                    if aviao.getTipo() == 'privado':
                        await asyncio.sleep(T5)
                        gare.setFree(True)
                        gare.setAviao(None)

                        msg = Message(to=self.get('GestorGaresID'))
                        msg.set_metadata('performative','free_gare_inform')
                        msg.body = jsonpickle.encode(gare)
                        await self.send(msg)
                        self.kill()

                    else:
                        await asyncio.sleep(T6)
                        aviao.setOperation('descolar')
                        aviao.setOrigem(aviao.getDestino())
                        aviao.setDestino(random.choice(AEROPORTOS))
                        self.set('aviao',aviao)

                        msg = Message(to=self.get('GestorGaresID'))
                        msg.set_metadata('performative','change_state_inform')
                        msg.body = jsonpickle.encode({'gare':gare, 'aviao':aviao})
                        await self.send(msg)

                        self.agent.add_behaviour(self.agent.RequestLandingOrTakeOff())
                

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
                ## CONTEÚDO: pista, gare e metereologia
                ## DESCRIÇÃO: resposta positiva para descolar
                ## RESPOSTA: circular da gare até à pista e informar o gestor que a gare está livre
                ##           circular na pista para descolar e informar a torre que a pista está livre
                ##           sair do sistema
                elif performative == 'takeoff_request_accept':
                    pista = received.get('pista')
                    gare = received.get('gare')
                    metereologia = received.get('metereologia')
                    print('TAKEOFF -> METEREOLOGIA: ' + str(metereologia) + ' Valor: ' + str(metereologia.value))

                    gare.setFree(True)
                    gare.setAviao(None)

                    pista.setFree(True)
                    
                    await asyncio.sleep(T3*metereologia.value)
                    msg = Message(to=self.get('GestorGaresID'))
                    msg.set_metadata('performative', 'free_gare_inform')
                    msg.body = jsonpickle.encode(gare)
                    await self.send(msg)
                    
                    await asyncio.sleep((T1+T2)*metereologia.value)
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