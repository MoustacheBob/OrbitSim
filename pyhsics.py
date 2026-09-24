import numpy as np
from typing import Any, Optional
import scipy as sp
from scipy import constants
from scipy.integrate import solve_ivp
import time
import matplotlib.pyplot as plt
import sched

DTYPE = np.float64

t0: float = time.time()
curtime: float = 0.0
timewarp: float = 1


def timefunc() -> float:
    global t0, curtime

    now = time.time()
    curtime += (now - t0) * timewarp
    t0 = now

    return curtime



class Hierarchy:
    def __init__(self) -> None:
        self.hierarchy = {}

    def __repr__(self):
         return str(self.hierarchy)

    def add(
        self,
        target: PhysObject | FixObject,
        parent: PhysObject | FixObject | None = None,
    ) -> None:
        self.hierarchy[target] = parent if parent is not None else None
        
    def getParent(self, target):
        return self.hierarchy[target]

    def getSiblings(self, target):

           return [
            other
            for other in self.hierarchy.keys()
            if self.hierarchy[other] is self.hierarchy[target] and other is not target
        ]

    def setparent(
        self,
        target: PhysObject | FixObject,
        new_parent: PhysObject | FixObject,
    ) -> None:
        self.hierarchy[target] = new_parent
        target.parent = new_parent
        





class FixObject:
    parent: PhysObject | FixObject | None

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
        return np.concatenate((self.position, self.velocity)).astype(DTYPE, copy=False)


    

class PhysObject:
    def __init__(self, name, radius, mass, position, velocity, parent = None):

        hierarchy.add(self, parent)
        self.name = name
        self.radius = radius
        self.mass = mass
        self.parent = hierarchy.getParent(self)
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
        parent = hierarchy.getParent(self) if parent is None else parent

        #--------- calculate normed postition and velocity
        norm_r = np.linalg.norm(r)
        norm_v = np.linalg.norm(v)

        #-------- fatass formula: T[seconds] = 2Pi* mu * ( (2mu/r - v^2) ^(-3/2))
        with np.errstate(invalid='ignore'):
            t = 2 * constants.pi * parent.mu * ((((2*parent.mu )/norm_r) - norm_v**2)**(-3/2))
        if np.isnan(t):
            t = 5000000

        return t

    def getState(self, t):
        try:
            state = self.orbit.sol(t)
        except Exception:
            state = np.concatenate((self.position, self.velocity)).astype(DTYPE, copy=False)
            print("getstate called without orbit calculated")
        return state



    def checkSoi(self, t, target: PhysObject | FixObject) -> float:
         """claculates distance to target Soi, >0 for outside, <0 for inside, 0 for border"""

         position = self.getState(t)[:3]
         target_postion = target.getState(t)[:3]

         distance = np.linalg.norm(position - target_postion)

         return distance - target.soi_radius

    def onParentChange(self, new_parent: PhysObject | FixObject, transition_time: float | None = None, ) -> None:
        """Move this object's state into ``new_parent``'s reference frame."""
        old_parent = hierarchy.getParent(self)
        # The stored orbit is relative to the old parent. Convert that state
        # to inertial coordinates before expressing it relative to the new one.
        relative_time = self.dt if transition_time is None else transition_time
        old_state = self.getState(relative_time)
        old_parent_state = old_parent.getState(relative_time)
        new_parent_state = new_parent.getState(relative_time)

        inertial_position = old_parent_state[:3] + old_state[:3]
        inertial_velocity = old_parent_state[3:] + old_state[3:]
        self.position = inertial_position - new_parent_state[:3]
        self.velocity = inertial_velocity - new_parent_state[3:]

        print(np.concatenate((self.position, self.velocity)))

        hierarchy.setparent(self, new_parent)
        self.parent = new_parent
        self.soi_radius = self.getSoiRadius()
        #self.orbit = self.calcintegral(parent=new_parent)
        

    def getSoiRadius(self):
        parent = hierarchy.getParent(self)

        return np.linalg.norm(self.position - parent.position) * ((self.mass/parent.mass)**(2/5)) if parent is not None else 1e67



    def calcintegral(self, r=None, v=None, parent=None, siblings: Optional[list] = None, start_time = 0):    #------>.y matrix [:3] for position , [3:] for velocity , .sol(t) for matrix at time t
        
        r = self.position if r is None else r
        v = self.velocity if v is None else v
        parent = hierarchy.getParent(self) if parent is None else parent
        self.dt = self.getOrbitalPeriod(r, v, parent)
        state0 = np.concatenate((r, v)).astype(DTYPE)


        def derivative(t, state):       #--------> function of gravity to feed into solve_ivp
            position = state[:3]
            velocity = state[3:]

            relative_r = position
            distance = np.linalg.norm(relative_r)

            acceleration = -parent.mu * relative_r / distance**3

            return np.concatenate((velocity, acceleration))

        def eventMaker(target):

            def soi_event(t, state):
                spacecraft_position = state[:3]
                target_position = target.getState(t + start_time)[:3]

                distance = np.linalg.norm(
                    spacecraft_position - target_position
                )

                return distance - target.soi_radius

            event = soi_event  # type: Any
            if target == hierarchy.getParent(self):
                 event.direction = 1
            else:
                 event.direction = -1
            event.terminal = True

            return event

        targets = hierarchy.getSiblings(self) if siblings is None else siblings
        targets.append(hierarchy.getParent(self))
        events = [eventMaker(target) for target in targets]
        print(events)
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
                #schedule.enter(self.dt, priority=0, action=self.onParentChange, argument=(event_target, event_time[0]))
                self.onParentChange(event_target)

        return solution


#dt = 2000000000
hierarchy = Hierarchy()
schedule = sched.scheduler(timefunc=timefunc, delayfunc=time.sleep)

Earth = FixObject('Earth', 6.671e6, 5.972e24 , (0,0,0), (0,0,0))

#Moon = PhysObject( 1, 10000, (100000+ Earth.radius, 0, 0), (0,10850.5,0), parent=Earth)
Moon = PhysObject('Moon', 1, 7.34767309e22, np.array([384399000, 0, 0], dtype=DTYPE), np.array([0,1018,0], dtype=DTYPE), parent=Earth)

Ship = PhysObject('Ship', 1, 2000, np.array([-36000000, 0, 0], dtype=DTYPE), np.array([1930,-4128,0], dtype=DTYPE), parent=Earth)

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
print(schedule.queue)




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

tempt = Ship.dt

Ship2 = Ship.calcintegral(start_time=Ship.dt)
tship2 = np.linspace(0, Ship.dt,1000)
statesship2 = Ship2.sol(tship2)
print(Ship2)
print(Ship.checkSoi(tempt + Ship.dt, Moon))

#Position is states[0:3]
x3 = statesship2[0]
y3 = statesship2[1]
z3 = statesship2[2]
#Velocity is states[3:6]
vx3 = statesship2[3]
vy3 = statesship2[4]
vz3 = statesship2[5]

ax.plot(x3, y3, z3, label='Ship2 trajectory', color='red')

ax.scatter(
    xs=Moon.orbit.sol(tempt)[0],
    ys=Moon.orbit.sol(tempt)[1],
    
    color='orange',
    s=100,
    label='moon',
    marker='o'
)


ax.axis('equal')
ax.set_xlabel('X [m]')
ax.set_ylabel('Y [m]')
ax.set_zlabel('Z [m]')
ax.set_title('Moon trajectory')
ax.legend()

plt.show()


