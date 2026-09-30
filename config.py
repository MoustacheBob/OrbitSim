from dataclasses import dataclass
import numpy as np

DTYPE = np.float64


@dataclass          
class FixStruct():
    
        name : str
        radius :float 
        mass : float 
        texture : str
        parent : str = None

@dataclass          
class PhysStruct():
    
        name : str
        radius :float 
        mass : float
        parent : str 
        position : tuple
        velocity : tuple
        texture : str
        orbit_color : str

OBJECTS = [
        FixStruct(
            name ="Earth",
            radius = 6.671e6,
            mass = 5.972e24,
            texture = 'Earth'
        ),

        PhysStruct(
            name ='Moon',
            radius = 1.738e6,
            mass = 7.34767309e22,
            parent = 'Earth',
            position = (384399000, 0, 0),
            velocity = (0,1018,0),
            texture = 'FullMoon',
            orbit_color = 'blue'
        ),

        PhysStruct(
            name ='Ship',
            radius = 1e6,
            mass = 10000,
            parent = 'Earth',
            position = (-36000000, 0, 0),
            velocity = (1800, 4200, 0),
            texture = 'RocketWhite',
            orbit_color = 'white'
        )

]
        
        
