#  Copyright (c) 2020. Mirza Coralic
#  All rights reserved.

# PyQt4 imports
import random

from PIL import Image, ImageOps, ImageDraw2
#from PIL.ImageDraw import ImageDraw

from PyQt4 import QtGui, QtCore, QtOpenGL
from PyQt4.QtCore import QTimer
from PyQt4.QtGui import QMessageBox
from PyQt4.QtOpenGL import QGLWidget

import logging; logging.basicConfig();
logging.root.setLevel(logging.DEBUG);

# PyOpenGL imports
import OpenGL.GL as gl
import OpenGL.GLU as glu
import OpenGL.arrays.vbo as glvbo
import math

from playsound import playsound


class GLPlotWidget(QGLWidget):
    # default window size
    width, height = 735, 855
    pos_x0 = -0.02
    pos_y0 = -0.74
    gpos_x0 = []
    gpos_y0 = []
    ang = 0.0
    mstate = 0
    nums = 10
    step = 1
    stepc = 0
    prevKey = QtCore.Qt.Key_Right
    virtKey = QtCore.Qt.Key_Right
    prevKeyGhost = []
    akeys = [QtCore.Qt.Key_Left, QtCore.Qt.Key_Right, QtCore.Qt.Key_Up, QtCore.Qt.Key_Down]
    ghost_last_move = [[0 for _ in range(6)] for _ in range(5)]
    score = 0
    lives = 3
    numg = 2
    follow_pcman = [False,False,False,False,False]
    follow_cnt = [0,0,0,0,0]
    sound_counter = 0
    tick_interval0 = 80
    tick_interval = 80
    isDead = False
    started = False
    walls_x = [-842, -702, -502, -302, -102, 98, 298, 498, 698, 838]
    walls_y = [-874, -674, -474, -274, -74, 126, 326, 526, 726, 986]

    wall_sample_ghost = [[],[],[],[],[]]

    def set_data(self, data):
        self.data = data
        self._pBits = self.makeRectImage()

    def read_texture(self, filename):
        img = Image.open(filename)
        img_data = np.array(list(img.getdata()), np.int32)
        textID = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, textID)
        gl.glPixelStorei(gl.GL_UNPACK_ALIGNMENT, 1)
        gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP)
        gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP)
        gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
        gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)
        gl.glTexEnvf(gl.GL_TEXTURE_ENV, gl.GL_TEXTURE_ENV_MODE, gl.GL_DECAL)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGB, img.size[0], img.size[1], 0, gl.GL_RGB, gl.GL_UNSIGNED_BYTE, img_data)
        return textID

    def initializeGL(self):
        # background color
        gl.glClearColor(0, 0, 0, 0)

        # setup textures (walls background without points/meat and with points/meat
        self.texture_0 = self.read_texture("Resources/pacman1.jpg")
        self.texture_1 = self.read_texture("Resources/pacman2.jpg")
        self.texture_ghost = []
        texId = self.read_texture("Resources/ghost_red.jpg")
        self.texture_ghost.append(texId)
        texId = self.read_texture("Resources/ghost_pink.jpg")
        self.texture_ghost.append(texId)
        texId = self.read_texture("Resources/ghost_green.jpg")
        self.texture_ghost.append(texId)
        texId = self.read_texture("Resources/ghost_orange.jpg")
        self.texture_ghost.append(texId)
        texId = self.read_texture("Resources/ghost_blue.jpg")
        self.texture_ghost.append(texId)

        self.gpos_x0 = [-1.02, 0.98, -1.2, 1.2, 0.0]
        self.gpos_y0 = [3.26, 3.26, 1.0, 1.0, 1.0]
        self.gpos_x = list(self.gpos_x0)
        self.gpos_y = list(self.gpos_y0)
        self.pos_x = self.pos_x0
        self.pos_y = self.pos_y0

        self.prevKeyGhost.append(QtCore.Qt.Key_Left)
        self.prevKeyGhost.append(QtCore.Qt.Key_Right)
        self.prevKeyGhost.append(QtCore.Qt.Key_Left)
        self.prevKeyGhost.append(QtCore.Qt.Key_Right)
        self.prevKeyGhost.append(QtCore.Qt.Key_Left)

        # create a Vertex Buffer Object with the specified data
        self.vbo = []
        for i in range(0, self.nums):
            self.vbo.append(glvbo.VBO(self.data[i]))

        self.drawScore()
        self.drawLives()
        self.drawTitle()

    def drawTitle(self):
        self.drawText(20, 10, "Pac-Man Python version by Mirza Coralic (c) 2020", 300, 12)

    def drawScore(self):
        self.drawText(170,self.height - 53,str(self.score),150,40)

    def drawLives(self):
        self.drawText(490, self.height - 53, str(self.lives), 30, 40)

    def drawBackground(self, textId):
        k = 855.0 / 735.0 # aspect ratio of widget window
        gl.glEnable(gl.GL_TEXTURE_2D)
        gl.glBindTexture(gl.GL_TEXTURE_2D, textId)
        gl.glBegin(gl.GL_QUADS)
        gl.glTexCoord2f(0, 1)
        gl.glVertex2f(-10.0,-10.0*k)
        gl.glTexCoord2f(1, 1)
        gl.glVertex2f(10.0,-10.0*k)
        gl.glTexCoord2f(1, 0)
        gl.glVertex2f(10.0,10.0*k)
        gl.glTexCoord2f(0, 0)
        gl.glVertex2f(-10.0,10.0*k)
        gl.glEnd()
        gl.glDisable(gl.GL_TEXTURE_2D)

    def drawGhost(self, idx):
        w = 41.0*10.0/735.0
        k = 855.0 / 735.0  # aspect ratio of widget window
        gl.glEnable(gl.GL_TEXTURE_2D)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture_ghost[idx])
        gl.glBegin(gl.GL_QUADS)
        gl.glTexCoord2f(0, 1)
        gl.glVertex2f(-w,-w)
        gl.glTexCoord2f(1, 1)
        gl.glVertex2f(w,-w)
        gl.glTexCoord2f(1, 0)
        gl.glVertex2f(w,w)
        gl.glTexCoord2f(0, 0)
        gl.glVertex2f(-w,w)
        gl.glEnd()
        gl.glDisable(gl.GL_TEXTURE_2D)

    def drawPacman(self):
        # bind the VBO
        self.vbo[self.mstate].bind()
        # tell OpenGL that the VBO contains an array of vertices
        gl.glEnableClientState(gl.GL_VERTEX_ARRAY)
        # these vertices contain 2 single precision coordinates
        gl.glVertexPointer(2, gl.GL_FLOAT, 0, self.vbo[self.mstate])
        # draw triangles of pacman from the VBO
        gl.glDrawArrays(gl.GL_TRIANGLE_FAN, 0, self.data[self.mstate].shape[0])

    def worldToScreen(self,x,y,flip):
        # project the point to screen
        point = glu.gluProject(x, y, 1.0, self.model_view, self.proj, self.view) # -0.75 -> pos_y0

        if flip:
          sx = round(point[0])
          sy = round(self.view[3] - point[1])
          return ([sx,sy])
        else:
          return ([point[0],point[1]])

    def readPixels(self, wh, idx):
        px = self.pos_x
        py = self.pos_y
        if idx>-1:
            px = self.gpos_x[idx]
            py = self.gpos_y[idx]

        x0, y0 = self.worldToScreen(px,py,False)
        w = wh
        h = wh
        gl.glReadBuffer(gl.GL_BACK)
        img = gl.glReadPixels(x0-w/2, y0-h/2, w, h, gl.GL_LUMINANCE, gl.GL_UNSIGNED_BYTE)
        im = Image.frombytes("L", (w, h), img) # (self.height*3 + 3) & -4, -1)
        im = ImageOps.flip(im)
        return im

    def checkLeftWall(self, preKey, sx, sy, wall_sample):
        if preKey == QtCore.Qt.Key_Left or preKey == QtCore.Qt.Key_Right:
            imL = wall_sample.crop([24, 30, 26, 70])
            imLb = np.fromstring(imL.tobytes(), np.uint8)
            thL = imLb.sum()/80
            #print('thL = ' + str(thL) + '   pos_x = ' + str(self.pos_x))
            return (thL<40 and sy in self.walls_y) # 50

        if preKey == QtCore.Qt.Key_Up or preKey == QtCore.Qt.Key_Down:
            imL2 = wall_sample.crop([0, 28, 30, 72])
            imL2b = np.fromstring(imL2.tobytes(), np.uint8)
            thL2 = imL2b.sum()/1320
            #print('thL2 = ' + str(thL2))
            return (thL2<16 and sy in self.walls_y) # 10

    def checkRightWall(self, preKey, sx, sy, wall_sample):
        if preKey == QtCore.Qt.Key_Left or preKey == QtCore.Qt.Key_Right:
            imR = wall_sample.crop([100-26, 30, 100-24, 70])
            imRb = np.fromstring(imR.tobytes(), np.uint8)
            thR = imRb.sum()/80
            #print('thR = ' + str(thR) + '   pos_x = ' + str(self.pos_x))
            return (thR<40 and sy in self.walls_y)

        if preKey == QtCore.Qt.Key_Up or preKey == QtCore.Qt.Key_Down:
            imR2 = wall_sample.crop([70, 28, 100, 72])
            imR2b = np.fromstring(imR2.tobytes(), np.uint8)
            thR2 = imR2b.sum()/1320
            #print('thR2 = ' + str(thR2))
            return (thR2<16 and sy in self.walls_y)

    def checkUpWall(self, preKey, sx, sy, wall_sample):
        if preKey == QtCore.Qt.Key_Up or preKey == QtCore.Qt.Key_Down:
            imU = wall_sample.crop([30, 24, 70, 26])
            imUb = np.fromstring(imU.tobytes(), np.uint8)
            thU = imUb.sum()/80
            #print('thU = ' + str(thU) + '   pos_y = ' + str(self.pos_y) + '    sy = ' + str(sy))
            return (thU<40 and sx in self.walls_x and sy<980) # pos_y<9.80 correction because upper wall not drawn correctly

        if preKey == QtCore.Qt.Key_Left or preKey == QtCore.Qt.Key_Right:
            imU2 = wall_sample.crop([28, 0, 72, 30])
            imU2b = np.fromstring(imU2.tobytes(), np.uint8)
            thU2 = imU2b.sum()/1320
            #print('thU2 = ' + str(thU2))
            return (thU2<16 and sx in self.walls_x)

    def checkDownWall(self, preKey, sx, sy, wall_sample):
        if preKey == QtCore.Qt.Key_Up or preKey == QtCore.Qt.Key_Down:
            imD = wall_sample.crop([30, 74, 70, 76])
            imDb = np.fromstring(imD.tobytes(), np.uint8)
            thD = imDb.sum()/80
            #print('thD = ' + str(thD))
            return (thD<40 and sx in self.walls_x)

        if preKey == QtCore.Qt.Key_Left or preKey == QtCore.Qt.Key_Right:
            imD2 = wall_sample.crop([28, 70, 72, 100])
            imD2b = np.fromstring(imD2.tobytes(), np.uint8)
            thD2 = imD2b.sum()/1320
            #print('thD2 = ' + str(thD2))
            return (thD2<16 and sx in self.walls_x)

    def checkMeat(self):
        imM = self.meat_sample
        imMb = np.fromstring(imM.tobytes(), np.uint8)
        thM = imMb.sum() / 100
        #print('thM = ' + str(thM))
        return (thM > 40)

    def moveLeft(self, idx, sx, sy, checkOnly):
        preKey = self.prevKey
        wall_sample = self.wall_sample
        if idx>-1:
            preKey = self.prevKeyGhost[idx]
            wall_sample = self.wall_sample_ghost[idx]

        ret = self.checkLeftWall(preKey,sx,sy,wall_sample)

        if ret and not checkOnly:
            if idx==-1:
                if self.pos_x < -9.6:
                    self.pos_x = 9.38
                else:
                    self.pos_x += - 0.2
                    self.ang = 180.0
                    self.prevKey = QtCore.Qt.Key_Left
            else:
                if self.gpos_x[idx] < -9.6:
                    self.gpos_x[idx] = 9.38
                else:
                    self.gpos_x[idx] += - 0.2
                    self.prevKeyGhost[idx] = QtCore.Qt.Key_Left

        return ret

    def moveRight(self, idx, sx, sy, checkOnly):
        preKey = self.prevKey
        wall_sample = self.wall_sample
        if idx>-1:
            preKey = self.prevKeyGhost[idx]
            wall_sample = self.wall_sample_ghost[idx]

        ret = self.checkRightWall(preKey,sx,sy,wall_sample)
        if ret and not checkOnly:
            if idx==-1:
                if self.pos_x > 9.5:
                    self.pos_x = -9.42
                else:
                  self.pos_x += 0.2
                  self.ang = 0.0
                  self.prevKey = QtCore.Qt.Key_Right
            else:
                if self.gpos_x[idx] > 9.5:
                    self.gpos_x[idx] = -9.42
                else:
                  self.gpos_x[idx] += 0.2
                  self.prevKeyGhost[idx] = QtCore.Qt.Key_Right

        return ret

    def moveUp(self, idx, sx, sy, checkOnly):
        preKey = self.prevKey
        wall_sample = self.wall_sample
        if idx>-1:
            preKey = self.prevKeyGhost[idx]
            wall_sample = self.wall_sample_ghost[idx]

        ret = self.checkUpWall(preKey,sx,sy,wall_sample)
        if ret and not checkOnly:
            if idx==-1:
                self.pos_y += 0.2
                self.ang = 90.0
                self.prevKey = QtCore.Qt.Key_Up
            else:
                self.gpos_y[idx] += 0.2
                self.prevKeyGhost[idx] = QtCore.Qt.Key_Up

        return ret

    def moveDown(self, idx, sx, sy, checkOnly):
        preKey = self.prevKey
        wall_sample = self.wall_sample
        if idx>-1:
            preKey = self.prevKeyGhost[idx]
            wall_sample = self.wall_sample_ghost[idx]

        ret = self.checkDownWall(preKey,sx,sy,wall_sample)
        if ret and not checkOnly:
            if idx==-1:
                self.pos_y += - 0.2
                self.ang = -90.0
                self.prevKey = QtCore.Qt.Key_Down
            else:
                self.gpos_y[idx] += - 0.2
                self.prevKeyGhost[idx] = QtCore.Qt.Key_Down

        return ret

    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key_Q:
            reply = QMessageBox.question(
                self, "Message",
                "Are you sure you want to quit?",
                QMessageBox.Close | QMessageBox.Cancel)

            if reply == QMessageBox.Close:
                sys.exit()

        elif e.key() == QtCore.Qt.Key_X:
            #sx, sy = self.worldToScreen(self.pos_x, self.pos_y,True)
            sx = 100.0*self.pos_x
            self.walls_x.append(int(round(sx)))
        elif e.key() == QtCore.Qt.Key_Y:
            #sx, sy = self.worldToScreen(self.pos_x, self.pos_y, True)
            sy = 100.0 *self.pos_y
            self.walls_y.append(int(round(sy)))
        elif e.key() == QtCore.Qt.Key_P:
            print('X: ' + str(self.walls_x))
            print('Y: ' + str(self.walls_y))

        ret = self.checkMovement(e.key(), -1, True) # idx = -1 for pacman, idx>=0 ghosts
        if ret:
            self.virtKey = e.key()
            self.pressedKeyRetry = e.key()
        else:
            self.pressedKeyRetry = e.key()

        self.pressedKey = e.key()

        if not self.started:
            self.timer = QTimer()
            self.timer.timeout.connect(self.tick)
            self.timer.start(self.tick_interval) #80 normal speed
            self.started = True

    def checkMovement(self, ekey, idx, checkOnly):
        sx = 0
        sy = 0
        if idx<0:
            sx = int(round(100.0*self.pos_x))
            sy = int(round(100.0*self.pos_y))
        else:
            sx = int(round(100.0*self.gpos_x[idx]))
            sy = int(round(100.0*self.gpos_y[idx]))
        ret = False
        if ekey == QtCore.Qt.Key_Left:
            ret = self.moveLeft(idx, sx, sy, checkOnly)
        elif ekey == QtCore.Qt.Key_Right:
            ret = self.moveRight(idx, sx, sy, checkOnly)
        elif ekey == QtCore.Qt.Key_Up:
            ret = self.moveUp(idx, sx, sy, checkOnly)
        elif ekey == QtCore.Qt.Key_Down:
            ret = self.moveDown(idx, sx, sy, checkOnly)

        return ret

    def tick(self):
        ret = False

        if not self.isDead:
            kRet = self.pressedKeyRetry
            kVirt = self.virtKey

            if kRet != kVirt:
              ret = self.checkMovement(kRet, -1, True)
              if ret:
                  kVirt = kRet
                  self.virtKey = kVirt

            ret = self.checkMovement(kVirt, -1, False)

            if ret:
                if self.sound_counter == 0 or self.sound_counter > int(480.0/self.tick_interval):
                  playsound('Resources/wakka.wav',False)
                  self.sound_counter = 0
                self.sound_counter += 1
            else:
                self.sound_counter = 0

        # state machine for pacman render (self.nums number of states)
        if self.isDead:
            if self.mstate < self.nums-1:
                self.mstate += 1
            else:
                self.mstate=0
                self.step = 1
                self.stepc = 0
                self.isDead = False
                self.started = False
                self.timer.stop()

                if self.lives == 0:
                    reply = QMessageBox.question(
                        self, "Message",
                        "GAME OVER!!! Want to play again?",
                        QMessageBox.Yes | QMessageBox.No)

                    if reply == QMessageBox.No:
                        sys.exit()
                    self.resetGame()
                else:
                    self.pos_x = self.pos_x0
                    self.pos_y = self.pos_y0


        else:
            if self.mstate > -1 and self.mstate < 4 : # 4 states
              self.mstate += self.step
            if self.stepc < 4-2:
              self.stepc += 1
            else:
              self.stepc = 0
              self.step = - self.step

        self.moveGhosts()

        self.updateGL()

        eaten = self.checkMeat()

        if eaten:
            # add to score and update/show score text
            self.score += 1
            self.eraseRectOnImage()
            self.drawScore()

            if self.score>299:
                self.mstate=0
                self.step = 1
                self.stepc = 0
                self.isDead = False
                self.started = False
                self.timer.stop()

                reply = QMessageBox.question(
                    self, "Message",
                    "YOU WIN THE GAME. Want to play again?",
                    QMessageBox.Yes | QMessageBox.No)

                if reply == QMessageBox.No:
                    sys.exit()
                self.resetGame()

        if not self.isDead:
            self.checkDie()

        if self.score == 40:
            self.gpos_x[2] = self.gpos_x0[0]
            self.gpos_x[3] = self.gpos_x0[1]
            self.gpos_y[2] = self.gpos_y0[0]
            self.gpos_y[3] = self.gpos_y0[1]
            self.numg = 4
            self.updateGL()
        elif self.score == 80:
            self.gpos_x[4] = self.gpos_x0[0]
            self.gpos_y[4] = self.gpos_y0[0]
            self.numg = 5
            self.updateGL()
        elif self.score == 200:
            self.tick_interval = int(2.0/3.0*self.tick_interval0)
            self.timer.setInterval(self.tick_interval)
        elif self.score == 250:
            self.tick_interval = self.tick_interval0
            self.timer.setInterval(self.tick_interval)

        '''testing
        if 1:
            #sx, sy = self.worldToScreen(self.pos_x, self.pos_y, True)
            sx = int(round(100.0*self.pos_x))
            sy = int(round(100.0*self.pos_y))
            pos = '{:3d}'.format(sx) + ',' + '{:1.3f}'.format(sx)
            self.drawText(480, self.height - 53,pos , 250, 40)
            #bottom -8.74, -8.54 up
        '''

    def moveGhosts(self):
        for i in range(0,self.numg):
            ekey = self.prevKeyGhost[i] #==QtCore.Qt.Key_Left
            ret = self.checkMovement(ekey,i,True)

            rn = random.randint(0,2)
            crossroad = ((int(round(100.*self.gpos_x[i])) in self.walls_x) and (int(round(100.*self.gpos_y[i])) in self.walls_y)) and (rn == 1)

            rem_key = ekey
            rem_key2 = ekey

            rn = random.randint(0,1)
            rn2 = random.randint(0,2)

            if rn==1:
                if self.pos_x > self.gpos_x[i]:
                    rem_key = QtCore.Qt.Key_Left
                else:
                    rem_key = QtCore.Qt.Key_Right
            else:
                if self.pos_y < self.gpos_y[i]:
                    rem_key = QtCore.Qt.Key_Up
                else:
                    rem_key = QtCore.Qt.Key_Down

            if ekey == QtCore.Qt.Key_Left:
                rem_key2 = QtCore.Qt.Key_Right
            elif ekey == QtCore.Qt.Key_Right:
                rem_key2 = QtCore.Qt.Key_Left
            if ekey == QtCore.Qt.Key_Up:
                rem_key2 = QtCore.Qt.Key_Down
            if ekey == QtCore.Qt.Key_Down:
                rem_key2 = QtCore.Qt.Key_Up

            if i==0:
                '''
                if self.follow_pcman[0]:
                    print('Following: ON')
                    print('.')
                else:
                    print('Following: OFF')
                    print('.')
                '''

                rn3 = random.randint(0,50)
                if rn3==1 and not self.follow_pcman[i]:
                    self.follow_pcman[i] = True
                    #print('--- Following turned on. ---')

                if self.follow_pcman[i]:
                    if self.follow_cnt[i] > 300:
                      self.follow_pcman[i] = False
                      self.follow_cnt[i] = 0
                      #print('--- Following turned off. Timed out. ---')

                    move_hist = [_ - 16777234 for _ in self.ghost_last_move[i]]
                    if move_hist == [1, 2, 0, 3, 1, 2]:  # stuck pos in foolowing mode
                        self.follow_pcman[i] = False
                        self.ghost_last_move[i] = [0 for _ in range(6)]
                        #print('--- Following off. Stucked. ---')
                    # print(move_hist)

                if self.follow_pcman[i]:
                    self.follow_cnt[i] += 1
                    glkey = self.ghost_last_move[i][-1]
                    gremov = QtCore.Qt.Key_Left
                    if glkey == QtCore.Qt.Key_Left:
                        gremov = QtCore.Qt.Key_Right
                    elif glkey == QtCore.Qt.Key_Right:
                        gremov = QtCore.Qt.Key_Left
                    if glkey == QtCore.Qt.Key_Up:
                        gremov = QtCore.Qt.Key_Down
                    elif glkey == QtCore.Qt.Key_Down:
                        gremov = QtCore.Qt.Key_Up

                    gdist_x = math.fabs(self.gpos_x[i] - self.pos_x)
                    gdist_y = math.fabs(self.gpos_y[i] - self.pos_y)

                    gadd = [0,0]
                    gadd_x = 0
                    gadd_y = 0
                    if self.gpos_x[i] < self.pos_x:
                        gadd_x = QtCore.Qt.Key_Right
                    else:
                        gadd_x = QtCore.Qt.Key_Left
                    if self.gpos_y[i] > self.pos_y:
                        gadd_y = QtCore.Qt.Key_Down
                    else:
                        gadd_y = QtCore.Qt.Key_Up

                    if gdist_x < gdist_y:
                        gadd = [gadd_y, gadd_x]
                    else:
                        gadd = [gadd_x, gadd_y]

                    gkeys = gadd + self.akeys
                    if self.follow_cnt[i]>1:
                        gkeys.remove(gremov)
                    ret2 = False
                    for m in range(0,5):
                      ret2 = self.checkMovement(gkeys[m],i,True)
                      if ret2:
                          self.checkMovement(gkeys[m], i, False)
                          self.ghost_last_move[i].append(gkeys[m])
                          self.ghost_last_move[i].pop(0)
                          break

            if self.follow_pcman[i]:
                continue

            if (not ret) or crossroad:
                tkeys = list(self.akeys)
                tkeys.remove(ekey)
                if (rem_key in tkeys) and rn2==1:
                    tkeys.remove(rem_key)
                elif (rem_key2 in tkeys):
                    tkeys.remove(rem_key2)
                rn = random.randint(0,len(tkeys)-1)
                ekey2 = tkeys[rn]
                self.checkMovement(ekey2, i, False)
            else:
                self.checkMovement(ekey, i, False)

    def checkDie(self):
        for i in range(0,self.numg):
            if math.fabs(self.pos_x-self.gpos_x[i]) < 1.0 and math.fabs(self.pos_y-self.gpos_y[i]) < 1.0:
                playsound('Resources/die.wav',False)
                self.isDead = True
                self.mstate = 0
                self.lives -= 1
                self.drawLives()

    def resetGame(self):
        self.started = False
        self.isDead = False
        self.numg = 2
        self.lives = 3
        self.score = 0
        self.tick_interval = self.tick_interval0
        self.pos_x = self.pos_x0
        self.pos_y = self.pos_y0
        self.gpos_x = list(self.gpos_x0)
        self.gpos_y = list(self.gpos_y0)
        self.texture_1 = self.read_texture("Resources/pacman2.jpg")
        self.updateGL()
        self.drawLives()
        self.drawScore()


    def drawText(self, off_x, off_y, text, w, h):
        font = ImageDraw2.Font("yellow","Resources/monkey.otf",h)
        img = Image.new("RGB", (w, h), (0,0,0))
        draw = ImageDraw2.Draw(img)
        draw.text((0, -3*h/10), text, font) # -12
        #img_flip = img.transpose(Image.FLIP_TOP_BOTTOM)
        #img.show()

        self.text_pBits = img.tobytes("raw", "RGB")

        gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture_1);
        gl.glTexSubImage2D(gl.GL_TEXTURE_2D, 0, off_x, off_y, w, h, gl.GL_RGB, gl.GL_UNSIGNED_BYTE, self.text_pBits);
        gl.glBindTexture(gl.GL_TEXTURE_2D, 0);

    def makeRectImage(self):
        img = Image.new("RGB", (34, 34), (0,0,0))
        img_flip = img.transpose(Image.FLIP_TOP_BOTTOM)
        pBits = img_flip.tobytes("raw", "RGB")
        self._pBits = pBits
        return self._pBits

    def eraseRectOnImage(self):
        off_x, off_y = self.worldToScreen(self.pos_x, self.pos_y,True)
        if off_x+17 > self.width or off_x-17<0:
            return

        gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture_1);
        gl.glTexSubImage2D(gl.GL_TEXTURE_2D, 0, off_x-17, off_y-17, 34,34, gl.GL_RGB, gl.GL_UNSIGNED_BYTE, self._pBits);
        gl.glBindTexture(gl.GL_TEXTURE_2D, 0);


    def paintGL(self):
        # clear the buffer
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

        self.drawBackground(self.texture_0)
        self.wall_sample = self.readPixels(100, -1)

        for i in range(0,self.numg):
          self.wall_sample_ghost[i] = self.readPixels(100, i)

        self.drawBackground(self.texture_1)
        self.meat_sample = self.readPixels(10, -1)

        for i in range(0,5):
            gl.glPushMatrix()
            gl.glTranslatef(self.gpos_x[i], self.gpos_y[i],0)
            self.drawGhost(i)
            gl.glPopMatrix()

        # set yellow color of pacman
        gl.glColor(1,1,0)

        gl.glPushMatrix()
        gl.glTranslatef(self.pos_x,self.pos_y,0)
        if self.isDead:
            gl.glRotated(90, 0, 0, 1)
        else:
            gl.glRotated(self.ang,0,0,1)
        self.drawPacman()
        gl.glPopMatrix()

    def resizeGL(self, width, height):
        # update the window size
        self.width, self.height = width, height
        # paint within the whole window
        gl.glViewport(0, 0, width, height)
        # set orthographic projection (2D only)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        # the window corner OpenGL coordinates are (-+1, -+1)
        k = 855.0/735.0
        gl.glOrtho(-10, 10, -10*k, 10*k, -1, 1)

        # get projection matrix, view matrix and the viewport rectangle
        self.model_view = np.array(gl.glGetDoublev(gl.GL_MODELVIEW_MATRIX))
        self.proj = np.array(gl.glGetDoublev(gl.GL_PROJECTION_MATRIX))
        self.view = np.array(gl.glGetIntegerv(gl.GL_VIEWPORT))


if __name__ == '__main__':
    # import numpy for generating random data points
    import sys
    import numpy as np
    import numpy.random as rdn

    # define a Qt window with an OpenGL widget inside it
    class TestWindow(QtGui.QMainWindow):
        def __init__(self):
            super(TestWindow, self).__init__()

            # initialize the GL widget
            self.widget = GLPlotWidget()

            R = 0.5 # pacman radius
            coordsArr = []

            n = self.widget.nums

            cres = 15.0

            for k in range(n,0,-1):
                coords_pacman = [[0.0, 0.0]]
                k0 = 360.0/(cres*math.pow(n,0.85)) # pow(n,0.3)
                a0 = (360.0-cres*math.pow(k,0.85)*k0)/2.0
                a1 = a0 + cres*math.pow(k,0.85)*k0
                for i in range(0,int(cres)+1):
                  a = (i*math.pow(k,0.85)*k0+a0)/180.0*math.pi
                  coords_pacman.append([math.cos(a)*R,math.sin(a)*R])
                coordsArr.append(coords_pacman)

            self.data = np.array(coordsArr,dtype=np.float32)

            self.widget.set_data(self.data)
            # put the window at the screen position (100, 100)
            self.setGeometry(100, 100, self.widget.width, self.widget.height)
            self.setCentralWidget(self.widget)
            self.widget.setFocusPolicy(QtCore.Qt.StrongFocus)
            self.show()
            print('starting...')
            
    # create the Qt App and window
    app = QtGui.QApplication(sys.argv)
    window = TestWindow()
    window.show()
    app.exec_()
