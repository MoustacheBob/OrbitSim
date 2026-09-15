import numpy as np
import scipy as sp
from scipy import constants
import time

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
        self.curforce = np.array([ 0, 0, 0], dtype=DTYPE)

    def update(self, dt):
        self.force(self.curforce)
        self.accel(self.acceleration, dt)
        self.move(self.velocity, dt)

    
    def move(self, velocity, dt):
        self.position += velocity * dt

    def accel(self, acceleration, dt):
        self.velocity += acceleration * dt

    def force(self, force):
        self.acceleration = force / self.mass



Earth = PhysObject('Earth', 1, 10 , np.array([0,0,0]), np.array([0,0,0]))
Earth.curforce = np.array([2, 1, 0.5])

def simulate(dt, steps):
    for i in range(0,steps):
        Earth.update(dt)
        print('acceleration: ', Earth.acceleration, 
              '\nvelocity: ', Earth.velocity,
              '\nposition: ', Earth.position, '\n')
        time.sleep(dt)


simulate(1, 1000)





