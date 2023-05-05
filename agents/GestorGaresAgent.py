import random
import jsonpickle

from spade import agent
from spade.message import Message
from spade.behaviour import CyclicBehaviour
from spade.behaviour import OneShotBehaviour

from utils.metereologia import Metereologia

from utils.functions import get_free_gares
from utils.functions import get_occupied_gare



class GestorGares(agent.Agent):

    metereologia = [Metereologia.CEULIMPO,Metereologia.CEULIMPO,Metereologia.CEULIMPO,
                    Metereologia.SOL,Metereologia.SOL,Metereologia.SOL,
                    Metereologia.CHUVAFRACA,Metereologia.CHUVAFRACA,
                    Metereologia.VENTOFRACO,Metereologia.VENTOFRACO,
                    Metereologia.NEVE,Metereologia.NEVE,
                    Metereologia.VENTOFORTE,Metereologia.VENTOFORTE,
                    Metereologia.GRANIZO,Metereologia.GRANIZO,
                    Metereologia.CHUVAFORTE,
                    Metereologia.NEVOEIRO,
                    Metereologia.TEMPESTADE,
                    Metereologia.FURACAO]


    async def setup(self):
        print("Agent {}".format(str(self.jid)) + " starting...")

        ## Behaviours
        self.info = self.GaresInfo()
        self.control = self.Control()

        self.add_behaviour(self.info)
        self.add_behaviour(self.control)


    class GaresInfo(OneShotBehaviour):
        async def run(self):
            gares = self.get('gares')
            msg = Message(to=self.get('TorreControloID'))
            msg.set_metadata('performative', 'gares_inform')
            msg.body = jsonpickle.encode(gares)
            await self.send(msg)
    

    class Control(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=10)
            
            if msg:
                performative = msg.get_metadata('performative')
                received = jsonpickle.decode(msg.body)
                print('GestorGares: ' + performative)
                
                
                ## DE: aviao
                ## CONTEÚDO: aviao
                ## DESCRIÇÃO: pedido de descolagem
                ## RESPOSTA: verificar metereologia
                ##           calcular a gare ocupada pelo avião
                ##           pedir à torre de controlo uma pista livre
                if performative == 'takeoff_request':
                    metereologia = random.choice(self.agent.metereologia)
                    
                    if metereologia == Metereologia.FURACAO:
                        target = received.getId()
                        performative = 'takeoff_request_refuse'
                        body = {'status':'aguardar'}
                    
                    else:
                        gare = get_occupied_gare(self.get('gares'), received)

                        target = self.get('TorreControloID')
                        performative = 'free_lane_request'
                        body = gare

                    msg = Message(to=target)
                    msg.set_metadata('performative',performative)
                    msg.body = jsonpickle.encode(body)
                    await self.send(msg)
                
                
                ## DE: torre controlo
                ## CONTEÚDO: aviao
                ## DESCRIÇÃO: pedido de gares livres
                ## RESPOSTA: calcular as gares livres para o tipo de avião
                ##           informar a torre da existência ou não de gares livres
                elif performative == 'free_gares_request':
                    aviao = received
                    
                    gares = get_free_gares(self.get('gares'), aviao)
                    performative = 'free_gares_accept' if len(gares) > 0 else 'free_gares_refuse'
                    body = {'aviao':aviao, 'gares':gares, 'pista':None} if len(gares) > 0 else {'aviao':aviao, 'pista':None}
                    
                    msg = Message(to=self.get('TorreControloID'))
                    msg.set_metadata('performative', performative)
                    msg.body = jsonpickle.encode(body)
                    await self.send(msg)
                
                
                
                ## DE: torre controlo
                ## CONTEÚDO: aviao e pista
                ## DESCRIÇÃO: pista livre para o aviao descolar
                ## RESPOSTA: calcular a gare onde o avião está estacionado
                ##           informar o avião da pista livre para descolar e a metereologia em questão
                elif performative == 'free_lane_accept':
                    aviao = received.get('aviao')
                    pista = received.get('pista')
                    
                    gare = get_occupied_gare(self.get('gares'), aviao)

                    self.agent.metereologia.remove(Metereologia.FURACAO)
                    metereologia = random.choice(self.agent.metereologia)
                    self.agent.metereologia.append(Metereologia.FURACAO)

                    msg = Message(to=aviao.getId())
                    msg.set_metadata('performative','takeoff_request_accept')
                    msg.body = jsonpickle.encode({'pista':pista,'gare':gare,'metereologia':metereologia})
                    await self.send(msg)
                

                
                ## DE: torre controlo
                ## CONTEÚDO: aviao
                ## DESCRIÇÃO: não existe pista livre para aterrar
                ## RESPOSTA: enviar mensagem para o aviao a informar que não há pista livre
                elif performative == 'free_lane_refuse':
                    msg = Message(to=received.getId())
                    msg.set_metadata('performative','takeoff_request_refuse')
                    msg.body = jsonpickle.encode({'status':'aguardar'})
                    await self.send(msg)



                ## DE: aviao
                ## CONTEÚDO: gare
                ## DESCRIÇÃO: mensagem do aviao a informar a ocupação de uma gare
                ## RESPOSTA: atualizar as gares
                ##           enviar informação para o torre
                elif performative == 'occupied_gare_inform':
                    self.set('gares', [received if item == received else item for item in self.get('gares')])
                    self.agent.add_behaviour(self.agent.GaresInfo())

                

                ## DE: aviao
                ## CONTEÚDO: gare
                ## DESCRIÇÃO: mensagem do aviao a informar a desocupação de uma gare
                ## RESPOSTA: alterar o estado da gare
                ##           enviar informação para o torre
                elif performative == 'free_gare_inform':
                    self.set('gares', [received if item == received else item for item in self.get('gares')])
                    self.agent.add_behaviour(self.agent.GaresInfo())

                

                ## DE: torre de controlo
                ## CONTEÚDO: gare, pista e aviao
                ## DESCRIÇÃO: pedido de confirmação de gare livre por parte da torre de controlo
                ## RESPOSTA: se a gare estiver livre, alterar o seu estado e informar a torre
                ##           se a gare estiver ocupada, calcular a lista de gares livres e voltar a enviar à torre
                elif performative == 'gare_request':
                    gare = received.get('gare')
                    pista = received.get('pista')
                    aviao = received.get('aviao')
                    
                    gares = self.get('gares')
                    confirm = gares[gares.index(gare)]
                    
                    if confirm.getFree():
                        confirm.setFree(False)
                        self.set('gares', [confirm if item == confirm else item for item in self.get('gares')])
                        
                        self.agent.add_behaviour(self.agent.GaresInfo())

                        msg = Message(to=self.get('TorreControloID'))
                        msg.set_metadata('performative', 'gare_request_accept')
                        msg.body = jsonpickle.encode({'gare':gare, 'pista':pista, 'aviao':aviao})
                        await self.send(msg)
                    
                    else:
                        gares = get_free_gares(self.get('gares'), aviao)
                        performative = 'free_gares_accept' if len(gares) > 0 else 'free_gares_refuse'
                        body = {'aviao':aviao, 'gares':gares, 'pista':pista} if len(gares) > 0 else {'aviao':aviao,'pista':pista}

                        msg = Message(to=self.get('TorreControloID'))
                        msg.set_metadata('performative', performative)
                        msg.body = jsonpickle.encode(body)
                        await self.send(msg)
                


                ## DE: aviao
                ## CONTEÚDO: gare e aviao
                ## DESCRIÇÃO: novo estado de um avião estacionado
                ## RESPOSTA: atualizar o estado das gares
                ##           enviar info para a torre
                elif performative == 'change_state_inform':
                    gare = received.get('gare')
                    aviao = received.get('aviao')

                    gare.setAviao(aviao)
                    self.set('gares', [gare if item == gare else item for item in self.get('gares')])

                    self.agent.add_behaviour(self.agent.GaresInfo())