from ursina import *
from config import *
from physics import *
from pathlib import Path
from ursina import application
import numpy as np

application.asset_folder = Path(__file__).resolve().parent

#Definitions:   Distances (radius, apoapsis, periapsis) in 1000km
#               Mass in metric Tons           

Text.default_font = 'textures/fonts/pixel_font.ttf'

app = Ursina()

class Visobject(Sprite):
    def __init__(self, radius: float = 1, texture :str = None, orbit_color: str = rgb(1, 1, 1), custom_parent: Entity = None, **kwargs):
        super().__init__(texture, collider = 'box', **kwargs)
        self.double_sided_setter(True)
        self.world_scale = radius * 2 / 1_000_000 / self.model_bounds.size.x  
        self.texture_scale = Vec2(-1, 1)
        self.on_click = Func(self.select)
        self.on_double_click = Func(self.on_double_select)
        self.orbit_color = orbit_color
    
        
        self.phys_object: PhysObject | FixObject = physobjects[self.name]
        self.phys_object.vis_object = self
        self.custom_parent = custom_parent
        self.update_position(0)

        #---------soi construction-----
        self.Soi = None
        if self.phys_object.parent is not None:
            self.Soi = Sprite(texture='Soi2', parent=self)
            self.Soi.scale = self.phys_object.soi_radius / radius

        #---------infot text construction-----
        self.info_text = Text(text=f'{self.name}\n{self.phys_object.mass:.2e} kg\n{self.position} m', parent=self, position = (0, -self.model_bounds.size.y/2 -3/self.world_scale.y, 0), origin=(0, 0))
        self.info_text.world_scale = Vec3(-50, 50, 50)
        self.info_text.visible = False
        self.selected_sprite = Sprite(texture='selected', parent = self, world_scale= 7)
        self.selected_sprite.visible = False

        self.draw_conic(self.sample_points())

    def update_position(self, now = None):  
         now = timefunc() if now is None else now
         position = self.phys_object.getState(now)[:3].copy()
         parent = self.custom_parent
         while parent is not None:
            position += parent.phys_object.getState(now)[:3]

            if hasattr(self, 'Conic'):
                self.Conic.position += parent.position

            parent = parent.custom_parent

             
         self.position = Vec3(position[0] / 1000000, position[2] /1000000, position[1]/1000000)

         

    def draw_conic(self, points: list[Vec3], color: str | None = None, thickness: int = 2):
        if not hasattr(self.phys_object, 'orbit'):
            return

        previous_conic = getattr(self, 'Conic', None)
        if previous_conic is not None:
            destroy(previous_conic, force_destroy=True)

        color = self.orbit_color if color is None else color

        self.Conic = Entity(model=Mesh(vertices=points, mode='line', thickness=thickness), color=color, alpha=0.25)


    def sample_points(self, sample_mult = 2000, orbit = None):

        orbit = self.phys_object.orbit if orbit is None and hasattr(self.phys_object, 'orbit') else orbit

        if orbit is None:
            return Vec3(0,0,0)
        else:
            points = []
            times = np.linspace(orbit.t[0], orbit.t[-1], sample_mult, endpoint=False)
            for time in times:
                point_position = orbit.sol(time)[:3]
                points.append((point_position[0] / 1000000, point_position[2] / 1000000, point_position[1] / 1000000))

            # point_position = orbit.sol(orbit.t[0])[:3]
            # points.append((point_position[0] / 1000000, point_position[2] / 1000000, point_position[1] / 1000000))

            return points
            

    def select(self):
        for object in visobjects:
            visobjects[object].selected_sprite.visible = False
            visobjects[object].info_text.visible = False
        self.selected_sprite.visible = not self.selected_sprite.visible
        self.info_text.visible = not self.info_text.visible

    def on_double_select(self):
        editor_cam.position = self.position
        

    def update(self):
        self.world_quaternion = Quat(0,0, 1, 0) * camera.world_quaternion 


def vis_object_maker():
        visobjects = {}

        for object in OBJECTS:

            parent = None
            if object.parent is not None:           #-----> needed to ensure objects receive their actual parent object,
                parent = visobjects[object.parent] #-----> Config needs parents to be before actual object (no sun -> Moon -> Earth)

            visobjects[object.name] = Visobject(
                name=object.name,
                radius=object.radius,
                orbit_color=object.orbit_color if hasattr(object, 'orbit_color') else None,
                texture=object.texture,
                custom_parent=parent
            )

        return visobjects

visobjects = vis_object_maker()

def sky_click():
    for object in visobjects:
        visobjects[object].selected_sprite.visible = False
        visobjects[object].info_text.visible = False


#-------Sky----------

sky_tex = load_texture('starBG')

star_sky = Sky(texture=sky_tex, collider = 'box')

star_sky.texture_scale = Vec2(5,2)

star_sky.on_click = Func(sky_click)


editor_cam = EditorCamera()
editor_cam.world_position = Vec3(0,0,-100)

def update():
    now = timefunc()
    for object in visobjects:
         visobjects[object].update_position(now)

    schedule.run(blocking=False)

visobjects['Moon'].sample_points()
app.run()