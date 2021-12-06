"""
Simulate multiple games between two or more bots. 

"""
from pyminion.bots.examples import BigMoney, BigMoneySmithy
from pyminion.expansions.base import base_set, smithy
from pyminion.game import Game
from pyminion.simulator import Simulator

bm = BigMoney()
bm_smithy = BigMoneySmithy()


game = Game(players=[bm, bm_smithy], expansions=[base_set], kingdom_cards=[smithy])

sim = Simulator(game, iterations=1000)

if __name__ == "__main__":
    sim.run()
