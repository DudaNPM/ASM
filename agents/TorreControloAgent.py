import random
import datetime
import jsonpickle

from utils.gare import Gare
from utils.aviao import Aviao

from spade import agent
from spade.message import Message
from spade.behaviour import CyclicBehaviour
from spade.behaviour import PeriodicBehaviour

from utils.metereologia import Metereologia

from utils.functions import get_avioes_descolar
from utils.functions import get_closest_lane_to_gare
from utils.functions import get_closest_lane_and_gare



MAX = 5 # número máximo de aviões em fila de espera para aterrar



class TorreControlo(agent.Agent):

    gares = list[Gare]()
    aterragens = list[Aviao]()
    descolagens = list[Aviao]()
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
        self.info = self.Info(period=10,start_at=datetime.datetime.now() + datetime.timedelta(seconds=2))
        self.control = self.Control()

        self.add_behaviour(self.info)
        self.add_behaviour(self.control)
    

    class Info(PeriodicBehaviour):
        async def run(self):
            body = {'gares':self.agent.gares, 'aterragens':self.agent.aterragens, 'descolagens':self.agent.descolagens, 'pistas':self.get('pistas')}
            msg = Message(to=self.get('InfoID'))
            msg.set_metadata('performative', 'global_inform')
            msg.body = jsonpickle.encode(body)
            await self.send(msg)


    class Control(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=10)
            
            if msg:
                performative = msg.get_metadata('performative')
                received = jsonpickle.decode(msg.body)
                print('TorreControlo: ' + performative)

                
                ## DE: aviao
                ## CONTEÚDO: aviao
                ## DESCRIÇÃO: pedido de aterragem por parte de um aviao
                ## RESPOSTA: verififcar metereologia
                ##           verificar se o aviao é privado, se for, ignora a fila de espera e tem acesso direto à gare
                ##           verificar se o aviao ja esta em fila de espera ou
                ##           verificar se o limite máximo de aviões em fila de espera não foi atingido, se sim processar pedido
                ##           caso contrário, mandar o aviao aterrar noutro aeroporto
                if performative == 'landing_request':
                    metereologia = random.choice(self.agent.metereologia)

                    if metereologia == Metereologia.FURACAO:
                        target = received.getId()
                        performative = 'landing_request_refuse'
                        body = {'status':'aguardar'}

                    elif received.getTipo() == 'privado':
                        if received not in self.agent.aterragens:
                            self.agent.aterragens.append(received)
                        
                        target = received.getId()
                        pista, gare = get_closest_lane_and_gare(self.get('pistas'), [self.agent.gares[0]])

                        if pista:
                            pista.setFree(False)
                            self.set('pistas', [pista if item == pista else item for item in self.get('pistas')])
                        
                        performative = 'landing_request_accept' if pista else 'landing_request_refuse'
                        body = {'pista':pista,'gare':gare,'metereologia':metereologia} if pista else {'status':'aguardar'}

                    elif received in self.agent.aterragens:
                        target = self.get('GestorGaresID')
                        performative = 'free_gares_request'
                        body = received
                    
                    elif len(self.agent.aterragens) < MAX:
                        self.agent.aterragens.append(received)
                        
                        target = self.get('GestorGaresID')
                        performative = 'free_gares_request'
                        body = received
                    
                    else:
                        target = received.getId()
                        performative = 'landing_request_refuse'
                        body = {'status':'aeroporto'}
                    
                    msg = Message(to=target)
                    msg.set_metadata('performative',performative)
                    msg.body = jsonpickle.encode(body)
                    await self.send(msg)

                

                ## DE: gestor de gares
                ## CONTEÚDO: pista, aviao e gares
                ## DESCRIÇÃO: lista de gares livres para o avião estacionar
                ## RESPOSTA: se houver uma pista no conteúdo alterar o seu estado para livre (porque era uma pista reservada anteriormente)
                ##           calcular a pista e gare mais próximos
                ##           se houver pista confirmar com o gestor de gares a reserva da gare
                ##           se não houver pista comunicar ao avião para aguardar
                elif performative == 'free_gares_accept':
                    pista = received.get('pista')
                    aviao = received.get('aviao')
                    gares = received.get('gares')

                    if pista:
                        pista.setFree(True)
                        self.set('pistas', [pista if item == pista else item for item in self.get('pistas')])

                    pista, gare = get_closest_lane_and_gare(self.get('pistas'), gares)
                    
                    if pista:
                        pista.setFree(False)
                        self.set('pistas', [pista if item == pista else item for item in self.get('pistas')])
                    
                    target = self.get('GestorGaresID') if pista else aviao.getId()
                    performative = 'gare_request' if pista else 'landing_request_refuse'
                    body = {'gare':gare, 'pista':pista, 'aviao':aviao} if pista else {'status':'aguardar'}
                    
                    msg = Message(to=target)
                    msg.set_metadata('performative',performative)
                    msg.body = jsonpickle.encode(body)
                    await self.send(msg)
                
                

                ## DE: gestor de gares
                ## CONTEÚDO: pista e aviao
                ## DESCRIÇÃO: não existem gares livres
                ## RESPOSTA: se houver uma pista no conteúdo alterar o seu estado para livre (porque era uma pista reservada anteriormente)
                ##           comunicar ao avião para aguardar
                elif performative == 'free_gares_refuse':
                    pista = received.get('pista')
                    aviao = received.get('aviao')
                    
                    if pista:
                        pista.setFree(True)
                        self.set('pistas', [pista if item == pista else item for item in self.get('pistas')])
                    
                    msg = Message(to=str(aviao.getId()))
                    msg.set_metadata('performative','landing_request_refuse')
                    msg.body = jsonpickle.encode({'status':'aguardar'})
                    await self.send(msg)



                ## DE: gestor de gares
                ## CONTEÚDO: pista, aviao e gare
                ## DESCRIÇÃO: confirmação da gare escolhida
                ## RESPOSTA: comunicar ao avião a pista, a gare e a metereologia em questão
                elif performative == 'gare_request_accept':
                    gare = received.get('gare')
                    pista = received.get('pista')
                    aviao = received.get('aviao')

                    self.agent.metereologia.remove(Metereologia.FURACAO)
                    metereologia = random.choice(self.agent.metereologia)
                    self.agent.metereologia.append(Metereologia.FURACAO)
                    
                    msg = Message(to=aviao.getId())
                    msg.set_metadata('performative', 'landing_request_accept')
                    msg.body = jsonpickle.encode({'pista':pista,'gare':gare,'metereologia':metereologia})
                    await self.send(msg)
                

                
                ## DE: gestor de gares
                ## CONTEÚDO: gare
                ## DESCRIÇÃO: pedido de pista livre
                ## RESPOSTA: calcular a pista livre mais próxima da gare
                ##           se houver, alterar o seu estado e comunicar ao gestor
                ##           caso contrário, comunicar ao gestor que não há
                elif performative == 'free_lane_request':
                    aviao = received.getAviao()
                    pista = get_closest_lane_to_gare(self.get('pistas'), received)
                    
                    if pista:
                        pista.setFree(False)
                        self.set('pistas', [pista if item == pista else item for item in self.get('pistas')])

                    performative = 'free_lane_accept' if pista else 'free_lane_refuse'
                    body = {'aviao':aviao, 'pista':pista} if pista else aviao
                    
                    msg = Message(to=self.get('GestorGaresID'))
                    msg.set_metadata('performative', performative)
                    msg.body = jsonpickle.encode(body)
                    await self.send(msg)
                
                

                ## DE: aviao
                ## CONTEÚDO: aviao e pista
                ## DESCRIÇÃO: mensagem do aviao a informar a desocupação da pista
                ## RESPOSTA: atualizar as pistas
                ##           remover o avião da lista de aterragens
                elif performative == 'free_lane_inform':
                    aviao = received.get('aviao')
                    pista = received.get('pista')

                    self.set('pistas', [pista if item == pista else item for item in self.get('pistas')])
                    
                    if aviao in self.agent.aterragens:
                        self.agent.aterragens.remove(aviao)
                


                ## DE: gestor
                ## CONTEÚDO: lista de gares
                ## DESCRIÇÃO: mensagem do gestor de gares com informação das gares
                ## RESPOSTA: atualizar a informação das gares
                ##           atualizar a lista de descolagens
                elif performative == 'gares_inform':
                    self.agent.gares = received
                    self.agent.descolagens = get_avioes_descolar(received)
                


                ## DE: aviao
                ## CONTEÚDO: avião
                ## DESCRIÇÃO: mensagem de um aviao a informar que vai aterrar noutro aeroporto
                ## RESPOSTA: atualizar a lista de aterragens
                elif performative == 'aviao_inform':
                    if received in self.agent.aterragens:
                        self.agent.aterragens.remove(received)