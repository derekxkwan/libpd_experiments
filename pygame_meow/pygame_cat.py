#gpl v3

from pylibpd import *
import array
import pygame
import numpy
from os import environ
import random

BUFFERSIZE = 1024
BLOCKSIZE = 64
FPS = 60

SCREENSIZE = (640, 480)
img_size = min(SCREENSIZE)/2
bg = (255, 255, 255)

environ['SDL_VIDEO_CENTERED'] = '1'
pygame.init()
screen = pygame.display.set_mode(SCREENSIZE)
clock = pygame.time.Clock()

class Cat(pygame.sprite.Sprite):
        def __init__(self, pos, img):
                super(Cat, self).__init__()
                size = (img_size, img_size)

                self.rect = pygame.Rect(pos, size)
                self.img = img
                self.meow_dur = 250
                self.meow_state = -1.0 # not meowing, range from 0 to meow_dur
                self.meow_frames = len(img) - 1 # first frame is rest state
                self.len_frame = float(self.meow_dur)/float(self.meow_frames) #length of a frame
                self.index = 0
                self.image = img[self.index]
                
        def update(self, dt):
                #dt should be in ms
                if self.meow_state >= 0:
                        self.meow_state = self.meow_state + dt
                        if self.meow_state <= self.meow_dur:
                                self.index = int(float(self.meow_state)/self.len_frame) + 1
                        else:
                                self.index = 0
                                self.meow_state = -1
                        self.image = self.img[self.index]
                
        def start_meow(self):
                self.meow_dur = random.randrange(250, 500) #put random dur of meow in ms
                self.meow_state = 0
                self.index = 1
                self.image = self.img[self.index]
                self.len_frame = float(self.meow_dur)/float(self.meow_frames)
                
cat_src = ['cat0.tga', 'cat1.tga', 'cat2.tga']
cat_anim = []

for cat in cat_src:
        cat_frame = pygame.image.load(cat)
        cat_frame = pygame.transform.scale(cat_frame, (img_size, img_size))
        cat_anim.append(cat_frame)

gray_cat = Cat(pos=(0,0), img=cat_anim)
spritez = pygame.sprite.Group(gray_cat)

m = PdManager(1, 2, pygame.mixer.get_init()[0], 1)
patch = libpd_open_patch('pygame_meow.pd', '.')
print "$0: ", patch

# this is basically a dummy since we are not actually going to read from the mic
inbuf = array.array('h', range(BLOCKSIZE))

# the pygame channel that we will use to queue up buffers coming from pd
ch = pygame.mixer.Channel(0)
# python writeable sound buffers
sounds = [pygame.mixer.Sound(numpy.zeros((BUFFERSIZE, 2), numpy.int16)) for s in range(2)]
samples = [pygame.sndarray.samples(s) for s in sounds]





def updatexy(event):
        libpd_float('x', float(event.pos[1]) / SCREENSIZE[1])
	libpd_float('y', float(event.pos[0]) / SCREENSIZE[0])
	libpd_bang('trig')
        gray_cat.start_meow()
        libpd_float('dur', float(gray_cat.meow_dur))

# we go into an infinite loop selecting alternate buffers and queueing them up
# to be played each time we run short of a buffer
selector = 0
quit = False
while not quit:
        dt = clock.tick(FPS) #num ms between each loop
        
	# we have run out of things to play, so queue up another buffer of data from Pd
	if not ch.get_queue():
		# make sure we fill the whole buffer
		for x in range(BUFFERSIZE):
			# let's grab a new block from Pd each time we're out of BLOCKSIZE data
			if x % BLOCKSIZE == 0:
				outbuf = m.process(inbuf)
			# de-interlace the data coming from libpd
			samples[selector][x][0] = outbuf[(x % BLOCKSIZE) * 2]
			samples[selector][x][1] = outbuf[(x % BLOCKSIZE) * 2 + 1]
		# queue up the buffer we just filled to be played by pygame
		ch.queue(sounds[selector])
		# next time we'll do the other buffer
		selector = int(not selector)
	
	for event in pygame.event.get():
		if event.type == pygame.QUIT or event.type == pygame.KEYDOWN and event.key == 27:
			quit = True
		
		if event.type == pygame.MOUSEBUTTONDOWN:
			updatexy(event)

        spritez.update(dt)
	screen.fill(bg)
        spritez.draw(screen)
	
	pygame.display.flip()

libpd_release()
