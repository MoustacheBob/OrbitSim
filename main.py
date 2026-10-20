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
selected: Visobject| None = None

app = Ursina()

class Visobject(Sprite):
    def __init__(self, radius: float = 1, texture :str = None, orbit_color: Color | None = None, custom_parent: Entity = None, **kwargs):
        super().__init__(texture, collider = 'box', **kwargs)
        self.double_sided_setter(True)
        self.world_scale = radius * 2 / 1_000_000 / self.model_bounds.size.x  
        self.texture_scale = Vec2(-1, 1)
        self.on_click = Func(self.select)
        self.on_double_click = Func(self.on_double_select)
        self.orbit_color = rgb(1, 1, 1) if orbit_color is None else orbit_color
    
        
        self.phys_object: PhysObject | FixObject = physobjects[self.name]
        self.phys_object.vis_object = self
        self.custom_parent = custom_parent
        self.update_position(0)

        #---------soi construction-----
        self.Soi = None
        if self.phys_object.parent is not None:
            self.Soi = Sprite(texture='Soi2', parent=self)
            self.Soi.scale = self.phys_object.soi_radius / radius

        # -------create info text once
        self.info_text = Text(
            text='',
            parent=camera.ui,
            position=Vec2(0,0),
            scale=1,
            #window.bottom_left.x, window.bottom_left.y + 20)
        )
        self.info_text.origin = Vec2(-.5,-.5)
        self.info_text.position = window.bottom_left + Vec2(0.01,0.01)
        self.info_text.visible = False

        # ----- selcected sprite
        self.selected_sprite = Sprite(texture='selected', parent = self, world_scale= 7, collider='box')
        self.selected_sprite.visible = False
        self.selected_sprite.on_double_click = Func(self.on_double_select)
        self.selected_sprite.on_click = Func(self.select)
       

        self.draw_conic(self.sample_points())

#------------------ object info---------------------------
    def update_info_text(self, now: float):
        phys = self.phys_object
        state = phys.getState(now)
        x, y, z = state[:3]
        velocity = np.linalg.norm(state[3:])

        self.info_text.text = (
            f'Name: {phys.name}\n'
            f'Mass: {phys.mass:.2e} kg\n'
            f'Radius: {phys.radius:g} x 10^3 km\n'
            # f'Position (m):'
            # f' X: {x:.2e},'
            # f' Y: {y:.2e},'
            # f' Z: {z:.2e}\n'
            f'Altitude: {round(np.linalg.norm((x,y,z))/1000, 2)}km\n'
            f'Velocity magnitude: {velocity:.2e} m/s\n'
            f'Orbital period: {phys.getOrbitalPeriod():.3e} s'
    )



        
    def update_position(self, now = None):  
        '''calculates gloabl postion by adding all parents relative position, if has a conic also sets its position to visobjects customparents position'''

        now = timefunc() if now is None else now
        position = self.phys_object.getState(now)[:3].copy()
        parent = self.custom_parent
        while parent is not None:
            position += parent.phys_object.getState(now)[:3]
            parent = parent.custom_parent

        if hasattr(self, 'Conic') and self.custom_parent is not None:
            self.Conic.position = self.custom_parent.position

             
        self.position = Vec3(position[0] / 1000000, position[2] /1000000, position[1]/1000000)

         

    def draw_conic(self, points: list[Vec3], color: Color | None = None, thickness: int = 2):
        '''creates or changes the conic, always call with samplepoints() as points.'''

        if not hasattr(self.phys_object, 'orbit'):
            return

        color = self.orbit_color if color is None else color
        model = Mesh(vertices=points, mode='line', thickness=thickness)
        if getattr(self, 'Conic', None) is None:
            self.Conic = Entity(model=model, color=color, alpha=0.25)
        else:
            self.Conic.model = model
            self.Conic.color = color
            self.Conic.alpha = 0.25


#------------------------ Creates array of points, used to set mesh for Conic
    def sample_points(self, sample_mult = 2000, orbit = None):
        '''Creates array of points from self.physobject.orbit or parameter, used to set mesh for Conic'''

        orbit = self.phys_object.orbit if orbit is None and hasattr(self.phys_object, 'orbit') else orbit

        if orbit is None:
            return Vec3(0,0,0)
        else:
            points = []
            times = np.linspace(orbit.t[0], orbit.t[-1], sample_mult)
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
        self.selected_sprite.visible = True
        self.info_text.visible = True
        global selected 
        selected = self

    def on_double_select(self):
        editor_cam.position = self.position
        selected = self
        

    def update(self):
        self.world_quaternion = Quat(0,0, 1, 0) * camera.world_quaternion 







class Ui():
    def __init__(self,ui_scale = 0.075,padding = 0.01) -> None:
        self.ui_scale = ui_scale
        self.padding = padding * ui_scale
        self.padding = padding
        
#-------------------Clock-------------------------------------
        self.clock = Text(
            text='0d : 00h : 00m : 00s',
            parent=camera.ui,
            position=(0, window.top[1] - padding),
            origin=(0, 0.5),
            scale=1,
        )

#--------------------timewarp buttons--------------------
        self.timewarp_buttons = {0 :'||', 1 : '1', 10 : '10', 1000 : '1000', 10000 : '10K', 100000 : '100K', 1000000 : '1M'}
        self.buttons = {}
        offset = 0
        for button in self.timewarp_buttons:
            cur_button = Button(text= self.timewarp_buttons[button], parent=camera.ui, model=Default, scale=ui_scale, position=window.top_left + Vec2(offset + padding, 0 - padding), origin=(-0.5, 0.5), color=rgb(50/255, 50/255, 50/255))
            cur_button.on_click = Func(set_timewarp, button)

            self.buttons[cur_button.text] = cur_button
            offset += 1 * ui_scale + padding

#------------------- List Visobjects---------------------
        offset=0
        for button in visobjects:
            cur_button = Button(text=button, icon=visobjects[button].texture, parent=camera.ui, model=Default, scale=Vec2(2.5,0.25)* ui_scale, position=window.top_right + Vec2(0 - padding, offset - padding), origin=((0.5+padding), 0.5+padding), color=rgb(50/255, 50/255, 50/255))
            cur_button.text_size = cur_button.text_size * .5
            cur_button.icon.scale = Vec2(.025, .25)
            cur_button.icon.position = Vec2(-5, 0) * ui_scale
            cur_button.on_click = Func(visobjects[button].select)
            cur_button.on_double_click= Func(visobjects[button].on_double_select)

            self.buttons[cur_button.text] = cur_button
            offset -= cur_button.scale_x_getter() * ui_scale + padding

#------------------- Burn buttons -----------------------
        
        

        prograde = Text('Prograde', color=color.green, position=window.bottom_right + Vec2( -0.2, 0.2))
        radial = Text('Radial-out', color=color.blue, position=window.bottom_right + Vec2( -0.2, 0.15))
        normal = Text('Normal', color=rgb(158/255, 0, 237/255), position=window.bottom_right + Vec2( -0.2, 0.1))
        self.burntext = [prograde, radial, normal]

        self.burninput =  ThinSlider(min=1,max=500,default=100,text='m/s burn',step=1, position=window.bottom + Vec2(0,0.08))
        self.burnbuttons = []
        for text in self.burntext:
            p_button = Button(text='+',text_color=color.black, color=text.color, position=text.position + Vec2(0.155,-0.01), scale=ui_scale/2.5)
            m_button = Button(text='-',text_color=color.black, color=text.color, position=text.position + Vec2(-0.025,-0.01), scale=ui_scale/2.5)

            p_button.on_click = Func(self.on_dvbutton_click, text.text, 1)
            m_button.on_click = Func(self.on_dvbutton_click, text.text,-1)


    
    def on_dvbutton_click(self, direction, directionmult = 1):
        if selected is not None:
            selected.phys_object.burnDv(direction, dv= directionmult * self.burninput.value)                




    def on_twbutton_click(self, timewarp):
        set_timewarp(timewarp)

    def update(self, now: float) -> None:
        total_seconds = max(0, int(now))
        days, remainder = divmod(total_seconds, 24 * 60 * 60)
        hours, remainder = divmod(remainder, 60 * 60)
        minutes, seconds = divmod(remainder, 60)
        self.clock.text = f'{days}d : {hours:02}h : {minutes:02}m : {seconds:02}s'


def vis_object_maker():
        '''unpacks OBJECTS from config into visual obects'''
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




#-------Sky----------
def sky_click():
    for object in visobjects:
        visobjects[object].selected_sprite.visible = False
        visobjects[object].info_text.visible = False

sky_tex = load_texture('starBG')

star_sky = Sky(texture=sky_tex, collider = 'box')

star_sky.texture_scale = Vec2(5,2)

star_sky.on_click = Func(sky_click)


editor_cam = EditorCamera()
editor_cam.world_position = Vec3(0,0,-100)
window.entity_counter.disable()
window.exit_button.disable()
window.collider_counter.disable()

def update():
    now = timefunc()
    UI.update(now)
    for object in visobjects:
         visobjects[object].update_position(now)
         visobjects[object].update_info_text(now)

    schedule.run(blocking=False)

UI = Ui()
app.run()