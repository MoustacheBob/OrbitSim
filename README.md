# OrbitSim
A Simple stylised orbit sim for my physics presentation


<img width="1907" height="1057" alt="Screenshot 2026-10-30 221420" src="https://github.com/user-attachments/assets/0906bf24-e05c-433e-9598-4381edd7bf49" />


## About
This Python project was made for a school project, to orbital flight more easy to visualize and for me to learn more about them aswell. The Physics solver usees a Patched Conics approach, i.e. Spheres of influence instead of n-body physics (still is suprisingly accurate), to dynamically calculate Body positions, velocities and acceleration. There are Timewarp options, a simple navigational Ui, Infos about the selected object and Buttons to burn a customizable of dV into any direction.

This projects consits of 3 Main parts:
- A frontend, using the python Ursina Engine to roughly visualize coordinates updated in the backend with neat pixel art.
- A backend, that uses mainly Scipy's integral calculation tools to give a very precise Orbital path to follow. Aslong as orbits do not Change (i.e. dont change SOI or change velocity), the orbits remain entirely static to avoid changes in orbital energy.
- A Config file, that has all the information about a celestial body, front and beckend, that can be customized to change or expand the celestial bodies present in the Sim.

### Usage
*a version of python is required*
I recommend cloning the repo, creating a virtual environment and installing the requirements from requirements.txt ( pip install -r requirements.txt ), then launching directly from main.py, but a zip file is also provided, from where the project can be launched with a .bat file (i havent had much time to test this and it is 200mb because of Ursina engine dependencies etc.)

## Changing the Config
Within the config.py file either in the cloned repo or in the OrbitSim folder when using the zip, Scroll until the Array "OBJECTS". within this Array you can create 2 types of Objects:
- a FixStruct, which will not move and always be at 0,0,0
- a Physstruct, which will be simulated

Every Szene needs One FixStruct, it needs to be declared first, it will act as the grounding pin for all other objects. Form there just 2 Things are important: 
1. All coordinates are parent relative, so if an obejct has the moon as a parent, an x coordinate of 1000 would be the moons x coordinate + 1000. Keep in mind when creating an object with a different parent than the Fixstruct.
2. Every object needs to be in the Array after its parent. For the Solar system this would mean something like Sun -> Earth -> Moon, not Sun -> Moon -> Earth.

please use the existing config, a recreation of the Artemis 2 Mission, as a reference. Notes: radius is a purely visual variable, determines Sprite size, texture paths need to be in textures foldeer and without file ending, rgb colors are in 0-1, so (100, 20, 30) would be (100/255, 20/255, 30/255).
I havent had much time to test Config changes please ask me if you have any issues.

<img width="1919" height="1052" alt="Screenshot 2026-10-30 221638" src="https://github.com/user-attachments/assets/c0ee0cc9-b048-4aa9-9eea-8fbb99148af4" />

credit for the Pixelart:
- https://opengameart.org/content/space-pixel-art by peony
- https://opengameart.org/content/space-background-1 by WestBeam


