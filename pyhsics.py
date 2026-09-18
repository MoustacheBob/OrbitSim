import numpy as np
import scipy as sp
from scipy import constants
from scipy.integrate import solve_ivp
import time
import matplotlib.pyplot as plt


DTYPE = np.float64

class FixObject:
    def __init__(self, radius, mass, position: np.array(), velocity: np.array()):

        self.radius = radius
        self.mass = mass
        self.position = np.asarray(position, dtype=float)
        self.velocity = np.asarray(velocity, dtype=float)

        self.mu = constants.G * self.mass
        self.soi_radius = 1e67

    def update(self, dt):
        self.move(self.velocity, dt)

    
    def move(self, velocity, dt):
        self.position += velocity * dt

    def getstate(self, t, orbital_period = None, orbit = None):
            
                    return self.position
            

    

    

class PhysObject:
    def __init__(self, radius, mass, position, velocity, parent = None):

        self.radius = radius
        self.mass = mass
        self.parent = parent
        self.position = np.asarray(position, dtype=DTYPE)
        self.velocity = np.asarray(velocity, dtype=DTYPE)
        self.acceleration = np.array([ 0, 0, 0], dtype=DTYPE)
        
        self.mu = constants.G * self.mass
        self.dt = self.getOrbitalPeriod()
        self.soi_radius = np.linalg.norm(self.position - parent.position) * ((self.mass/parent.mass)**(2/5)) if parent is not None else 1e67
        self.orbit = self.calcintegral()

        

    
    def getOrbitalPeriod(self, r = None, v = None, parent = None):  # -----> float Orbital Period in seconds
        r = self.position if r is None else r
        v = self.velocity if v is None else v
        parent = self.parent if parent is None else parent

        #--------- calculate normed postition and velocity
        norm_r = np.linalg.norm(r)
        norm_v = np.linalg.norm(v)

        #-------- fatass formula: T[seconds] = 2Pi* mu * ( (2mu/r - v^2) ^(-3/2))

        t = 2 * constants.pi * parent.mu * ((((2*parent.mu )/norm_r) - norm_v**2)**(-3/2))

        return t

    def getState(self, t, orbital_period = None, orbit = None): 
        orbital_period = self.dt if orbital_period is None else orbital_period
        orbit = self.dt if orbit is None else orbit

        return orbit.sol(t % orbital_period)

    def soiCheckFunction(self, t, target):
        """check distance to target soi: >0 for outside, <0 for inside, used in minimize function"""
        spacecraft_pos = self.getState(t)[:3]
        target_pos = target.getState(t)[:3]

        return np.linalg.norm(spacecraft_pos -- target_pos) - target.soi_radius



    def calcintegral(self, r=None, v=None, parent=None):    #------>.y matrix [:3] for position , [3:] for velocity , .sol(t) for matrix at time t
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

        solution = solve_ivp(
            derivative,
            (0, self.dt),
            state0,
            method='DOP853',
            dense_output=True,
            atol = 1e-6,
            rtol = 1e-6
        )

        return solution


#dt = 2000000000

Earth = FixObject(6.671e6, 5.972e24 , (0,0,0), (0,0,0))

#Moon = PhysObject( 1, 10000, (100000+ Earth.radius, 0, 0), (0,10850.5,0), parent=Earth)
Moon = PhysObject(1, 7.34767309e22, np.array([384399000, 0, 0], dtype=DTYPE), np.array([0,1018,0], dtype=DTYPE), parent=Earth)

#Ship = PhysObject(1, 2000, np.array([300000000, 0, 0], dtype=DTYPE), np.array([0, 1000, 0], dtype=DTYPE), Earth)

start_time = time.time()

solutionMoon =  Moon.calcintegral()


#solutionShip =  Ship.calcintegral()

print("Final position:", solutionMoon.y[:3 , -1])
print("Final velocity:", solutionMoon.y[3: ,-1])
print("Orbital Period:", Moon.getOrbitalPeriod())
position_difference = Moon.position - solutionMoon.y[:3, -1]
print("position difference:", position_difference)

print(time.time()-start_time)
print(Moon.soi_radius)


#   - matplotlib visualization
t = np.linspace(0, Moon.dt, 10000)
states = solutionMoon.sol(t)

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
ax.axis('equal')
ax.set_xlabel('X [m]')
ax.set_ylabel('Y [m]')
ax.set_zlabel('Z [m]')
ax.set_title('Moon trajectory')
ax.legend()

plt.show()


