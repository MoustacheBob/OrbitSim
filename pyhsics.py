import numpy as np
import scipy as sp
from scipy import constants
from scipy.integrate import solve_ivp
import time

start_time = time.time()
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
        pass

    
    def move(self, velocity, dt):
        self.position += velocity * dt

    

    

class PhysObject:
    def __init__(self, Name, radius, mass, position: np.array(), velocity: np.array(), parent = None):

        self.name = Name
        self.radius = radius
        self.mass = mass
        self.parent = parent
        self.position = np.asarray(position, dtype=DTYPE)
        self.velocity = np.asarray(velocity, dtype=DTYPE)
        self.acceleration = np.array([ 0, 0, 0], dtype=DTYPE)
        
        self.mu = constants.G * self.mass


    def update(self):
        pass
    
    def calcintegral(self, r, v, parent):
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
            (0, 10000),
            state0,
            method='DOP853',
            rtol=1e-10,
            atol=1e-10
        )

        return solution

Earth = FixObject('Earth', 1, 5.972e24 , np.array([0,0,0]), np.array([0,0,0]))

Moon = PhysObject('Moon', 1, 7.34767309e22, np.array([384399000, 0, 0], dtype=DTYPE), np.array([0,0,0], dtype=DTYPE))


solution =  Moon.calcintegral(Moon.position, Moon.velocity, Earth)

print("Final position:", solution.y[:3, -1])
print("Final velocity:", solution.y[3:, -1])

print(time.time()-start_time)





