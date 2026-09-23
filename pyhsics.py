import numpy as np
from pyparsing import Optional
import scipy as sp
from scipy import constants
from scipy.integrate import solve_ivp
import time
import matplotlib.pyplot as plt


DTYPE = np.float64

class Hierarchy:
    def __init__(self) -> None:
        self.hierarchy = {}

    def __repr__(self):
         return str(self.hierarchy)

    def add(self, target: PhysObject | FixObject, parent: PhysObject | FixObject = None):
        self.hierarchy[target] = parent if parent is not None else None
        
    def getParent(self, target):
        return self.hierarchy[target]

    def getSiblings(self, target):

           return [
            other
            for other in self.hierarchy.keys()
            if self.hierarchy[other] is self.hierarchy[target] and other is not target
        ]

    def setparent(self, target: PhysObject | FixObject, new_parent: PhysObject | FixObject):
        self.hierarchy[target] = new_parent
        target.parent = new_parent
        





class FixObject:
    def __init__(self, name, radius, mass, position, velocity):
        hierarchy.add(self, None)
        self.name = name
        self.radius = radius
        self.mass = mass
        self.position = np.asarray(position, dtype=float)
        self.velocity = np.asarray(velocity, dtype=float)

        self.mu = constants.G * self.mass
        self.soi_radius = 1e67
        self.parent = None
        
        

    def __repr__(self) -> str:
            return self.name 

    def update(self, dt):
        self.move(self.velocity, dt)

    
    def move(self, velocity, dt):
        self.position += velocity * dt

    def getState(self, t, orbital_period = None, orbit = None):
            
                    return self.position
            

    

    

class PhysObject:
    def __init__(self, name, radius, mass, position, velocity, parent = None):

        hierarchy.add(self, parent)
        self.name = name
        self.radius = radius
        self.mass = mass
        self.parent = parent
        self.position = np.asarray(position, dtype=DTYPE)
        self.velocity = np.asarray(velocity, dtype=DTYPE)
        self.acceleration = np.array([ 0, 0, 0], dtype=DTYPE)
        
        self.mu = constants.G * self.mass
        self.dt = self.getOrbitalPeriod()
        self.soi_radius = self.getSoiRadius()
        self.orbit = self.calcintegral()

        

    def __repr__(self) -> str:
        return self.name  

    
    def getOrbitalPeriod(self, r = None, v = None, parent = None):  # -----> float Orbital Period in seconds
        """calculates orbital period of object at current position and velocity, raises exception as orbital period gety virtually infinite"""

        r = self.position if r is None else r
        v = self.velocity if v is None else v
        parent = self.parent if parent is None else parent

        #--------- calculate normed postition and velocity
        norm_r = np.linalg.norm(r)
        norm_v = np.linalg.norm(v)

        #-------- fatass formula: T[seconds] = 2Pi* mu * ( (2mu/r - v^2) ^(-3/2))
        with np.errstate(invalid='ignore'):
            t = 2 * constants.pi * parent.mu * ((((2*parent.mu )/norm_r) - norm_v**2)**(-3/2))
        if np.isnan(t):
            t = 1000

        return t

    def getState(self, t, orbital_period = None, orbit = None): 
        """get position [:3] and velocity [3:] of  self with orbital period and orbit self if not specified"""

        orbital_period = self.dt if orbital_period is None else orbital_period
        orbit = self.dt if orbit is None else orbit

        return self.orbit.sol(t % orbital_period)


    def checkSoi(self, t, target: PhysObject | FixObject) -> float:
         """claculates distance to target Soi, >0 for outside, <0 for inside, 0 for border"""

         position = self.getState(t)[:3]
         target_postion = target.getState(t)[:3]

         distance = np.linalg.norm(position - target_postion)

         return distance - target.soi_radius

    def changeparent(self, new_parent):
        hierarchy.setparent(self, new_parent)
        self.soi_radius = self.getSoiRadius()
        #self.orbit = self.calcintegral()
        #self.dt = self.getOrbitalPeriod()

    def getSoiRadius(self):
        parent = hierarchy.getParent(self)

        return np.linalg.norm(self.position - parent.position) * ((self.mass/parent.mass)**(2/5)) if parent is not None else 1e67



    def calcintegral(self, r=None, v=None, parent=None, siblings: Optional[list] = None):    #------>.y matrix [:3] for position , [3:] for velocity , .sol(t) for matrix at time t
        self.dt = self.getOrbitalPeriod(r, v, parent)
        r = self.position if r is None else r
        v = self.velocity if v is None else v
        parent = self.parent if parent is None else parent
        state0 = np.concatenate((r, v)).astype(DTYPE)


        def derivative(t, state):       #--------> function of gravity to feed into solve_ivp
            position = state[:3]
            velocity = state[3:]

            relative_r = position - parent.position
            distance = np.linalg.norm(relative_r)

            acceleration = -parent.mu * relative_r / distance**3

            return np.concatenate((velocity, acceleration))

        def eventMaker(target):

            def soi_event(t, state):
                spacecraft_position = state[:3]
                target_position = target.getState(t)[:3]

                distance = np.linalg.norm(
                    spacecraft_position - target_position
                )

                return distance - target.soi_radius

            event = soi_event  # type: Any
            event.direction = 0
            event.terminal = True

            return event

        targets = hierarchy.getSiblings(self) if siblings is None else siblings
        targets.append(hierarchy.getParent(self))
        events = [eventMaker(target) for target in targets]
        #print(events)
        solution = solve_ivp(
            derivative,
            (0, self.dt),
            state0,
            method='DOP853',
            events=events,
            dense_output=True,
            atol = 1e-6,
            rtol = 1e-6
        )

        
        for event_target, event_time in zip(targets, solution.t_events or []):
            if len(event_time) > 0:
                print('Soi change with:', event_target, 'at', event_time, 's, at location', solution.y_events)
                self.dt = event_time[0]
                self.changeparent(event_target)
                self.position = solution.sol(event_time[0])[:3]
                self.velocity = solution.sol(event_time[0])[3:]
                

        return solution


#dt = 2000000000
hierarchy = Hierarchy()


Earth = FixObject('Earth', 6.671e6, 5.972e24 , (0,0,0), (0,0,0))

#Moon = PhysObject( 1, 10000, (100000+ Earth.radius, 0, 0), (0,10850.5,0), parent=Earth)
Moon = PhysObject('Moon', 1, 7.34767309e22, np.array([384399000, 0, 0], dtype=DTYPE), np.array([0,1018,0], dtype=DTYPE), parent=Earth)

Ship = PhysObject('Ship', 1, 2000, np.array([-36000000, 0, 0], dtype=DTYPE), np.array([1900,-4048,0], dtype=DTYPE), parent=Earth)

start_time = time.time()

solutionMoon =  Moon.orbit
solutionShip =  Ship.orbit
print(hierarchy)
print(hierarchy.getSiblings(Ship))

# --------- debug printing
#print(solutionShip)
print("Final position:", solutionShip.y[:3 , -1])
print("Final velocity:", solutionShip.y[3: ,-1])
print("Orbital Period:", Ship.dt)
position_difference = Moon.position - solutionMoon.y[:3, -1]
print("position difference:", position_difference)

print(time.time()-start_time)





#   ---------- matplotlib visualization---------------------------------
t = np.linspace(0, Moon.dt, 10000)
tship = np.linspace(0, Ship.dt,1000)
states = solutionMoon.sol(t)
statesship = solutionShip.sol(tship)

# Position is states[0:3]
x = states[0]
y = states[1]
z = states[2]

# Velocity is states[3:6]
vx = states[3]
vy = states[4]
vz = states[5]

fig = plt.figure(figsize=(8, 8))
ax = fig.add_subplot(111, projection='3d')

ax.plot(x, y, z, label='Moon trajectory', color='green')
ax.scatter(
    Earth.position[0],
    Earth.position[1],
    Earth.position[2],
    color='blue',
    s=100,
    label='Earth',
    marker='o'
)

ax.scatter(
    x[0],
    y[0],
    z[0],
    color='red',
    s=50,
    label='Moon start'
)

# Position is states[0:3]
x2 = statesship[0]
y2 = statesship[1]
z2 = statesship[2]

# Velocity is states[3:6]
vx2 = statesship[3]
vy2 = statesship[4]
vz2 = statesship[5]

ax.plot(x2, y2, z2, label='Ship trajectory', color='yellow')



Ship2 = Ship.calcintegral()
tship2 = np.linspace(0, Ship.dt,1000)
statesship2 = Ship2.sol(tship2)
print(statesship2)
#Position is states[0:3]
x3 = statesship2[0]
y3 = statesship2[1]
z3 = statesship2[2]
#Velocity is states[3:6]
vx3 = statesship2[3]
vy3 = statesship2[4]
vz3 = statesship2[5]

ax.plot(x3, y3, z3, label='Ship2 trajectory', color='yellow')




ax.axis('equal')
ax.set_xlabel('X [m]')
ax.set_ylabel('Y [m]')
ax.set_zlabel('Z [m]')
ax.set_title('Moon trajectory')
ax.legend()

plt.show()


