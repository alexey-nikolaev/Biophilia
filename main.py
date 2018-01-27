#import kivy
#kivy.require('1.10.0')

from question_composer import generate_question

from os.path import join
import locale
import math
import random
import copy
from functools import partial
import weakref

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.stencilview import StencilView
from kivy.uix.widget import Widget
from kivy.uix.slider import Slider
from kivy.graphics import Color, Line, Rectangle
from kivy.uix.image import AsyncImage
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.core.image import Image as CoreImage
from kivy.metrics import pt, dp, sp
from kivy.graphics import BorderImage
from kivy.uix.screenmanager import ScreenManager, Screen, RiseInTransition
from kivy.base import EventLoop, stopTouchApp
from kivy.graphics.texture import Texture
from kivy.uix.behaviors import ToggleButtonBehavior

from navigationdrawer import NavigationDrawer

from kivy.core.text import LabelBase  
LabelBase.register(name="FrutigerBold",  
                   fn_regular="fonts/FrutigerNeueLTW1G-Bold.otf")
LabelBase.register(name="FrutigerBoldItalic",  
                   fn_regular="fonts/FrutigerNeueLTW1G-BoldIt.otf")

from kivy.core.audio import SoundLoader
global sounds
sounds = {}
sounds['correct'] = SoundLoader.load(join('sounds','correct.ogg'))
sounds['incorrect'] = SoundLoader.load(join('sounds', 'incorrect.ogg'))
sounds['click'] = SoundLoader.load(join('sounds', 'click.ogg'))
sounds['forest'] = SoundLoader.load(join('sounds', 'forest.ogg'))
sounds['flip'] = SoundLoader.load(join('sounds', 'flip.ogg'))
sounds['forest'].loop = True

from kivy.core.window import Window
#Window.clearcolor = (32/255., 32/255., 34/255., 1)
Window.clearcolor = (154/255., 10/255., 53/255., 1)

from kivy.storage.jsonstore import JsonStore
global store
store = JsonStore('store.json')

from kivy.loader import Loader
Loader.loading_image = 'loader.png'
Loader.error_image = 'loader.png'

global nds # navigation drawers
nds = []

global puzzlegrids
puzzlegrids = []

global lang
if store.exists('lang'):
    global lang
    lang = store.get('lang')['value']
else:
    if locale.getdefaultlocale()[0] == 'ru_RU':
        global lang
        lang = 'rus'
    else:
        global lang
        lang = 'eng'

if store.exists('music'):
    sounds['forest'].volume = store.get('music')['value']
if store.exists('effects'):
    for key in ['correct', 'incorrect', 'flip', 'click']:
        sounds[key].volume = store.get('effects')['value']

global health
if store.exists('health'):
    global health
    health = store.get('health')['value']
else:
    global health
    health = 3

global sc
sc = Window.width*0.01/sp(1)

class SoundSlider(Slider):
    def __init__(self, name, pos_hint_y, **kwargs):
        super(SoundSlider, self).__init__(**kwargs)
        self.min = 0
        self.max = 100
        self.value = 50
        self.step = 1
        self.pos_hint = {'center_x': .65, 'center_y': pos_hint_y}
        self.name = name
        self.size_hint = (.6, .08)

class LangOption(ToggleButtonBehavior, Image):
    def __init__(self, option, **kwargs):
        super(LangOption, self).__init__(**kwargs)
        self.option = option
        self.group = 'language'
        self.allow_no_selection = False
        self.allow_stretch = True
        if self.option == 'rus':
            self.source = join('settings', 'rus.png')
        elif self.option == 'eng':
            self.source = join('settings', 'eng.png')

    def on_state(self, widget, value):
        sounds['click'].play()
        if value == 'down':
            if self.option == 'rus':
                self.source = join('settings', 'rus_selected.png')
            elif self.option == 'eng':
                self.source = join('settings', 'eng_selected.png')
        else:
            if self.option == 'rus':
                self.source = join('settings', 'rus.png')
            elif self.option == 'eng':
                self.source = join('settings', 'eng.png')

class MButton(Button):
    def __init__(self, **kwargs):
        super(MButton, self).__init__(**kwargs)
        self.background_color = (0.5, 0.5, 0.5, 1.0)
        self.size_hint = (0.8, 0.1)
        self.font_name = "FrutigerBold"
        self.font_size=str(round(6.5*sc,1))+'dp'
        pass
    
    def on_press(self, *args):
        sounds['click'].play()
        if self.text in ('play game', u'играть'):
            app = App.get_running_app()
            if app.root.current == "Menu":
                self.parent.parent.current = "GameScreen 0"
            else:
                for nd in nds:
                    if nd.state == 'open':
                        nd.toggle_state()
        elif self.text in ('settings', u'настройки'):
            app = App.get_running_app()
            app.root.current = "Settings"
        elif self.text in ('restart', u'заново'):
            global health
            health = 3
            app = App.get_running_app()
            if app.root.current == "Menu":
                self.parent.parent.current = "GameScreen 0"
            else:
                for nd in nds:
                    if nd.state == 'open':
                        nd.toggle_state()
                if app.root.current == "GameScreen 0":
                    app.root.current = "GameScreen 1"
                else:
                    app.root.current = "GameScreen 0"
        elif self.text in (u'выход', 'exit'):
            store.put('health', value=health)
            store.put('lang', value=lang)
            store.put('music', value=sounds['forest'].volume)
            store.put('effects', value=sounds['click'].volume)
            stopTouchApp()
            #App.get_running_app().stop()
        
class Logo(Image):
    def __init__(self, **kwargs):
        super(Logo, self).__init__(**kwargs)
        self.bind(pos = self.set_size)
    
    def set_size(self, *args):
        self.width = self.parent.children[0].width
        self.height = self.width/1.411

class Pic(AsyncImage):
    def __init__(self, source, num, **kwargs):
        super(Pic, self).__init__(**kwargs)
        self.source=source.replace('https','http')
        self.num=num
        self.name='pic'+str(num)
        self.allow_stretch=True
        self.clicked=False
    
    def on_touch_down(self, touch, *args):
        if hasattr(self._coreimage, 'loaded'):
            if self._coreimage.loaded:
                if self.num == 1:
                    global pic1_c
                    pic1_c = self.center
                    global c
                    c = self.parent.center
                if self.collide_point(*touch.pos):
                    if not self.parent.parent.active_question.used and not self.parent.parent.active_question.busy:
                        self.parent.selected_pic=self.num
                        self.parent.check_answer()
                        if not self.clicked:
                            self.clicked=True
                            for s in Scorer.instances:
                                if s.parent.name == 'memoryframe':
                                    if s.parent.img_counter<9:
                                        annotation = self.parent.parent.active_question.data['annotation'][self.num-1]
                                        if not annotation in s.parent.active_question.annotations:
                                            s.parent.img_counter += 1
                                            s.parent.imgbox.add_widget(MemoryPic(self.texture, s.parent.img_counter))
                                            s.parent.active_question.annotations.append(annotation)
                                    break
                    
    def reload(self, *args):
        self.source=self.parent.parent.active_question.data.get('images', ['']*4)[self.num-1].replace('https','http')
        self.clicked=False

class MemoryPic(AsyncImage):
    def __init__(self, texture, num, **kwargs):
        super(MemoryPic, self).__init__(**kwargs)
        self.texture=texture
        self.num=num
        self.allow_stretch=True

    def on_touch_down(self, touch, *args):
        if self.collide_point(*touch.pos):
            if self.num == self.parent.parent.active_question.answer:
                self.parent.parent.active_question.move_next()
                
class PuzzlePic(AsyncImage):
    def __init__(self, source, num, pic, **kwargs):
        super(PuzzlePic, self).__init__(**kwargs)
        self.source=source.replace('https','http')
        self.num=num
        self.name='pic'+str(num)
        self.allow_stretch=True
        self.pic=pic

    def on_touch_down(self, touch, *args):
        if self.collide_point(*touch.pos):
            if not self.parent.blocked:
		if self.parent.selected_pic_1==None:
		    self.parent.selected_pic_1=self
		    self.parent.selected_pic_1_pos=(self.pos[0], self.pos[1])
		else:
		    self.parent.selected_pic_2=self
		    self.parent.selected_pic_2_pos=(self.pos[0], self.pos[1])
		    self.parent.swap_parts()

    def on_touch_move(self, touch, *args):
	if self.collide_point(*touch.pos):
            if not self.parent.blocked:
		if self.parent.selected_pic_1==None:
		    self.parent.selected_pic_1=self
		    self.parent.selected_pic_1_pos=(self.pos[0], self.pos[1])
		elif self.parent.selected_pic_1==self:
		    pass
		else:
		    self.parent.selected_pic_2=self
		    self.parent.selected_pic_2_pos=(self.pos[0], self.pos[1])
		    self.parent.swap_parts()

    def reload(self, *args):
        pass
        # self.source=self.parent.parent.active_question.data.get('parts', ['']*9)[self.pic]

class PuzzleGrid(GridLayout):
    def __init__(self, **kwargs):
        super(PuzzleGrid, self).__init__(**kwargs)
        self.cols=3
        self.name='puzzlegrid'
        p=0.005*Window.width
        self.padding=[p,p,p,p]
        self.spacing=[0,0]
        self.size_hint_x=1
        self.size_hint_y=Window.width*1./(Window.height*0.92)
        self.pos_hint={'center_x':.5, 'center_y':.5}
        self.selected_pic_1=None
        self.selected_pic_2=None
        self.selected_pic_1_pos=None
        self.selected_pic_2_pos=None
        self.blocked=False

    def repos(self, *args):
        if self.parent.active_question.data.get('parts', 0)==0:
            self.pos_hint={'center_x':-.5, 'center_y':-.5}
        else:
            self.pos_hint={'center_x':.5, 'center_y':.5}

    def check_grid(self, *args):
        parts = [s.replace('https', 'http') for s in self.parent.active_question.data['parts']]
        sources = []
        for i in range(len(parts)):
            for part in self.children:
                if part.num == i:
                    sources.append(part.source)
                    break
        if sources == parts:
            self.blocked = True
            Clock.schedule_once(self.show_response, 2.)
            Clock.schedule_once(self.parent.active_question.change_screens, 4.)

    def reload(self, *args):
        self.clear_widgets()
        if not self.parent.active_question.data.get('parts', 0)==0:
            parts = self.parent.active_question.data['parts']
            self.cols = int(len(parts)**.5)
            used_nums = range(len(parts))
            for i,c in enumerate(used_nums):
                part = PuzzlePic(source=parts[c], num=i, pic=c)
                part.reload()
                self.add_widget(part)

    def shuffle_check(self, *args):
        app = App.get_running_app()
        if hasattr(self.parent.parent.parent.parent.parent.parent, 'current'):
            if self.parent.parent.parent.parent.parent.parent.current == app.root.current:
                ready_flag = True
                for pic in self.children:
                    if hasattr(pic._coreimage, 'loaded'):
                        if not pic._coreimage.loaded:
                            ready_flag = False
                            break
                    else:
                        ready_flag = False
                        break
                if ready_flag:
                    self.shuffle()
                else:
                    Clock.schedule_once(self.shuffle_check, 2.)
                
    def shuffle(self, *args):
        app = App.get_running_app()
        if hasattr(self.parent.parent.parent.parent.parent.parent, 'current'):
            if self.parent.parent.parent.parent.parent.parent.current == app.root.current:
                while True:
                    used_nums = range(len(self.children))
                    random.shuffle(used_nums)
                    correct_order = range(len(self.children))
                    comparison = [0 if x==y else 1 for x,y in zip(correct_order,used_nums)]
                    if sum(comparison)>round(len(self.children)/2.):
                        break
                        
                parts_pos = []
                for i in range(len(self.children)):
                    for part in self.children:
                        if part.num == i:
                            parts_pos.append((part.pos[0], part.pos[1]))
                            break
                
                for i,c in enumerate(used_nums):
                    for part in self.children:
                        if part.num == i:
                            part.num = c
                            anim = Animation(pos=parts_pos[c], d=.5)
                            anim.start(part)
                            break
                self.release()

    def show_response(self, *args):
        if lang == 'rus':
            self.parent.add_widget(ResponseLabel(text=u'верно', target=0, mode='puzzle'))
        else:
            self.parent.add_widget(ResponseLabel(text='correct', target=0, mode='puzzle'))
        sounds['correct'].play()

    def release(self, *args):
	self.blocked=False

    def swap_parts(self, *args):
        if not self.blocked:
	    self.blocked=True
            anim_1 = Animation(pos=self.selected_pic_2_pos, d=.5)
            anim_1.start(self.selected_pic_1)
            anim_2 = Animation(pos=self.selected_pic_1_pos, d=.5)
            anim_2.start(self.selected_pic_2)
            sounds['flip'].play()
	    Clock.schedule_once(self.release, .5)
            nums = [self.selected_pic_1.num, self.selected_pic_2.num]
            nums_copy = nums[:]
            self.selected_pic_1.num, self.selected_pic_2.num = nums_copy[1], nums_copy[0]
            self.selected_pic_1 = None
            self.selected_pic_2 = None
            self.check_grid()
                     
class PicGrid(GridLayout):
    def __init__(self, **kwargs):
        super(PicGrid, self).__init__(**kwargs)
        self.cols=2
        self.name='picgrid'
        p=0.005*Window.width
        self.padding=[p,p,p,p]
        self.spacing=[p,p]
        self.size_hint_x=1
        self.size_hint_y=Window.width*1./(Window.height*0.92)
        self.pos_hint={'center_x':.5, 'center_y':.5}
        self.selected_pic=None

    def repos(self, *args):
        if self.parent.active_question.data.get('parts', 0)==0:
            self.pos_hint={'center_x':.5, 'center_y':.5}
        else:
            self.pos_hint={'center_x':-.5, 'center_y':-.5}
    
    def check_answer(self, *args):
        self.parent.active_question.busy=True
        if self.selected_pic==self.parent.active_question.data['answer']:
            if lang == 'rus':
                self.parent.add_widget(ResponseLabel(text=u'верно', target=self.selected_pic))
            else:
                self.parent.add_widget(ResponseLabel(text='correct', target=self.selected_pic))
            sounds['correct'].play()
	elif self.selected_pic==self.parent.active_question.data.get('preselect', 0):
	    self.parent.active_question.busy=False
        else:
            if lang == 'rus':
                self.parent.add_widget(ResponseLabel(text=u'неверно', target=self.selected_pic))
            else:
                self.parent.add_widget(ResponseLabel(text='incorrect', target=self.selected_pic))
            sounds['incorrect'].play()
            
class InfoLabel(Widget):
    def __init__(self, text, target, response, **kwargs):
        super(InfoLabel, self).__init__(**kwargs)
        self.text=text
        self.name='infolabel'
        self.size_hint=(.51,.2)
        self.target=target
        self.response=response
        self.resized=False    
        self.bind(size=partial(self.draw,self.response), pos=partial(self.draw,self.response))
        
        if not self.response=='preselect':
            Clock.schedule_once(self.die, 2.)
        
    def draw(self, response, *args):
        if not self.resized:
            step = 2.*(c[0]-pic1_c[0])
            self.canvas.clear()
            with self.canvas:
                if response in ('correct', u'верно'):
                    self.color = Color(76/255.,187/255.,23/255.,1)
                elif response in ('incorrect', u'неверно'):
                    #self.color = Color(1,20/255.,147/255.,1)
                    self.colot = Color(204/255.,0,0,1)
                elif response=='preselect':
                    self.color = Color(1,153/255.,0,1)
            
                self.rect = Rectangle(size=self.size, pos=self.pos)
                label = Label(text='\n'+self.text, pos=self.pos, font_size=str(round(4*sc,1))+'dp', text_size=(self.width, None), markup=True, halign='center', size=self.size, font_name='FrutigerBoldItalic')
                
                def resize(self, *args):
                    #self.size=label.texture_size
                    self.parent.size=(self.texture_size[0], self.texture_size[1])
                    if self.parent.target==1:
                        pos=(.5-step/(2.*Window.width)-0.05/Window.width, .5+step*1./(Window.height*0.92))
                    elif self.parent.target==2:
                        pos=(.5+step/(2.*Window.width)+0.05/Window.width, .5+step*1./(Window.height*0.92))
                    elif self.parent.target==3:
                        pos=(.5-step/(2.*Window.width)-0.05/Window.width, .5-step*1./(Window.height*0.92))
                    elif self.parent.target==4:
                        pos=(.5+step/(2.*Window.width)+0.05/Window.width, .5-step*1./(Window.height*0.92))
                    self.parent.center_x=pos[0]*Window.width
                    self.parent.center_y=pos[1]*Window.height*0.92
                    self.center_x=pos[0]*Window.width
                    self.center_y=pos[1]*Window.height*0.92
                    self.parent.resized=True
                label.bind(texture_size=resize)
                self.add_widget(label)
    
    def die(self, *args):
        self.parent.active_question.busy=False
        self.parent.remove_widget(self)

class Question(Widget):
    def __init__(self, **kwargs):
        super(Question, self).__init__(**kwargs)
        self.points = 3
        self.used = False
        self.busy = False
	question_types = ['Biogeographic Regions', 'Primary Diet basic', 'Primary Diet detailed',
                          'Lifespan (wild, undetermined) - undetermined - average - years',
                          'Lifespan (captivity, undetermined) - undetermined - average - years',
                          'IUCN Red List', 'Mass - average - g', 'Mating System',
                          'Sexual Dimorphism', 'Key Behaviors', 'Positive Impacts', 'Negative Impacts',
                          'Key Reproductive Features', 'Parental Investment', 'Communication Channels',
                          'Perception Channels'] #preselect questions excluded
        next_question_type = random.choice(question_types)
        self.data = generate_question(next_question_type, lang)

    def lose_points(self, *args):
	if self.points>0:
            self.points-=1
            
    def change_screens(self, *args):
        for s in Scorer.instances:
            if s.parent.name == 'memoryframe':
                if s.parent.img_counter >= 9:
                    self.parent.parent.parent.parent.parent.parent.current  = "MemoryScreen"
                    s.parent.active_question.generate_questions()
                    break
        else:
            if self.parent.parent.parent.parent.parent.name == "GameScreen 0":
                self.parent.parent.parent.parent.parent.parent.current = "GameScreen 1"
                for nd in nds:
                    if nd.state == 'open':
                        nd.toggle_state()
            else:
                self.parent.parent.parent.parent.parent.parent.current = "GameScreen 0"
            
    def move_next(self, *args):
        global health
        health = health*.7 + self.parent.active_question.points*.3
        for s in Scorer.instances:
            s.update()
	
        self.parent.puzzlegrid.blocked=False
        self.used = False
        question_types = ['Species', 'Biogeographic Regions', 'Primary Diet basic', 'Primary Diet detailed',
                          'Lifespan (wild, undetermined) - undetermined - average - years',
                          'Lifespan (captivity, undetermined) - undetermined - average - years',
                          'IUCN Red List', 'Family', 'Mass - average - g', 'Mating System',
                          'Sexual Dimorphism', 'Terrestrial Biomes', 'Key Behaviors', 'Positive Impacts',
                          'Negative Impacts', 'Puzzle', 'Key Reproductive Features', 'Parental Investment',
                          'Communication Channels', 'Perception Channels']
        question_types_test = ['Mass - average - g']
        next_question_type = random.choice(question_types)
        self.data = generate_question(next_question_type, lang)
        self.points = 3
        for wid in self.parent.children:
            if hasattr(wid, 'name'):
                if wid.name == 'hframe' or wid.name == 'infolabel':
                    Clock.schedule_once(wid.die, 0.001)
        for mp in self.parent.maxpoints:
            mp.update()
        for q in self.parent.q_label:
            q.reload()

        for pic in self.parent.grid.children:
            pic.reload()
        self.parent.grid.repos()
        self.parent.puzzlegrid.reload()
        self.parent.puzzlegrid.repos()

        if not self.data.get('preselect', 0)==0:
            target=self.data.get('preselect', 0)
            self.parent.add_widget(HighlightFrame(target=target, response='preselect'))
            self.parent.add_widget(InfoLabel(text=self.data['annotation'][target-1], target=target, response='preselect'))

class Scorer(Label):
    instances = []
    def __init__(self, shift, **kwargs):
        super(Scorer, self).__init__(**kwargs)
        self.__class__.instances.append(weakref.proxy(self))
	self.score=round(health,2)
	self.name='scorer'
	self.font_name='FrutigerBold'
	self.font_size=str(round(4.5*sc,1))+'dp'
	if lang == 'rus':
            self.text=u'[b]здоровье: '+'{0:.3g}'.format(self.score)+'[/b]'
        else:
            self.text='[b]health: '+'{0:.3g}'.format(self.score)+'[/b]'
	self.markup=True

	if shift==(0,0): 
	    self.color=[1,1,1,1]
	else:
	    self.color=[154/255., 10/255., 53/255., 1]

	self.text_size=(Window.width, None)
	self.size=self.texture_size
	self.pos_hint={'center_x':.7375+shift[0]*sp(.4*round(sc,1))*1./Window.width, 'center_y':.1+shift[1]*sp(.4*round(sc,1))*1./(Window.height*0.92)}
	self.halign='center'
    
    def update(self, *args):
	self.score=round(health,2)
	if lang == 'rus':
            self.text=u'[b]здоровье: '+'{0:.3g}'.format(self.score)+u'[/b]'
        else:
            self.text='[b]health: '+'{0:.3g}'.format(self.score)+'[/b]'
	for child in self.parent.children:
            if getattr(child, 'name', 'noname') == 'heartline':
                child.update(self.score)
                break

class MaxPoints(Label):
    def __init__(self, shift, **kwargs):
        super(MaxPoints, self).__init__(**kwargs)
	self.font_size=str(round(4.5*sc,1))+'dp'
	self.font_name='FrutigerBold'
	self.name='maxpoints'
	self.markup=True
	if shift==(0,0): 
	    self.color=[1,1,1,1]
	else:
	    self.color=[154/255., 10/255., 53/255., 1]
	self.text_size=(Window.width, None)
        self.size=self.texture_size
        self.pos_hint={'center_x':.2625+shift[0]*sp(.4*round(sc,1))*1./Window.width, 'center_y':.1+shift[1]*sp(.4*round(sc,1))*1./(Window.height*0.92)}
	self.halign='center'

        Clock.schedule_once(self.update, .1)
    
    def update(self, *args):
	self.maxpoints=self.parent.active_question.points
	if lang == 'rus':
            self.text=u'[b]осталось очков: '+str(self.maxpoints)+u'[/b]'
        else:
            self.text='[b]points left: '+str(self.maxpoints)+'[/b]'
        for child in self.parent.children:
            if child.name == 'starline':
                child.update(self.maxpoints)
                break
    
class StarLine(BoxLayout):
    def __init__(self, **kwargs):
        super(StarLine, self).__init__(**kwargs)
        self.name='starline'
        self.orientation='horizontal'
        self.size_hint=(.25,.045)
        self.pos_hint={'x': .14, 'y': .025}
        self.stars=[]
        
        for i in range(3):
            star = Image(source='star.png', allow_stretch=True)
            self.stars.append(star)
            self.add_widget(star)
        
    def update(self, points, *args):
        if points == 3:
            for star in self.stars:
                star.source='star.png'
		star.opacity=1
		if hasattr(star, 'init_pos'): star.pos = star.init_pos
        elif points == 2:
	    for star in self.stars:
                star.init_pos = (star.pos[0], star.pos[1])
	    anim = Animation(y=self.y+Window.height, opacity=.1, t='out_quad')
            anim.start(self.stars[2])
        elif points == 1:
	    anim = Animation(y=self.y+Window.height, opacity=.1, t='out_quad')
            anim.start(self.stars[1])
        elif points == 0:
	    anim = Animation(y=self.y+Window.height, opacity=.1, t='out_quad')
            anim.start(self.stars[0])
            
class HeartLine(BoxLayout):
    def __init__(self, **kwargs):
        super(HeartLine, self).__init__(**kwargs)
        self.name='heartline'
        self.orientation='horizontal'
        self.size_hint=(.25,.045)
        self.pos_hint={'x': .61, 'y': .025}
        self.hearts=[]
        
        for i in range(3):
            heart = Image(source='heart.png', allow_stretch=True)
            self.hearts.append(heart)
            self.add_widget(heart)
        
    def update(self, points, *args):
        a = [(i,abs(points-0.001-i/2.)) for i in range(7)]
	a = sorted(a,key=lambda tup: tup[1])
	b = a[0][0]/2.
	for j in range(3):
	    if j+1<=b:
	        self.hearts[j].source='heart.png'
	    elif j<=b and b-int(b)==.5:
		self.hearts[j].source='heart_half.png'
            else:
		self.hearts[j].source='heart_no.png'

class QuestionLabel(Label):
    def __init__(self, text, shift, **kwargs):
        super(QuestionLabel, self).__init__(**kwargs)
        self.name='qlabel'
        self.font_name='FrutigerBold'
        self.font_size=str(round(6.5*sc,1))+'dp'
        self.markup=True
        self.text='[b]'+text+'[/b]'
        self.halign='center'
        if shift==(0,0): 
	    #self.color=[173/255.,1,47/255.,1]
	    self.color=[1,1,1,1]
	else:
	    self.color=[96/255.,58/255.,20/255.,1]
        self.text_size=(Window.width, None)
        self.size=self.texture_size
        self.pos_hint={'center_x':.5+shift[0]*sp(.6*round(sc,1))*1./Window.width, 'center_y':.9+shift[1]*sp(.6*round(sc,1))*1./(Window.height*0.92)}

    def reload(self, *args):
	self.text='[b]'+self.parent.active_question.data['question']+'[/b]'

class ResponseLabel(Widget):
    def __init__(self, text, target, mode='quiz', **kwargs):
        super(ResponseLabel, self).__init__(**kwargs)
        self.size_hint=(1.,.12)
        self.pos_hint={'center_x':.5, 'center_y': .5}
        self.bind(size=self.draw, pos=self.draw, center_x=self.draw, center_y=self.draw)
        self.name='rlabel'
        self.text=text
        self.target=target
        if mode=='quiz':
            Clock.schedule_once(self.hide, 1.5)
            Clock.schedule_once(self.die, 4.5)
            Clock.schedule_once(self.call_annotation, 1.5)
        elif mode=='puzzle':
            Clock.schedule_once(self.die, 2.)
        
    def draw(self, *args):
        self.canvas.clear()
        self.clear_widgets()
        with self.canvas:
	    if self.text in ('correct', u'верно'):
                self.color = Color(76/255.,187/255.,23/255.,1)
	    elif self.text in ('incorrect', u'неверно'):
		self.color = Color(204/255.,0,0,1)
            self.rect = Rectangle(size=self.size, pos=self.pos)
        self.add_widget(Label(text='[b]'+self.text+'[/b]', markup=True, size=self.size, pos=self.pos, font_size=str(round(7*sc,1))+'dp', font_name='FrutigerBold'))
        
    def add_hframe(self, *args):
        self.parent.add_widget(HighlightFrame(target=self.target, response=self.text))
    
    def add_infolabel(self, text, *args):
        self.parent.add_widget(InfoLabel(text=text, target=self.target, response=self.text))
        
    def die(self, *args):
        self.parent.remove_widget(self)
    
    def hide(self, *args):
        self.pos_hint={'center_x':-1, 'center_y':-1}
        
    def call_annotation(self, *args):
        self.add_hframe()
	text=self.parent.active_question.data['annotation'][self.target-1]
        self.add_infolabel(text=text)
        
class Gradient(object):
    @staticmethod
    def horizontal(rgba_left, rgba_right):
        texture = Texture.create(size=(2, 1), colorfmt="rgba")
        pixels = rgba_left + rgba_right
        pixels = [chr(int(v * 255)) for v in pixels]
        buf = ''.join(pixels)
        texture.blit_buffer(buf, colorfmt='rgba', bufferfmt='ubyte')
        return texture

    @staticmethod
    def vertical(rgba_top, rgba_bottom):
        texture = Texture.create(size=(1, 2), colorfmt="rgba")
        pixels = rgba_bottom + rgba_top
        pixels = [chr(int(v * 255)) for v in pixels]
        buf = ''.join(pixels)
        texture.blit_buffer(buf, colorfmt='rgba', bufferfmt='ubyte')
        return texture

class Band(Widget):
    def __init__(self, **kwargs):
        super(Band, self).__init__(**kwargs)
	self.size=(Window.width, Window.height*0.04)
        self.pos=(0, Window.height*0.07)
	self.name='band'

        with self.canvas:
            self.color = Color(154/255., 10/255., 53/255., .6)
            self.rect = Rectangle(size=self.size, pos=self.pos)

class SettingsBand(Widget):
    def __init__(self, **kwargs):
        super(SettingsBand, self).__init__(**kwargs)
	self.size=(Window.width, Window.height*0.1)
        self.pos=(0, Window.height*0.45)
	self.name='settingsband'

        with self.canvas:
            self.color = Color(0, 0, 0, .6)
            self.rect = Rectangle(size=self.size, pos=self.pos)

class HighlightFrame(Widget):
    def __init__(self, target, response, **kwargs):
        super(HighlightFrame, self).__init__(**kwargs)
        self.name='hframe'
	self.response=response
	self.target=target

	Clock.schedule_once(self.create_frame, .001)

    def create_frame(self, *args):
        if not self.parent.active_question.used:
            if self.response in ('correct', u'верно'):
                self.parent.active_question.used = True
                Clock.schedule_once(self.parent.active_question.change_screens, 3.)
                color=(76/255.,187/255.,23/255.,1)
            if self.response in ('incorrect', u'неверно'):
                self.parent.active_question.lose_points()
                for mp in self.parent.maxpoints:
                    mp.update()
                color=(204/255.,0,0,1)
            if self.response=='preselect':
                color=(1,153/255.,0,1)
        
            if self.target==1: 
                path=[0,0,-1,0,-1,1,0,1,0,0]
            if self.target==2: 
                path=[0,0,0,1,1,1,1,0,0,0]
            if self.target==3: 
                path=[0,0,0,-1,-1,-1,-1,0,0,0]
            if self.target==4:
                path=[0,0,1,0,1,-1,0,-1,0,0]
                    
            points=[]
            step = 2*(c[0]-pic1_c[0]-0.005*Window.width)
            for i in range(len(path)):
                if i%2==0:
                    if self.target==1:
                        points.append(c[0]-0.005*Window.width+path[i]*step)
                    if self.target==2:
                        points.append(c[0]+0.005*Window.width+path[i]*step)

                    if self.target==3:
                        points.append(c[0]-0.005*Window.width+path[i]*step)
                    if self.target==4:
                        points.append(c[0]+0.005*Window.width+path[i]*step)
                else:
                    if self.target==1:
                        points.append(c[1]+0.005*Window.width+path[i]*step)
                    if self.target==2:
                        points.append(c[1]+0.005*Window.width+path[i]*step)
                    if self.target==3:
                        points.append(c[1]-0.005*Window.width+path[i]*step)
                    if self.target==4:
                        points.append(c[1]-0.005*Window.width+path[i]*step)
                    
            with self.canvas:
                self.color=Color(color[0],color[1],color[2],color[3])
                Line(points=points, width=sp(round(1*sc,1)), closed=True, cap='square', joint='miter')
                
            if not self.response=='preselect':
                Clock.schedule_once(self.die, 2.)
        
    def die(self, *args):
        self.parent.remove_widget(self)

class Caption(Label, FloatLayout):
    def __init__(self, **kwargs):
        super(Caption, self).__init__(**kwargs) 
	with self.canvas:
            Rectangle(size=Window.size, pos=(0,0), texture=Gradient.horizontal((107/255., 7/255., 37/255., 1), (154/255., 10/255., 53/255., 1)))
	self.height=Window.height*0.05
	self.width=Window.width*0.6
	self.add_widget(Label(text='Biophilia', font_name='FrutigerBold', pos=(-Window.width*0.175, Window.height*0.92), allow_stretch=True, font_size=str(round(6.5*sc,1))+'dp', halign='left', color=[1,1,1,1]))
	self.add_widget(Image(source='logo.png', pos=(Window.width*0.04, Window.height*0.92), allow_stretch=True))
	self.add_widget(NDButton())
        self.add_widget(SkipButton())

class NDButton(Image):
    def __init__(self, **kwargs):
        super(NDButton, self).__init__(**kwargs)
	self.source='3stripes.png'
	self.pos=(-Window.width*0.4, Window.height*0.92)
	self.allow_stretch=True

    def on_touch_down(self, touch, *args):  
        if self.collide_point(*touch.pos):
            sounds['click'].play()
            self.parent.parent.parent.parent.toggle_state()

class SettingsStateButton(Image):
    def __init__(self, option, **kwargs):
        super(SettingsStateButton, self).__init__(**kwargs)
        self.option=option
        self.size_hint=(.2,.2)
        if self.option == 'apply':
            self.source = join('settings', 'apply.png')
            self.pos_hint = {'center_x': .3, 'center_y': .1}
        elif self.option == 'cancel':
            self.source = join('settings', 'cancel.png')
            self.pos_hint = {'center_x': .7, 'center_y': .1}
	self.allow_stretch=True

    def on_touch_down(self, touch, *args):  
        if self.collide_point(*touch.pos):
            sounds['click'].play()
            if self.option == 'apply':
                for child in self.parent.children:
                    if hasattr(child, 'name'):
                        if child.name == 'music_slider':
                            sounds['forest'].volume = child.value_normalized
                        elif child.name == 'effects_slider':
                            for key in ['click', 'correct', 'incorrect', 'flip']:
                                sounds[key].volume = child.value_normalized
                    if hasattr(child, 'option'):
                        if child.option == 'eng':
                            if child.state == 'down':
                                global lang
                                lang = 'eng'
                            else:
                                global lang
                                lang = 'rus'
                            break
                for pg in puzzlegrids:
                    pg.parent.active_question.move_next()
                self.parent.parent.current='Menu'
            elif self.option == 'cancel':
                self.parent.parent.current='Menu'
                   
class SkipButton(Image):
    instances = []
    def __init__(self, **kwargs):
        super(SkipButton, self).__init__(**kwargs)
        self.__class__.instances.append(weakref.proxy(self))
	self.source='skip.png'
	self.pos=(Window.width*0.4, Window.height*0.92)
	self.allow_stretch=True
    
    def hide(self, *args):
        self.pos=(Window.width*0.4, -500)
    
    def show(self, *args):
        self.pos=(Window.width*0.4, Window.height*0.92)

    def on_touch_down(self, touch, *args):  
        if self.collide_point(*touch.pos):
            sounds['click'].play()
            app= App.get_running_app()
            if app.root.current == "MemoryScreen":
                for s in Scorer.instances:
                    if s.parent.name == 'memoryframe':
                        s.parent.active_question.return_to_quiz()
                        break
            else:
                for pg in puzzlegrids:
                    if pg.parent.parent == self.parent.parent:
                        pg.parent.active_question.points = 0
                        pg.parent.active_question.change_screens()
                        break        
        
class MainBox(BoxLayout):
    def __init__(self, **kwargs):
        super(MainBox, self).__init__(**kwargs)
        self.orientation='vertical'
	self.add_widget(Caption(size_hint_y=.08))
        self.add_widget(MainFrame(size_hint_y=.92))
            
class MainFrame(FloatLayout, StencilView):
    def __init__(self, **kwargs):
        super(MainFrame, self).__init__(**kwargs)
	self.name='mainframe'

	with self.canvas.before:
	    texture=CoreImage('bg.jpg').texture
	    texture.wrap='repeat'
	    texture.uvsize=[2,3]
	    self.rect=Rectangle(pos=(0,0), size=Window.size, texture=texture)

	self.active_question = Question()
	self.add_widget(self.active_question)

        self.grid = PicGrid()
        pic1 = Pic(source=self.active_question.data.get('images', ['']*4)[0], num=1)
        pic2 = Pic(source=self.active_question.data.get('images', ['']*4)[1], num=2)
        pic3 = Pic(source=self.active_question.data.get('images', ['']*4)[2], num=3)
        pic4 = Pic(source=self.active_question.data.get('images', ['']*4)[3], num=4)
        self.grid.add_widget(pic1)
        self.grid.add_widget(pic2)
        self.grid.add_widget(pic3)
        self.grid.add_widget(pic4)
        #pic1.reload()
        #pic2.reload()
        #pic3.reload()
        #pic4.reload()
        self.add_widget(self.grid)
        self.grid.repos()

        self.puzzlegrid = PuzzleGrid()
        global puzzlegrids
        puzzlegrids.append(self.puzzlegrid)
        self.add_widget(self.puzzlegrid)
        self.puzzlegrid.reload()
        self.puzzlegrid.repos()

        def add_preselect(*args):
          target=self.active_question.data.get('preselect', 0)
          self.grid.parent.add_widget(HighlightFrame(target=target, response='preselect'))
          self.grid.parent.add_widget(InfoLabel(text=self.active_question.data['annotation'][target-1], target=target, response='preselect'))

    	if not self.active_question.data.get('preselect', 0)==0:
	  Clock.schedule_once(add_preselect, 1.)

	#shifts = [(-1,-1),(-1,0),(-1,1),(0,1),(0,-1),(1,1),(1,0),(1,-1),(0,0)]
	shifts = [(1,-1),(1,0),(0,-1),(0,0)]
	self.q_label=[]
	for shift in shifts:
	    self.q_label.append(QuestionLabel(text=self.active_question.data['question'], shift=shift))
	for q in self.q_label:
            self.add_widget(q)

	self.add_widget(Band())

        shifts = [(-1,-1),(-1,0),(-1,1),(0,1),(0,-1),(1,1),(1,0),(1,-1),(0,0)]
	self.scorer=[]
	for shift in shifts:
	    self.scorer.append(Scorer(shift=shift))
	for s in self.scorer:
            self.add_widget(s)

        shifts = [(-1,-1),(-1,0),(-1,1),(0,1),(0,-1),(1,1),(1,0),(1,-1),(0,0)]
	self.maxpoints=[]
	for shift in shifts:
	    self.maxpoints.append(MaxPoints(shift=shift))
	for mp in self.maxpoints:
            self.add_widget(mp)
            
        self.add_widget(StarLine())
        self.add_widget(HeartLine())

        global c
        c = self.grid.center
        global pic1_c
        pic1_c = pic1.center

class MemoryBox(BoxLayout):
    def __init__(self, **kwargs):
        super(MemoryBox, self).__init__(**kwargs)
        self.orientation='vertical'
	self.add_widget(Caption(size_hint_y=.08))
        self.add_widget(MemoryFrame(size_hint_y=.92))

class MemoryFrame(FloatLayout, StencilView):
    def __init__(self, **kwargs):
        super(MemoryFrame, self).__init__(**kwargs)
	self.name='memoryframe'
	self.active_question = MemoryQuestion(self)
	self.img_counter=0
	self.imgbox=GridLayout(size_hint_x=1, size_hint_y=Window.width*1./(Window.height*0.92), pos_hint={'center_x':.5, 'center_y':.5}, rows=3, cols=3)

	with self.canvas.before:
	    texture=CoreImage('bg.jpg').texture
	    texture.wrap='repeat'
	    texture.uvsize=[2,3]
	    self.rect=Rectangle(pos=(0,0), size=Window.size, texture=texture)

	self.add_widget(self.imgbox)

	shifts = [(1,-1),(1,0),(0,-1),(0,0)]
	self.q_label=[]
	for shift in shifts:
	    self.q_label.append(QuestionLabel(text=self.active_question.question, shift=shift))
	for q in self.q_label:
            self.add_widget(q)

	self.add_widget(Band())

        shifts = [(-1,-1),(-1,0),(-1,1),(0,1),(0,-1),(1,1),(1,0),(1,-1),(0,0)]
	self.scorer=[]
	for shift in shifts:
	    self.scorer.append(Scorer(shift=shift))
	for s in self.scorer:
            self.add_widget(s)

        shifts = [(-1,-1),(-1,0),(-1,1),(0,1),(0,-1),(1,1),(1,0),(1,-1),(0,0)]
	self.maxpoints=[]
	for shift in shifts:
	    self.maxpoints.append(MaxPoints(shift=shift))
	for mp in self.maxpoints:
            self.add_widget(mp)
            
        self.add_widget(StarLine())
        self.add_widget(HeartLine())

class MemoryQuestion:
    def __init__(self, frame, *args):
        self.name='memoryquestion'
        self.frame=frame
        self.points=3
        self.question="Click on "
        self.annotations=[]
        self.annotations_shuffled=[]
        self.qpos=0
        self.answer=0

    def generate_questions(self, *args):
        self.annotations_shuffled=random.sample(self.annotations, len(self.annotations))
        if lang == 'rus':
            self.question = u"Нажмите на фото животного:\n"+self.annotations_shuffled[0]
        else:
            self.question="Click on "+self.annotations_shuffled[0]
        self.answer=self.annotations.index(self.annotations_shuffled[0])+1
        for q in self.frame.q_label:
            q.text='[b]'+self.question+'[/b]'

    def move_next(self, *args):
        if self.qpos < len(self.annotations)-1:
            self.qpos+=1
            if lang == 'rus':
                self.question=u"Нажмите на фото животного:\n"+self.annotations_shuffled[self.qpos]
            else:
                self.question="Click on "+self.annotations_shuffled[self.qpos]
            self.answer=self.annotations.index(self.annotations_shuffled[self.qpos])+1
            for q in self.frame.q_label:
                q.text='[b]'+self.question+'[/b]'
        else:
            if lang == 'rus':
                self.frame.add_widget(ResponseLabel(text=u'верно', target=0, mode='puzzle'))
            else:
                self.frame.add_widget(ResponseLabel(text='correct', target=0, mode='puzzle'))
            sounds['correct'].play()
            Clock.schedule_once(self.return_to_quiz, 2.)

    def return_to_quiz(self, *args):
        for nd in nds:
            if nd.state == 'open':
                nd.toggle_state()
        app = App.get_running_app()
        app.root.current = "GameScreen 0"           
        
class GameScreen(Screen):
    def __init__(self, **kwargs):
        super(GameScreen, self).__init__(**kwargs)

    def on_pre_enter(self, *args):
        for nd in nds:
            if nd.state == 'open':
                nd.toggle_state()

    def on_enter(self, *args):
        if self.name == 'MemoryScreen':
            for s in SkipButton.instances:
                s.show()
        else:
            for s in SkipButton.instances:
                s.hide()
            for s in Scorer.instances:
                s.update()
            for pg in puzzlegrids:
                if pg.parent.parent.parent.parent.parent == self:
                    if pg.pos_hint['center_x'] == .5:
                        pg.blocked = True
                        Clock.schedule_once(pg.shuffle_check, 2.)
                        for s in SkipButton.instances:
                            s.show()
                        break
                    
    def on_leave(self, *args):
        for pg in puzzlegrids:
            if pg.parent.parent.parent.parent.parent == self:
                pg.parent.active_question.move_next()
                break
        if self.name == 'MemoryScreen':
            for s in Scorer.instances:
                if s.parent.name == 'memoryframe':
                    s.parent.img_counter = 0
                    s.parent.imgbox.clear_widgets()
                    s.parent.active_question.annotations=[]
                    s.parent.active_question.annotations_shuffled=[]
                    s.parent.active_question.qpos=0
                    s.parent.active_question.answer=0
                    break

class SettingsScreen(Screen):
    def __init__(self, **kwargs):
        super(SettingsScreen, self).__init__(**kwargs)

    def on_pre_enter(self, *args):
        self.clear_widgets()
        self.add_widget(SettingsBand())

        if lang == 'eng':
            self.add_widget(Image(allow_stretch=True, source=join('settings', 'settings.png'), size_hint=(.15, .15*Window.width/Window.height), pos_hint={'center_x': .32, 'center_y': .5}))
            self.add_widget(Label(text='settings', pos_hint={'center_x': .57, 'center_y': .5}, font_name='FrutigerBold', font_size=str(round(8*sc,1))+'dp', color=[1,1,1,1]))
            self.add_widget(Label(text='language', pos_hint={'center_x': .25, 'center_y': .38}, font_name='FrutigerBold', font_size=str(round(6.5*sc,1))+'dp', color=[1,1,1,1]))
            self.add_widget(LangOption(option='eng', pos_hint={'center_x': .6, 'center_y': .38}, size_hint=(.15, .2)))
            self.add_widget(LangOption(option='rus', pos_hint={'center_x': .85, 'center_y': .38}, size_hint=(.15, .2)))
            self.add_widget(Label(text='music', pos_hint={'center_x': .25, 'center_y': .3}, font_name='FrutigerBold', font_size=str(round(6.5*sc,1))+'dp', color=[1,1,1,1]))
            self.add_widget(Label(text='sound\neffects', pos_hint={'center_x': .25, 'center_y': .22}, font_name='FrutigerBold', font_size=str(round(6.5*sc,1))+'dp', color=[1,1,1,1]))
            self.add_widget(SoundSlider(name='music_slider', pos_hint_y=0.3))
            self.add_widget(SoundSlider(name='effects_slider', pos_hint_y=0.22))
        elif lang == 'rus':
            self.add_widget(Image(allow_stretch=True, source=join('settings', 'settings.png'), size_hint=(.15, .15*Window.width/Window.height), pos_hint={'center_x': .25, 'center_y': .5}))
            self.add_widget(Label(text=u'настройки', pos_hint={'center_x': .55, 'center_y': .5}, font_name='FrutigerBold', font_size=str(round(8*sc,1))+'dp', color=[1,1,1,1]))
            self.add_widget(Label(text=u'язык', pos_hint={'center_x': .2, 'center_y': .38}, font_name='FrutigerBold', font_size=str(round(6.5*sc,1))+'dp', color=[1,1,1,1]))
            self.add_widget(LangOption(option='eng', pos_hint={'center_x': .6, 'center_y': .38}, size_hint=(.15, .2)))
            self.add_widget(LangOption(option='rus', pos_hint={'center_x': .85, 'center_y': .38}, size_hint=(.15, .2)))
            self.add_widget(Label(text=u'музыка', pos_hint={'center_x': .2, 'center_y': .3}, font_name='FrutigerBold', font_size=str(round(6.5*sc,1))+'dp', color=[1,1,1,1]))
            self.add_widget(Label(text=u'эффекты', pos_hint={'center_x': .2, 'center_y': .22}, font_name='FrutigerBold', font_size=str(round(6.5*sc,1))+'dp', color=[1,1,1,1]))
            self.add_widget(SoundSlider(name='music_slider', pos_hint_y=0.3))
            self.add_widget(SoundSlider(name='effects_slider', pos_hint_y=0.22))
        
        self.add_widget(SettingsStateButton('apply'))
        self.add_widget(SettingsStateButton('cancel'))
        self.add_widget(Logo(id='logo', source='logo_large.png', allow_stretch=True, size_hint=(0.4, 0.5), pos_hint={'center_x': .5, 'center_y': .78}))
        
        for child in self.children:
            if hasattr(child, 'option'):
                for l in ['rus', 'eng']:
                    if child.option == l:
                        if lang == l:
                            child.state = 'down'
                        else:
                            child.state = 'normal'
            elif hasattr(child, 'name'):
                if child.name == 'music_slider':
                    child.value_normalized = sounds['forest'].volume
                elif child.name == 'effects_slider':
                    child.value_normalized = sounds['click'].volume

class MenuScreen(Screen):
    def __init__(self, **kwargs):
        super(MenuScreen, self).__init__(**kwargs)

    def on_pre_enter(self, *args):
        if lang == 'rus':
            for child in self.children:
                if hasattr(child, 'text'):
                    if child.text == 'settings':
                        child.text = u'настройки'
                    elif child.text == 'play game':
                        child.text = u'играть'
                    elif child.text == 'exit':
                        child.text = u'выход'
                    elif child.text == 'restart':
                        child.text = u'заново'
        elif lang == 'eng':
            for child in self.children:
                if hasattr(child, 'text'):
                    if child.text == u'настройки':
                        child.text = 'settings'
                    elif child.text == u'играть':
                        child.text = 'play game'
                    elif child.text == u'заново':
                        child.text = 'restart'
                    elif child.text == u'выход':
                        child.text = 'exit'

class GameFrames(ScreenManager):
    def __init__(self, **kwargs):
        super(GameFrames, self).__init__(**kwargs)
	self.transition=RiseInTransition(duration=.3)

        menu_screen=MenuScreen(name='Menu')
        with menu_screen.canvas:
            Rectangle(size=Window.size, pos=(0,0), texture=Gradient.horizontal((107/255., 7/255., 37/255., 1), (154/255., 10/255., 53/255., 1)))
        if lang == 'rus':
            menu_screen.add_widget(MButton(id='new_game_btn', text=u'играть', name='game', pos_hint={'center_x': .5, 'center_y': .46}))
            menu_screen.add_widget(MButton(id='restarts_btn', text=u'заново', name='restart', pos_hint={'center_x': .5, 'center_y': .34}))
            menu_screen.add_widget(MButton(id='settings_btn', text=u'настройки', name='settings', pos_hint={'center_x': .5, 'center_y': .22}))
            menu_screen.add_widget(MButton(id='exit_btn', text=u'выход', name='exit', pos_hint={'center_x': .5, 'center_y': .1}))
        else:
            menu_screen.add_widget(MButton(id='new_game_btn', text='play game', name='game', pos_hint={'center_x': .5, 'center_y': .46}))
            menu_screen.add_widget(MButton(id='restarts_btn', text='restart', name='restart', pos_hint={'center_x': .5, 'center_y': .34}))
            menu_screen.add_widget(MButton(id='settings_btn', text='settings', name='settings', pos_hint={'center_x': .5, 'center_y': .22}))
            menu_screen.add_widget(MButton(id='exit_btn', text='exit', name='exit', pos_hint={'center_x': .5, 'center_y': .1}))
        menu_screen.add_widget(Logo(id='logo', source='logo_large.png', allow_stretch=True, size_hint=(0.4, 0.5), pos_hint={'center_x': .5, 'center_y': .78}))
        self.add_widget(menu_screen)

        settings_screen=SettingsScreen(name='Settings')
        with settings_screen.canvas:
            Rectangle(size=Window.size, pos=(0,0), texture=Gradient.horizontal((107/255., 7/255., 37/255., 1), (154/255., 10/255., 53/255., 1)))
        self.add_widget(settings_screen)
                
        for i in range(3):
            screen = GameScreen()
            if i<2:
                screen.name='GameScreen %d' % i
            else:
                screen.name='MemoryScreen'

            def translate_buttons(self, *args):
                for ch in self.side_panel.children:
                    if hasattr(ch, 'text'):
                        if lang == 'rus':
                            if ch.text == 'settings':
                                ch.text = u'настройки'
                            elif ch.text == 'play game':
                                ch.text = u'играть'
                            elif ch.text == 'exit':
                                ch.text = u'выход'
                            elif ch.text == u'restart':
                                ch.text = u'заново'
                        elif lang == 'eng':
                            if ch.text == u'настройки':
                                ch.text = 'settings'
                            elif ch.text == u'играть':
                                ch.text = 'play game'
                            elif ch.text == u'выход':
                                ch.text = 'exit'
                            elif ch.text == u'заново':
                                ch.text = u'restart'

            navigationdrawer = NavigationDrawer()
            navigationdrawer.bind(state=translate_buttons)
            navigationdrawer.anim_type = 'slide_above_simple'
            
            side_panel = FloatLayout(orientation='vertical')
            if lang == 'rus':
                side_panel.add_widget(MButton(id='new_game_btn', text=u'играть', name='game', pos_hint={'center_x': .5, 'center_y': .46}))
                side_panel.add_widget(MButton(id='restarts_btn', text=u'заново', name='restart', pos_hint={'center_x': .5, 'center_y': .34}))
                side_panel.add_widget(MButton(id='settings_btn', text=u'настройки', name='settings', pos_hint={'center_x': .5, 'center_y': .22}))
                side_panel.add_widget(MButton(id='exit_btn', text=u'выход', name='exit', pos_hint={'center_x': .5, 'center_y': .1}))
            else:
                side_panel.add_widget(MButton(id='new_game_btn', text='play game', name='game', pos_hint={'center_x': .5, 'center_y': .46}))
                side_panel.add_widget(MButton(id='restarts_btn', text='restart', name='restart', pos_hint={'center_x': .5, 'center_y': .34}))
                side_panel.add_widget(MButton(id='settings_btn', text='settings', name='settings', pos_hint={'center_x': .5, 'center_y': .22}))
                side_panel.add_widget(MButton(id='exit_btn', text='exit', name='exit', pos_hint={'center_x': .5, 'center_y': .1}))

            side_panel.add_widget(Logo(id='logo', source='logo_large.png', allow_stretch=True, size_hint=(0.7, 0.9), pos_hint={'center_x': .5, 'center_y': .78}))
            navigationdrawer.add_widget(side_panel)
            navigationdrawer.side_panel=side_panel

            if i<2:
                navigationdrawer.add_widget(MainBox())
            else:
                navigationdrawer.add_widget(MemoryBox())

            global nds
            nds.append(navigationdrawer)
            
            screen.add_widget(navigationdrawer)
            self.add_widget(screen)
        
        self.current='Menu'
        sounds['forest'].play()

class Game(App):
    def build(self):
        self.title = 'Biophilia'
	self.icon = 'icon_small.png'
        self.game = GameFrames()
        return self.game

    def on_pause(self, *args):
        return True

    def on_resume(self, *args):
        return True

    def on_start(self, *args):
        EventLoop.window.bind(on_keyboard=self.hook_keyboard)

    def hook_keyboard(self, window, key, *args):
        if key == 27:
            for nd in nds:
               if nd.state == 'open':
                   nd.toggle_state()
            return True

if __name__=='__main__':
    Game().run()
