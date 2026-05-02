#Night City Traffic Simulation

from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math, random

# ─── Window ───────────────────────────────────────────
W, H = 800, 500

# ─── State ────────────────────────────────────────────
cars = [
    {"x": 100, "base_speed": 2.0, "speed": 2.0, "color": (0.8, 0.2, 0.2), "scale": 1.0,  "lane": 0},
    {"x": 400, "base_speed": 1.5, "speed": 1.5, "color": (0.2, 0.4, 0.9), "scale": 0.85, "lane": 0},
    {"x": 600, "base_speed": 2.5, "speed": 2.5, "color": (0.2, 0.7, 0.3), "scale": 0.75, "lane": 1},
]

LIGHT_X    = 520
STOP_DIST  = 55   

traffic_light = {"state": 0, "timer": 0}   # 0=red 1=yellow 2=green
light_colors  = [(1,0,0), (1,0.8,0), (0,0.9,0)]
angle         = 0.0

# ─── Bresenham Line ────────────────────────────────────
def bresenham_line(x0, y0, x1, y1):
    pts = []
    dx, dy = abs(x1-x0), abs(y1-y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy
    while True:
        pts.append((x0, y0))
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 > -dy: err -= dy; x0 += sx
        if e2 <  dx: err += dx; y0 += sy
    return pts

def draw_bresenham_line(x0, y0, x1, y1):
    glBegin(GL_POINTS)
    for p in bresenham_line(x0, y0, x1, y1):
        glVertex2f(*p)
    glEnd()

# ─── Bresenham Circle ──────────────────────────────────
def bresenham_circle(cx, cy, r):
    pts = []
    x, y, d = 0, r, 1 - r
    def add8(x, y):
        for px, py in [(cx+x,cy+y),(cx-x,cy+y),(cx+x,cy-y),(cx-x,cy-y),
                       (cx+y,cy+x),(cx-y,cy+x),(cx+y,cy-x),(cx-y,cy-x)]:
            pts.append((px, py))
    while x <= y:
        add8(x, y)
        if d < 0: d += 2*x + 3
        else:     d += 2*(x-y) + 5; y -= 1
        x += 1
    return pts

def draw_bresenham_circle(cx, cy, r):
    glBegin(GL_POINTS)
    for p in bresenham_circle(cx, cy, r):
        glVertex2f(*p)
    glEnd()

def fill_circle(cx, cy, r, seg=40):
    glBegin(GL_TRIANGLE_FAN)
    glVertex2f(cx, cy)
    for i in range(seg+1):
        a = 2*math.pi*i/seg
        glVertex2f(cx + r*math.cos(a), cy + r*math.sin(a))
    glEnd()

# ─── Blending glow ────────────────────────────────────
def draw_glow(cx, cy, r, color, alpha=0.15):
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE)
    glColor4f(*color, alpha)
    fill_circle(cx, cy, r)
    glDisable(GL_BLEND)

# ─── Buildings ────────────────────────────────────────
building_data = [
    (30,  220, 55, 160),
    (95,  240, 50, 140),
    (155, 200, 60, 180),
    (230, 215, 55, 165),
    (300, 195, 65, 185),
    (380, 210, 55, 170),
    (450, 200, 60, 180),
    (525, 220, 50, 160),
    (590, 205, 65, 175),
    (670, 215, 60, 165),
]

win_data = [(6, 15, 0), (6, 30, 0), (6, 45, 0),
            (20,15, 0), (20,30, 0), (20,45, 0)]

def draw_buildings():
    for i, (bx, by, bw, bh) in enumerate(building_data):
    
        depth = 0.3 + 0.25 * (i % 3)
        br = depth * 0.15
        bg = depth * 0.15
        bb = depth * 0.35

        
        fog_c = 0.10 + FOG_ALPHA * 0.55   # fog color mix factor
        br = br * (1 - fog_c) + 0.08 * fog_c
        bg = bg * (1 - fog_c) + 0.09 * fog_c
        bb = bb * (1 - fog_c) + 0.22 * fog_c

        glColor3f(br, bg, bb)
        glBegin(GL_QUADS)
        glVertex2f(bx,    by)
        glVertex2f(bx+bw, by)
        glVertex2f(bx+bw, by+bh)
        glVertex2f(bx,    by+bh)
        glEnd()
       
        win_alpha = max(0.1, 0.85 - FOG_ALPHA * 0.7)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        for wx, wy, _ in win_data:
            if random.random() > 0.3:
                r2 = random.Random(bx*wx + wy)
                wc = [(1,0.9,0.6),(0.6,0.8,1),(1,0.7,0.4)][r2.randint(0,2)]
                glColor4f(*wc, win_alpha)
                glBegin(GL_QUADS)
                glVertex2f(bx+wx,    by+wy)
                glVertex2f(bx+wx+7,  by+wy)
                glVertex2f(bx+wx+7,  by+wy+5)
                glVertex2f(bx+wx,    by+wy+5)
                glEnd()
        glDisable(GL_BLEND)

# ─── Road ─────────────────────────────────────────────
def draw_road():
    # asphalt
    glColor3f(0.08, 0.08, 0.14)
    glBegin(GL_QUADS)
    glVertex2f(0,0); glVertex2f(W,0); glVertex2f(W,195); glVertex2f(0,195)
    glEnd()

    # edge lines (Bresenham)
    glColor3f(0.6, 0.6, 0.7)
    draw_bresenham_line(0, 195, W, 195)
    draw_bresenham_line(0,   2, W,   2)

    # center dashed line (Bresenham)
    glColor3f(0.9, 0.85, 0.1)
    x = 0
    while x < W:
        draw_bresenham_line(x, 100, min(x+30, W), 100)
        x += 55

    # lane divider
    glColor3f(0.3, 0.3, 0.5)
    draw_bresenham_line(0, 155, W, 155)

# ─── Street lamp ──────────────────────────────────────
lamp_positions = [120, 300, 480, 660]

def draw_lamps():
    for lx in lamp_positions:
        # pole (GL_LINES)
        glColor3f(0.35, 0.35, 0.55)
        glLineWidth(3)
        glBegin(GL_LINES)
        glVertex2f(lx, 195); glVertex2f(lx, 255)
        glVertex2f(lx, 255); glVertex2f(lx+18, 255)
        glEnd()
        glLineWidth(1)
        # lamp head (filled circle)
        glColor3f(1.0, 1.0, 0.7)
        fill_circle(lx+18, 255, 6)
        # glow (blending)
        draw_glow(lx+18, 240, 50, (1.0, 0.95, 0.5), 0.10)
        draw_glow(lx+18, 220, 70, (1.0, 0.95, 0.5), 0.05)

# ─── Traffic light ────────────────────────────────────
def draw_traffic_light():
    tx, ty = 520, 200
    # box
    glColor3f(0.1, 0.1, 0.2)
    glBegin(GL_QUADS)
    glVertex2f(tx-10, ty); glVertex2f(tx+10, ty)
    glVertex2f(tx+10, ty+50); glVertex2f(tx-10, ty+50)
    glEnd()
    # pole
    glColor3f(0.3, 0.3, 0.4)
    glLineWidth(2)
    glBegin(GL_LINES)
    glVertex2f(tx, ty); glVertex2f(tx, 195)
    glEnd()
    glLineWidth(1)

    offsets = [42, 28, 14]
    for i, off in enumerate(offsets):
        active = (i == traffic_light["state"])
        c = light_colors[i] if active else (0.1, 0.1, 0.1)
        glColor3f(*c)
        fill_circle(tx, ty+off, 7)
        # Bresenham circle outline
        glColor3f(0.6, 0.6, 0.6)
        draw_bresenham_circle(int(tx), int(ty+off), 7)
        if active:
            draw_glow(tx, ty+off, 20, c, 0.18)

# ─── Car (triangles + 2D transformation) ──────────────
def draw_car(cx, cy, sc, color):
    glPushMatrix()
    # Translation + Scaling (2D transformation)
    glTranslatef(cx, cy, 0)
    glScalef(sc, sc, 1)

    r, g, b = color
    # body (GL_QUADS built from triangles)
    glColor3f(r, g, b)
    glBegin(GL_TRIANGLES)
    glVertex2f(-30,-10); glVertex2f(30,-10); glVertex2f(30, 8)
    glVertex2f(-30,-10); glVertex2f(30,  8); glVertex2f(-30, 8)
    glEnd()
    # roof (triangle shape)
    glColor3f(r*0.8, g*0.8, b*0.8)
    glBegin(GL_TRIANGLES)
    glVertex2f(-15, 8); glVertex2f(15, 8); glVertex2f(10, 22)
    glVertex2f(-15, 8); glVertex2f(10,22); glVertex2f(-12,22)
    glEnd()
    # wheels (Bresenham circle + fill)
    glColor3f(0.15, 0.15, 0.15)
    fill_circle(-17, -10, 8)
    fill_circle( 17, -10, 8)
    glColor3f(0.4, 0.4, 0.4)
    draw_bresenham_circle(-17, -10, 8)
    draw_bresenham_circle( 17, -10, 8)
    # headlight beam (blending)
    draw_glow(32, 2, 18, (1, 1, 0.8), 0.12)
    glPopMatrix()

# ─── Moon ─────────────────────────────────────────────
def draw_moon():
    glColor3f(0.90, 0.90, 0.75)
    fill_circle(680, 440, 25)
    glColor3f(0.04, 0.04, 0.12)   # bite out
    fill_circle(690, 445, 22)

# ─── Stars ────────────────────────────────────────────
star_positions = [(50,450),(130,430),(200,460),(290,440),
                  (370,455),(460,435),(550,450),(630,460),
                  (100,420),(400,415),(600,425),(750,440)]

def draw_stars():
    glPointSize(2)
    glColor3f(0.9, 0.9, 1.0)
    glBegin(GL_POINTS)
    for sx, sy in star_positions:
        glVertex2f(sx, sy)
    glEnd()
    glPointSize(1)

FOG_ALPHA = 0.0  
def draw_fog_overlay():
    
    if FOG_ALPHA <= 0:
        return
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glBegin(GL_QUADS)
    glColor4f(0.10, 0.12, 0.28, FOG_ALPHA * 0.4)  
    glVertex2f(0, H);  glVertex2f(W, H)
    glColor4f(0.12, 0.15, 0.35, FOG_ALPHA * 0.85) 
    glVertex2f(W, 0);  glVertex2f(0, 0)
    glEnd()
    glDisable(GL_BLEND)

def draw_fog_strips():
    
    if FOG_ALPHA <= 0:
        return
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    strips = [
        (0,   160, W, 175, FOG_ALPHA * 0.30),
        (0,   130, W, 148, FOG_ALPHA * 0.22),
        (100, 105, 500, 118, FOG_ALPHA * 0.18),
    ]
    for x0, y0, x1, y1, a in strips:
        glColor4f(0.15, 0.18, 0.40, a)
        glBegin(GL_QUADS)
        glVertex2f(x0, y0); glVertex2f(x1, y0)
        glVertex2f(x1, y1); glVertex2f(x0, y1)
        glEnd()
    glDisable(GL_BLEND)

# ─── Display ──────────────────────────────────────────
def display():
    glClear(GL_COLOR_BUFFER_BIT)
    glLoadIdentity()

    # sky
    glColor3f(0.03, 0.03, 0.10)
    glBegin(GL_QUADS)
    glVertex2f(0,0); glVertex2f(W,0); glVertex2f(W,H); glVertex2f(0,H)
    glEnd()

    draw_stars()
    draw_moon()
    draw_buildings()
    draw_road()
    draw_lamps()
    draw_traffic_light()

    for car in cars:
        lane_y = 145 if car["lane"] == 0 else 110
        draw_car(car["x"], lane_y, car["scale"], car["color"])

    
    draw_fog_strips()
    draw_fog_overlay()

    # HUD
    glColor3f(0.6, 0.6, 0.9)
    glRasterPos2f(10, 15)
    fog_pct = int(FOG_ALPHA * 100)
    label = f"F: fog +  |  G: fog -  |  fog: {fog_pct}%  |  ESC: quit"
    for ch in label:
        glutBitmapCharacter(GLUT_BITMAP_8_BY_13, ord(ch))

    glutSwapBuffers()

# ─── Timer: animate cars + traffic light ──────────────
def timer(v):
    global angle

    
    # state duration: red=180f, yellow=60f, green=150f
    durations = [180, 60, 150]
    traffic_light["timer"] += 1
    if traffic_light["timer"] >= durations[traffic_light["state"]]:
        traffic_light["timer"] = 0
        traffic_light["state"] = (traffic_light["state"] + 1) % 3

    is_red    = traffic_light["state"] == 0
    is_yellow = traffic_light["state"] == 1

    
    for car in cars:
        stop_line = LIGHT_X - STOP_DIST

        if (is_red or is_yellow) and car["x"] < LIGHT_X and car["x"] >= stop_line - 5:
            
            dist = stop_line - car["x"]
            if dist <= 0:
                car["speed"] = 0
            else:
                car["speed"] = min(car["base_speed"], dist * 0.15)
        else:
            
            car["speed"] = car["base_speed"]

        car["x"] += car["speed"]

        
        if car["x"] > W + 60:
            car["x"] = -60
            car["scale"] = round(random.uniform(0.75, 1.0), 2)
            

    angle += 0.5
    glutPostRedisplay()
    glutTimerFunc(16, timer, 0)

# ─── Keyboard ─────────────────────────────────────────
def keyboard(key, x, y):
    global FOG_ALPHA
    if key == b'\x1b':
        glutDestroyWindow(glutGetWindow())
    elif key == b'f' or key == b'F':
        FOG_ALPHA = min(1.0, round(FOG_ALPHA + 0.15, 2))  
        glutPostRedisplay()
    elif key == b'g' or key == b'G':
        FOG_ALPHA = max(0.0, round(FOG_ALPHA - 0.15, 2))  
        glutPostRedisplay()

# ─── Init ─────────────────────────────────────────────
def init():
    glClearColor(0.03, 0.03, 0.10, 1)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(0, W, 0, H)
    glMatrixMode(GL_MODELVIEW)
    glEnable(GL_POINT_SMOOTH)
    glEnable(GL_LINE_SMOOTH)
    glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)

def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)
    glutInitWindowSize(W, H)
    glutInitWindowPosition(100, 100)
    glutCreateWindow(b"Night City Traffic - OpenGL")
    init()
    glutDisplayFunc(display)
    glutKeyboardFunc(keyboard)
    glutTimerFunc(16, timer, 0)
    print("Controls: F = fog  | G = fog  | ESC = quit")
    glutMainLoop()

if __name__ == "__main__":
    main()