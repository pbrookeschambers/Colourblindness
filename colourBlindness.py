import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import qoplots
from cycler import cycler

from matplotlib import rcParams

from opensimplex import OpenSimplex

qoplots.init()
scheme = qoplots.getScheme()

## -- Conversions

def rgbToHex(rgb):
    colString = "#"
    for d in rgb:
        colString += f"{int(round(d * 255)):02X}"
    return colString

def rgbToHSL(rgb):
    r, g, b = rgb
    if r > 1 or g > 1 or b > 1:
        r, g, b = r / 255, g / 255, b / 255
        rgb = [r, g, b]
    xmax = max(rgb)
    xmin = min(rgb)
    C = xmax - xmin
    l = (xmax + xmin) / 2
    if C == 0:
        h = 0
    elif xmax == r:
        h = 60 * (g - b) / C
    elif xmax == g:
        h = 60 * (2 + (b - r) / C)
    elif xmax == b:
        h = 60 * (4 + (r - g) / C)
    else:
        print(f"ERROR: Could not convert (r, g, b) = ({r}, {g}, {b}) to HSL")
    if l == 0 or l == 1:
        s = 0
    else:
        s = (xmax - l) / min(l, 1 - l)
    if h < 0:
        h += 360
    return (h / 360, s, l)


def hslToRGB(hsl):
    h, s, l = hsl
    C = (1 - abs(2 * l - 1)) * s
    hpr = h * 6
    X = C * (1 - abs(hpr % 2 - 1))
    m = l - C / 2
    if 0 <= hpr < 1:
        r, g, b = C, X, 0
    elif 1 <= hpr < 2:
        r, g, b = X, C, 0
    elif 2 <= hpr < 3:
        r, g, b = 0, C, X
    elif 3 <= hpr < 4:
        r, g, b = 0, X, C
    elif 4 <= hpr < 5:
        r, g, b = X, 0, C
    elif 5 <= hpr < 6:
        r, g, b = C, 0, X
    else:
        print(f"ERROR: Could not convert (h, s, l) = ({h}, {s}, {l}) to RGB. Hprime = {hpr}")
    r, g, b = r + m, g + m, b + m
    return (r, g, b)


def hexToRGB(col):
    r, g, b = [int(col[2 * i + 1 : 2 * i + 3], 16) / 255 for i in range(3)]
    return (r, g, b)


## -- Colour Shifting

class Colour():
    def __init__(self, r = None, g = None, b = None):
        if r == None:
            r = [0,0,0]
        if g == None and b == None:
            self.r, self.g, self.b = r
        else:
            self.r = r
            self.g = g
            self.b = b
        self.u, self.v = 0, 0
        self.x, self.y, self.z = rgbToXYZ([self.r, self.g, self.b])
    def getRGB(self):
        return (self.r, self.g, self.b)
    def getXYZ(self):
        return (self.x, self.y, self.z)
    def recalcRGB(self):
        self.r, self.g, self.b = xyzToRGB((self.x, self.y, self.z))
    def recalcXYZ(self):
        self.x, self.y, self.z = xyzToRGB((self.r, self.g, self.b))

def rgbToXYZ(rgb):
    r, g, b = rgb
    if (r > 1 or g > 1 or b > 1):
        r, g, b = r / 255, g / 255, b / 255
    x=(0.430574*r+0.341550*g+0.178325*b);
    y=(0.222015*r+0.706655*g+0.071330*b);
    z=(0.020183*r+0.129553*g+0.939180*b);
    return (x, y, z)

def xyzToRGB(xyz):
    x, y, z = xyz
    r=( 3.063218*x-1.393325*y-0.475802*z);
    g=(-0.969243*x+1.875966*y+0.041555*z);
    b=( 0.067871*x-0.228834*y+1.069251*z);
    return (r, g, b)


rBlind={'prot':{'cpu':0.735,'cpv':0.265,'am':1.273463,'ayi':-0.073894},
            'deut':{'cpu':1.14,'cpv':-0.14,'am':0.968437,'ayi':0.003331},
            'trit':{'cpu':0.171,'cpv':-0.003,'am':0.062921,'ayi':0.292119}};


def z(v, gamma):
    return 0 if v <= 0 else 1 if v >= 1 else v ** (1 / gamma)

def blindMk(rgb, t):
    gamma=2.2; wx=0.312713; wy=0.329016; wz=0.358271
    col = Colour(rgb)
    c = Colour(col.r ** gamma, col.g ** gamma, col.b ** gamma)

    sum_xyz = c.x + c.y + c.z
    u = 0
    v = 0
    if sum_xyz != 0:
        c.u = c.x / sum_xyz
        c.v = c.y / sum_xyz
    nx = wx * c.y / wy
    nz = wz * c.y / wy
    clm = 0
    s = Colour()
    d = Colour()
    d.y = 0
    if c.u < rBlind[t]['cpu']:
        clm = (rBlind[t]['cpv'] - c.v) / (rBlind[t]['cpu'] - c.u)
    else:
        clm = (c.v - rBlind[t]['cpv']) / (c.u - rBlind[t]['cpu'])

    clyi = c.v - c.u * clm
    d.u = (rBlind[t]['ayi'] - clyi) / (clm - rBlind[t]['am'])
    d.v = (clm * d.u) + clyi

    s.x = d.u * c.y / d.v
    s.y = c.y
    s.z = (1 - (d.u + d.v)) * c.y / d.v
    s.recalcRGB()

    d.x = nx - s.x
    d.z = nz - s.z
    d.recalcRGB()

    adjr = 0 if d.r == 0 else ((0 if s.r < 0 else 1) - s.r) / d.r
    adjg = 0 if d.g == 0 else ((0 if s.g < 0 else 1) - s.g) / d.g
    adjb = 0 if d.b == 0 else ((0 if s.b < 0 else 1) - s.b) / d.b

    adjust = max([ai if 0 <= ai <= 1 else 0 for ai in [adjr, adjg, adjb]])

    s.r = s.r + (adjust * d.r)
    s.g = s.g + (adjust * d.g)
    s.b = s.b + (adjust * d.b)

    return [z(s.r, gamma), z(s.g, gamma), z(s.b, gamma)]


def colourShift(rgb, t, p):
    if p >= 1:
        p = p / 100
    if not(t in rBlind):
        print(f"ERROR: Unrecognised type {t}")
        return
    newCol = blindMk(rgb, t)
    return [(1 - p) * c + p * newC for c, newC in zip(rgb, newCol)]

def shiftScheme(scheme, t, p):
    newScheme = []
    for col in scheme:
        if type(col) == str:
            col = hexToRGB(col)
        newScheme.append(colourShift(col, t, p))
    return newScheme

def themeToSVG(theme):
    outString  = """<svg>\n"""
    background = theme[1] if type(theme[1]) != str else hexToRGB(theme[1])
    outString += f"""<rect x = "0" y = "0" width = "250" height = "130" rx = "10" style = "fill: rgb({background[0] * 255:.0f}, {background[1] * 255:.0f}, {background[2] * 255:.0f})"/>\n"""
    for i, col in enumerate(theme[:-2]):
        if type(col) == str:
            col = hexToRGB(col)
        if i == 0:
            outline = col
        outString += f"""<rect x = "{60 * (i % 4) + 10:d}" y = "{(60 if i >= 4 else 0) + 10:d}"  width = "50" height = "50" rx = "10" style = "fill: rgb({col[0] * 255:.0f}, {col[1] * 255:.0f}, {col[2] * 255:.0f}); stroke-width: 2; stroke: rgb({outline[0] * 255:.0f}, {outline[1] * 255:.0f}, {outline[2] * 255:.0f})"/>\n"""
    outString += "</svg>"
    return outString


def updateRCParams(scheme):
    dark = False
    colScheme = {}
    names = ["ForegroundColour", "BackgroundColour", "Accent1", "Accent2", "Accent3", "Accent4", "Accent5", "Accent6", "Hyperlink", "FollowedHyperlink"]
    for col, name in zip(scheme, names):
        colScheme[name] = col if type(col) == str else rgbToHex(col)
    linewidths = {'presentation' : 1.4, 'report' : 0.8}
    markerSizes = {'presentation' : 4, 'report' : 6}
    formatting = {
        'text.color' : colScheme["ForegroundColour"],
        'axes.labelcolor' : colScheme["ForegroundColour"],
        'axes.edgecolor' : colScheme["ForegroundColour"],
        'xtick.color' : colScheme["ForegroundColour"],
        'ytick.color' : colScheme["ForegroundColour"],
        'axes.facecolor' : colScheme["BackgroundColour"],
        'figure.facecolor' : "white",
        'axes.facecolor' : colScheme["BackgroundColour"],
        'legend.edgecolor' : colScheme["ForegroundColour"],
        'legend.facecolor' : colScheme["BackgroundColour"],
        'axes.spines.top' : True,
        'axes.spines.right' : True,
        'axes.prop_cycle' : cycler(
            'color',
            [colScheme["Accent" + str(i)] for i in range(1, 7)] +
            [qoplots.lighten(
                colScheme["Accent" + str(i)],
                0.3
            ) for i in range(1, 7)]
        ) if not(dark) else cycler(
            'color',
            [colScheme["Accent" + str(i)] for i in range(1, 7)] +
            [qoplots.darken(
                colScheme["Accent" + str(i)],
                0.3
            ) for i in range(1, 7)]
        ),
        'axes.linewidth' : linewidths['report'],
        'xtick.major.width' : linewidths['report'],
        'ytick.major.width' : linewidths['report'],
        'lines.markersize' : markerSizes['report'],
        'figure.figsize' : (5, 3.5),
        'text.latex.preamble' : "\\usepackage{amsmath, amssymb}",
        'text.usetex' : True,
        'savefig.facecolor' : "white",
        'savefig.edgecolor' : 'none',
        'font.family' : 'serif'
    }
    for key, val in formatting.items():
        rcParams[key] = val

st.set_page_config(layout = "wide")

OSNoise = OpenSimplex()

themes = sorted([s[0].upper() + s[1:] for s in qoplots.getAvailableSchemes()])

schemeName = st.sidebar.selectbox("Colour Scheme", themes, index = themes.index("Twilight"))

severitySlider = st.sidebar.slider("Severity", min_value = 0, max_value = 100, value = 100, step = 1, format = "%d%%")

protCheck = st.sidebar.checkbox("Protanopia",   value = True, help = "Protanopia occurs when the red cones are absent. This is a form of red-green colour blindness.")
deutCheck = st.sidebar.checkbox("Deuteranopia", value = True, help = "Deuteranopia occurs when the green cones are absent. This is another form of red-green colour blindness.")
tritCheck = st.sidebar.checkbox("Tritanopia",   value = True, help = "Tritanopia occurs when the short wavelength cones are absent. This is a form of blue-yellow colour blindness.")
update    = st.sidebar.checkbox("Update",   value = True, help = "This is necessary for automatically updating the theme. Please leave checked.")


columns = st.columns(4)

columns[0].write("## Normal")
normalImage = columns[0].empty()

normalImage.image(themeToSVG(scheme))


x = np.linspace(0, 5, 200)
y = [[OSNoise.noise2d(x = x[i], y = j) for i in range(len(x))] for j in range(6)]

figDPI = 300

if update:
    qoplots.init(scheme = schemeName)
    scheme = qoplots.getScheme()
    normalImage.image(themeToSVG(scheme))
    fig = plt.figure(dpi = figDPI)
    for j in range(6):
        plt.plot(x, y[j], label = f"Accent{j+1}")
    plt.legend()
    plt.tick_params(
        axis       ='both',
        which      ='both',
        bottom     =False,
        top        =False,
        left       = False,
        right      = False,
        labelleft  = False,
        labelbottom=False)
    columns[0].pyplot(fig, dpi = figDPI)



if protCheck:
    protScheme = shiftScheme(scheme, 'prot', severitySlider)
    columns[1].write("## Protanopia")
    protImage = columns[1].image(themeToSVG(protScheme))
    updateRCParams(protScheme)
    fig = plt.figure(dpi = figDPI)
    for j in range(6):
        plt.plot(x, y[j], label = f"Accent{j+1}")
    plt.legend()
    plt.tick_params(
        axis       ='both',
        which      ='both',
        bottom     =False,
        top        =False,
        left       = False,
        right      = False,
        labelleft  = False,
        labelbottom=False)
    columns[1].pyplot(fig, dpi = figDPI)

if deutCheck:
    deutScheme = shiftScheme(scheme, 'deut', severitySlider)
    columns[2].write("## Deuteranopia")
    deutImage = columns[2].image(themeToSVG(deutScheme))
    updateRCParams(deutScheme)
    fig = plt.figure(dpi = figDPI)
    for j in range(6):
        plt.plot(x, y[j], label = f"Accent{j+1}")
    plt.legend()
    plt.tick_params(
        axis       ='both',
        which      ='both',
        bottom     =False,
        top        =False,
        left       = False,
        right      = False,
        labelleft  = False,
        labelbottom=False)
    columns[2].pyplot(fig, dpi = figDPI)

if tritCheck:
    tritScheme = shiftScheme(scheme, 'trit', severitySlider)
    columns[3].write("## Tritanopia")
    tritImage = columns[3].image(themeToSVG(tritScheme))
    updateRCParams(tritScheme)
    fig = plt.figure(dpi = figDPI)
    for j in range(6):
        plt.plot(x, y[j], label = f"Accent{j+1}")
    plt.legend()
    plt.tick_params(
        axis       ='both',
        which      ='both',
        bottom     =False,
        top        =False,
        left       = False,
        right      = False,
        labelleft  = False,
        labelbottom=False)
    columns[3].pyplot(fig, dpi = figDPI)
