import jsonpickle

from utils.functions import printInfo

from spade import agent
from spade.behaviour import CyclicBehaviour


class Info(agent.Agent):

    async def setup(self):
        print("Agent {}".format(str(self.jid)) + " starting...")

        ## Behaviours
        self.info = self.Info()
        self.add_behaviour(self.info)
    

    class Info(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=10)
            
            if msg:
                performative = msg.get_metadata('performative')

                if performative == 'global_inform':
                    received = jsonpickle.decode(msg.body)
                    printInfo(received)