from pgzero_shim import Actor, screen, keyboard, keys, clock, go
import random

WIDTH = 600
HEIGHT = 600
TITLE = "Raketen mit Punkten"

raumschiff=Actor("baer1.png")
raumschiff.x=60
raumschiff.y=300

aliens=[]
herzen=[]
raketen = []

leben=100
anzahl_raketen = 10


def alien_erzeugen():
    alien=Actor("alien.png", pos=(600,random.randint(0,600)))
    aliens.append(alien)

def herz_erzeugen():
    herz=Actor("herz.png", pos=(600, random.randint(0,600)))
    herzen.append(herz)

def rakete_erzeugen():
    rakete = Actor("rakete.png", pos=(raumschiff.x + 30, raumschiff.y + 33))
    raketen.append(rakete)


def on_key_down(key):
    global anzahl_raketen

    if key == keys.SPACE:
        if anzahl_raketen > 0:
            rakete_erzeugen()
            anzahl_raketen = anzahl_raketen - 1



def update():
    global leben
    global anzahl_raketen

    if keyboard.up:
        if raumschiff.y<0:
            raumschiff.y=600
        else:
            raumschiff.y=raumschiff.y-6

    elif keyboard.down:
        if raumschiff.y>600:
            raumschiff.y=0
        else:
            raumschiff.y=raumschiff.y+6


    for alien in aliens:
        alien.x=alien.x-3

        if alien.x<0:
            aliens.remove(alien)

        if raumschiff.colliderect(alien):
            aliens.remove(alien)
            if leben !=0:
                leben=leben-10

        for rakete in raketen:
            if rakete.colliderect(alien):
                aliens.remove(alien)
                raketen.remove(rakete)


    for herz in herzen:
        herz.x=herz.x-5

        if herz.x<0:
            herzen.remove(herz)

        if raumschiff.colliderect(herz):
            herzen.remove(herz)
            leben+=20


    for rakete in raketen:
        rakete.x = rakete.x + 8
        if rakete.x > 600:
            raketen.remove(rakete)


def draw():
    screen.blit("hintergrund.gif",(0,0))

    raumschiff.draw()

    for alien in aliens:
        alien.draw()

    for herz in herzen:
        herz.draw()

    for rakete in raketen:
        rakete.draw()

    screen.draw.text('Leben ' + str(leben), (15,10), color=(255,255,255), fontname="pixels.ttf", fontsize=60)
    screen.draw.text("Raketen " + str(anzahl_raketen),(265, 10),color=(255, 255, 255),fontname="pixels.ttf",fontsize=60,)

clock.schedule_interval(alien_erzeugen,random.randint(0,3))
clock.schedule_interval(herz_erzeugen,random.randint(5,10))



go()
