import numpy as np
from typing import Any, Optional
import scipy as sp
from scipy import constants
from scipy.integrate import solve_ivp
import time
import matplotlib.pyplot as plt
import sched
from config import OBJECTS, FixStruct, PhysStruct

DTYPE = np.float64

simulation_start: float = time.monotonic()
timewarp: float = 10000
clock_last_update: float = simulation_start
clock_elapsed: float = 0.0


def timefunc() -> float:
    global clock_last_update, clock_elapsed
    now = time.monotonic()
    clock_elapsed += (now - clock_last_update) * timewarp
    clock_last_update = now
    return clock_elapsed


def set_timewarp(new_timewarp: float) -> None:
    global timewarp
    timefunc()
    timewarp = new_timewarp


def delayfunc(delay: float) -> None:
    time.sleep(float(delay) / timewarp)



class Hierarchy:
    def __init__(self) -> None:
        self.hierarchy = {}

    def __repr__(self):
         return str(self.hierarchy)

    def add(self, target: PhysObject | FixObject, parent: PhysObject | FixObject | None = None,):
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

    def __init__(self, name, radius, mass):
        hierarchy.add(self, None)
        self.name = name
        self.radius = radius
        self.mass = mass
        self.position = np.zeros(3, dtype=float)
        self.velocity = np.zeros(3, dtype=float)

        self.mu = constants.G * self.mass
        self.soi_radius = 1e67
        self.parent = None
        
        

    def __repr__(self) -> str:
            return self.name 


    def getState(self, t, orbital_period = None, orbit = None):
        return np.concatenate((self.position, self.velocity)).astype(DTYPE, copy=False)


    

class PhysObject:
    def __init__(self, name, radius, mass, position, velocity, parent):

        hierarchy.add(self, parent)
        self.name = name
        self.radius = radius
        self.mass = mass
        self.parent = hierarchy.getParent(self)
        self.postion0 = np.asarray(position, dtype=DTYPE)
        self.velocity0 = np.asarray(velocity, dtype=DTYPE)
        self.acceleration = np.array([ 0, 0, 0], dtype=DTYPE)
        
        self.mu = constants.G * self.mass
        self.orbit_end_time = timefunc() + self.getOrbitalPeriod()
        self.soi_radius = self.getSoiRadius()
        self.orbit: Any
        self.calcintegral()

        

    def __repr__(self) -> str:
        return self.name  

    
    def getOrbitalPeriod(self, r = None, v = None, parent = None):  # -----> float Orbital Period in seconds
        """calculates orbital period of object at current position and velocity, raises exception as orbital period gety virtually infinite"""

        r = self.postion0 if r is None else r
        v = self.velocity0 if v is None else v
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

    def getState(self, t): #-----> np.array[x,y,z, vx,vy,vz] 
        try:
            state = self.orbit.sol(t)
        except Exception:
            state = np.concatenate((self.postion0, self.velocity0)).astype(DTYPE, copy=False)
            print("getstate called without orbit calculated")
        return state



    def checkSoi(self, t, target: PhysObject | FixObject) -> float:
         """claculates distance to target Soi, >0 for outside, <0 for inside, 0 for border"""

         position = self.getState(t)[:3]
         target_postion = target.getState(t)[:3]

         distance = np.linalg.norm(position - target_postion)

         return distance - target.soi_radius

    def onParentChange(self, new_parent: PhysObject | FixObject, transition_time: float) -> None:
        """Move this object's state into ``new_parent``'s reference frame."""
        old_parent = hierarchy.getParent(self)
        old_state = self.getState(transition_time)
        old_parent_state = old_parent.getState(transition_time)
        new_parent_state = new_parent.getState(transition_time)

        inertial_position = old_parent_state[:3] + old_state[:3]
        inertial_velocity = old_parent_state[3:] + old_state[3:]
        self.postion0 = inertial_position - new_parent_state[:3]
        self.velocity0 = inertial_velocity - new_parent_state[3:]

        print(np.concatenate((self.postion0, self.velocity0)))

        hierarchy.setparent(self, new_parent)
        self.parent = new_parent
        self.soi_radius = self.getSoiRadius()
        #self.orbit = self.calcintegral(parent=new_parent)
        

    def getSoiRadius(self):
        parent = hierarchy.getParent(self)

        return np.linalg.norm(self.postion0) * ((self.mass/parent.mass)**(2/5)) if parent is not None else 1e67



    def calcintegral(self, r=None, v=None, parent=None, siblings: Optional[list] = None, start_time = None):    #------>.y matrix [:3] for position , [3:] for velocity , .sol(t) for matrix at time t
        
        start_time = timefunc() if start_time is None else start_time
        r = self.postion0 if r is None else r
        v = self.velocity0 if v is None else v
        parent = hierarchy.getParent(self) if parent is None else parent
        self.orbit_end_time = self.getOrbitalPeriod(r, v, parent) + timefunc()
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
                target_position = (
                    np.zeros(3, dtype=DTYPE)
                    if target is hierarchy.getParent(self)
                    else target.getState(t)[:3]
                )

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
        #print(events)
        solution = solve_ivp(
            derivative,
            (start_time, start_time + self.orbit_end_time),
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
                self.orbit_end_time = float(event_time[0])

                new_parent = event_target if event_target is not hierarchy.getParent(self) else hierarchy.getParent(event_target)

                schedule.enterabs(self.orbit_end_time, priority=0, action=self.onParentChange, argument=(new_parent, self.orbit_end_time))
                
        schedule.enterabs(self.orbit_end_time, priority=1000, action=self.calcintegral, kwargs={'start_time' : self.orbit_end_time})
        print('ran integration of :', self, ', t: ', start_time)

        self.orbit = solution
        return solution


def phys_object_maker():
        physobjects = {}

        for object in OBJECTS:
            if isinstance(object, FixStruct):
                physobjects[object.name] = FixObject(
                    name=object.name,
                    radius=object.radius,
                    mass=object.mass
                    )

            elif isinstance(object, PhysStruct):

                parent = None
                if object.parent is not None:           #-----> needed to ensure objects receive their actual parent object,
                    parent = physobjects[object.parent] #-----> Config needs parents to be before actual object (no sun -> Moon -> Earth)

                physobjects[object.name] = PhysObject(
                    name=object.name,
                    radius=object.radius,
                    mass=object.mass,
                    position=object.position,
                    velocity=object.velocity,
                    parent=parent
                )

        return physobjects

#dt = 2000000000
hierarchy = Hierarchy()
schedule = sched.scheduler(timefunc=timefunc, delayfunc=delayfunc)

physobjects = phys_object_maker()

Earth = physobjects['Earth']
Moon = physobjects['Moon']
Ship = physobjects['Ship']

# #Moon = PhysObject( 1, 10000, (100000+ Earth.radius, 0, 0), (0,10850.5,0), parent=Earth)
# Moon = PhysObject('Moon', 1, 7.34767309e22, np.array([384399000, 0, 0], dtype=DTYPE), np.array([0,1018,0], dtype=DTYPE), parent=Earth)

# Ship = PhysObject('Ship', 1, 2000, np.array([36000000, 0, 0], dtype=DTYPE), np.array([0,4500,0], dtype=DTYPE), parent=Earth)

start_time = timefunc()

solutionMoon =  Moon.orbit
solutionShip =  Ship.orbit
print(hierarchy)
print(hierarchy.getSiblings(Ship))

# --------- debug printing
print(solutionShip)
print("Final position:", solutionShip.y[:3 , -1])
print("Final velocity:", solutionShip.y[3: ,-1])
print("Orbital Period:", Ship.orbit_end_time)
position_difference = Moon.postion0 - solutionMoon.y[:3, -1]
print("position difference:", position_difference)

print(timefunc() - start_time)
print(schedule.queue)




#   ---------- matplotlib visualization---------------------------------
t = np.linspace(start_time, Moon.orbit_end_time + start_time, 10000)
tship = np.linspace(start_time, Ship.orbit_end_time + start_time,1000)
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

# tempt = Ship.orbit_end_time
# Ship.onParentChange(new_parent=Moon, transition_time=Ship.orbit_end_time)
# Ship2 = Ship.calcintegral(start_time=Ship.orbit_end_time)
# tship2 = np.linspace(tempt, Ship.orbit_end_time,1000)
# statesship2 = Ship2.sol(tship2)


# #Position is states[0:3]
# x3 = statesship2[0]
# y3 = statesship2[1]
# z3 = statesship2[2]
# # #Velocity is states[3:6]
# vx3 = statesship2[3]
# vy3 = statesship2[4]
# vz3 = statesship2[5]

# ax.plot(x3, y3, z3, label='Ship2 trajectory', color='red')

# ax.scatter(
#     xs=Moon.orbit.sol(tempt)[0],
#     ys=Moon.orbit.sol(tempt)[1],
    
#     color='orange',
#     s=100,
#     label='moon',
#     marker='o'
# )


ax.axis('equal')
ax.set_xlabel('X [m]')
ax.set_ylabel('Y [m]')
ax.set_zlabel('Z [m]')
ax.set_title('Moon trajectory')
ax.legend()

#plt.show()



