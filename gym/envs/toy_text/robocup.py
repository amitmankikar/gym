import sys
from six import StringIO
from gym import utils
from gym.envs.toy_text import discrete
import numpy as np

MAP = [
    "+-------+",
    "|A: : :B|",
    "|A: : :B|",
    "+-------+",
]

class RobocupEnv(discrete.DiscreteEnv):
    """
    
    Pending things: build __init__
    Rewards must be vectorized
    Action must be vectorized
    Action must have only 5 instead of 6 

    """
    metadata = {'render.modes': ['human', 'ansi']}

    def __init__(self):
        self.desc = np.asarray(MAP,dtype='c')

        self.locs = locs = [(0,0), (0,3), (1,0), (1,3)]

        nS = 21976
        nR = 2
        nC = 4
        maxR = nR-1
        maxC = nC-1
        isd = np.zeros(nS)
        nA = 6
        P = {s : {a : [] for a in range(nA)} for s in range(nS)}
        for row in range(nR):
            for col in range(nC):
                for passidx in range(len(locs)+1):
                    for destidx in range(len(locs)):
                        state = self.encode(row, col, passidx, destidx, 0, 0)
                        if passidx < 4 and passidx != destidx:
                            isd[state] += 1
                        for a in range(nA):
                            # defaults
                            newrow, newcol, newpassidx = row, col, passidx
                            reward = -1
                            done = False
                            taxiloc = (row, col)

                            if a==0:
                                newrow = min(row+1, maxR)
                            elif a==1:
                                newrow = max(row-1, 0)
                            if a==2 and self.desc[1+row,2*col+2]==b":":
                                newcol = min(col+1, maxC)
                            elif a==3 and self.desc[1+row,2*col]==b":":
                                newcol = max(col-1, 0)
                            elif a==4: # pickup
                                if (passidx < len(locs) and taxiloc == locs[passidx]):
                                    newpassidx = len(locs)
                                else:
                                    reward = -10
                            elif a==5: # dropoff
                                if (taxiloc == locs[destidx]) and passidx==len(locs):
                                    newpassidx = destidx
                                    done = True
                                    reward = 100
                                elif (taxiloc in locs) and passidx==len(locs):
                                    newpassidx = locs.index(taxiloc)
                                else:
                                    reward = -10
                            newstate = self.encode(newrow, newcol, newpassidx, destidx, 0, 0)
                            P[state][a].append((1.0, newstate, reward, done))
        isd /= isd.sum()
        discrete.DiscreteEnv.__init__(self, nS, nA, P, isd)

    def encode(self, p1row, p1col, passloc, destidx, p2row, p2col):
        d = 6
        i = p1row+1
        i *= d
        i += p1col+1
        i *= d
        i += passloc+1
        i *= d
        i += destidx+1
        i *= d
        i += p2row+1
        i *= d
        i += p2col+1
        return i

    def decode(self, i):
        d = 6
        out = []
        out.append( (i % d) -1)
        i = i // d
        out.append( (i % d) -1)
        i = i // d
        out.append( (i % d) -1)
        i = i // d
        out.append( (i % d) -1)
        i = i // d
        out.append( (i % d) -1)
        i = i // d
        out.append( (i % d) -1)
        assert 0 <= i < d
        return reversed(out)

    def render(self, mode='human'):
        outfile = StringIO() if mode == 'ansi' else sys.stdout

        out = self.desc.copy().tolist()
        out = [[c.decode('utf-8') for c in line] for line in out]
        taxirow, taxicol, passidx, destidx, p2row, p2col = self.decode(self.s)

#        print taxirow, taxicol, passidx, destidx, ["South", "North", "East", "West", "Pickup", "Dropoff"][self.lastaction]

        def ul(x): return "_" if x == " " else x
        if passidx < 4:
            out[1+taxirow][2*taxicol+1] = utils.colorize(out[1+taxirow][2*taxicol+1], 'yellow', highlight=True)
            pi, pj = self.locs[passidx]
            out[1+pi][2*pj+1] = utils.colorize(out[1+pi][2*pj+1], 'blue', bold=True)
        else: # passenger in taxi
            out[1+taxirow][2*taxicol+1] = utils.colorize(ul(out[1+taxirow][2*taxicol+1]), 'green', highlight=True)

        di, dj = self.locs[destidx]
        out[1+di][2*dj+1] = utils.colorize(out[1+di][2*dj+1], 'magenta')
        outfile.write("\n".join(["".join(row) for row in out])+"\n")
        if self.lastaction is not None:
            outfile.write("  ({})\n".format(["South", "North", "East", "West", "Pickup", "Dropoff"][self.lastaction]))
        else: outfile.write("\n")

        # No need to return anything for human
        if mode != 'human':
            return outfile
