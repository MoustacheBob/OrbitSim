import numpy as np
import scipy as sp
from scipy import constants
from scipy.integrate import solve_ivp
import time
import matplotlib.pyplot as plt


DTYPE = np.float64

class FixObject:
    def __init__(self, Name, radius, mass, position: np.array(), velocity: np.array()):

        self.name = Name
        self.radius = radius
        self.mass = mass
        self.position = np.asarray(position, dtype=float)
        self.velocity = np.asarray(velocity, dtype=float)
        self.mu = constants.G * self.mass

    def update(self, dt):
        self.move(self.velocity, dt)

    
    def move(self, velocity, dt):
        self.position += velocity * dt

    

    

class PhysObject:
    def __init__(self, Name, radius, mass, position, velocity, parent = None):

        self.name = Name
        self.radius = radius
        self.mass = mass
        self.parent = parent
        self.position = np.asarray(position, dtype=DTYPE)
        self.velocity = np.asarray(velocity, dtype=DTYPE)
        self.acceleration = np.array([ 0, 0, 0], dtype=DTYPE)
        
        self.mu = constants.G * self.mass
        self.dt = self.getOrbitalPeriod()


    def update(self):
        pass
    
    def getOrbitalPeriod(self, r = None, v = None, parent = None):
        r = self.position if r is None else r
        v = self.velocity if v is None else v
        parent = self.parent if parent is None else parent

        #--------- calculate normed postition and velocity
        norm_r = np.linalg.norm(r)
        norm_v = np.linalg.norm(v)

        #-------- fatass formula: T[seconds] = 2Pi* mu * ( (2mu/r - v^2) ^(-3/2))

        t = 2 * constants.pi * parent.mu * ((((2*parent.mu )/norm_r) - norm_v**2)**(-3/2))

        return t

    def calcintegral(self, r=None, v=None, parent=None):
        r = self.position if r is None else r
        v = self.velocity if v is None else v
        parent = self.parent if parent is None else parent
        state0 = np.concatenate((r, v)).astype(DTYPE)


        def derivative(t, state):
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

Earth = FixObject('Earth', 6.671e6, 5.972e24 , np.array([0,0,0]), np.array([0,0,0]))

#Moon = PhysObject('Moon', 1, 10000, (300000+ Earth.radius, 0, 0), (0,5730,0), parent=Earth)
Moon = PhysObject('Moon', 1, 7.34767309e22, np.array([384399000, 0, 0], dtype=DTYPE), np.array([0,1018,0], dtype=DTYPE), parent=Earth)

#Ship = PhysObject('Ship', 1, 2000, np.array([300000000, 0, 0], dtype=DTYPE), np.array([0, 1000, 0], dtype=DTYPE), Earth)

start_time = time.time()

solutionMoon =  Moon.calcintegral()
#solutionShip =  Ship.calcintegral()

print("Final position:", solutionMoon.y[:3 , -1])
print("Final velocity:", solutionMoon.y[3: ,-1])
print("Orbital Period:", Moon.getOrbitalPeriod())
position_difference = Moon.position - solutionMoon.y[:3, -1]
print("position difference:", position_difference)

print(time.time()-start_time)


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

ax.plot(x, y, z, label='Moon trajectory')
ax.scatter(
    Earth.position[0],
    Earth.position[1],
    Earth.position[2],
    color='blue',
    s=100,
    label='Earth'
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


