from dataclasses import dataclass
import numpy as np
from ursina import rgb,color

DTYPE = np.float64

EARTH_RADIUS = 6.371e6
EARTH_ENTRY_ALTITUDE = 120e3


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
        gravity_sources: tuple[str, ...] = ()
        stop_radius: float | None = None

OBJECTS = [
        FixStruct(
            name ="Earth",
            radius = EARTH_RADIUS,
            mass = 5.972e24,
            texture = 'Earth'
        ),

        PhysStruct(
            name ='Moon',
            radius = 1.738e6,
            mass = 7.34767309e22,
            parent = 'Earth',
            # Lunar orbit snapshot rotated to align the representative free-return flyby.
            position=(230.015230e6, -308.027749e6, 0),
            velocity=(815.9468, 609.3686, 0),
            texture = 'FullMoon',
            orbit_color = rgb(1,0,0)
        ),

        # PhysStruct(
        #     name ='Ship',
        #     radius = 1e6,
        #     mass = 10000,
        #     parent = 'Earth',
        #     position = (-36000000, 0, 0),
        #     velocity = (0,-5000, 0),
        #     texture = 'RocketWhite',
        #     orbit_color = rgb(0,0,1)
        # ),

        PhysStruct(
            name ='Ship',
            radius = 1e6,
            mass = 10000,
            parent = 'Earth',
            position=(-(EARTH_RADIUS + 200e3), 0, 0),
            velocity=(425, -10921.4864, 0),
            texture = 'RocketWhite',
            orbit_color = rgb(0,0,1),
            gravity_sources=('Moon',),
            stop_radius=EARTH_RADIUS + EARTH_ENTRY_ALTITUDE,
        ),

]
        
    #  --------------------------------------Backup Innits
    # 
    # PhysStruct(
    #                name ='Ship',
    #                radius = 1e6,
    #                mass = 10000,
    #                parent = 'Earth',
    #                position=(-(EARTH_RADIUS + 200e3), 0, 0),
    #                velocity=(425, -10921.4864, 0),
    #                texture = 'RocketWhite',
    #                orbit_color = rgb(0,0,1),
    #                gravity_sources=('Moon',),
    #                stop_radius=EARTH_RADIUS + EARTH_ENTRY_ALTITUDE,
    #            ),
        
    #     PhysStruct(
    #                 name ='Moon',
    #                 radius = 1.738e6,
    #                 mass = 7.34767309e22,
    #                 parent = 'Earth',
    #                 # Lunar orbit snapshot rotated to align the representative free-return flyby.
    #                 position=(230.015230e6, -308.027749e6, 0),
    #                 velocity=(815.9468, 609.3686, 0),
    #                 texture = 'FullMoon',
    #                 orbit_color = rgb(1,0,0)
    #             ),