import json
from matplotlib import rcParams
from cycler import cycler
import os
from typing import NamedTuple

def hslToRGB(col):
    import numpy as np
    h, s, l = col
    C = (1 - abs(2 * l - 1)) * s
    Hpr = h / 60
    X = C * (1 - abs(Hpr % 2 - 1))
    m = l - C / 2
    if Hpr < 1:
        return np.array([C + m, X + m, 0 + m])
    elif Hpr < 2:
        return np.array([X + m, C + m, 0 + m])
    elif Hpr < 3:
        return np.array([0 + m, C + m, X + m])
    elif Hpr < 4:
        return np.array([0 + m, X + m, C + m])
    elif Hpr < 5:
        return np.array([X + m, 0 + m, C + m])
    elif Hpr < 6:
        return np.array([C + m, 0 + m, X + m])
    else:
        return np.array([m    , m    , m    ])

def rgbToHSL(colString):
    import numpy as np
    if type(colString) == type(""):
        colString = colString.replace("#", "")
        colArray = np.array([int(colString[0:2], 16), int(colString[2:4], 16), int(colString[4:6], 16)], dtype = "float") / 255
    else:
        try:
            colArray = np.array(colString, dtype = "float")
            if np.max(colArray) > 1:
                colArray = colArray / 255
        except:
            raise TypeError(f"Could not convert colour to array. Type {type(colString)}")
    v = np.max(colArray)
    xmin = np.min(colArray)
    C = v - xmin
    l = (v + xmin) / 2
    if l == 0 or l == 1:
        s = 0
    else:
        s = (2 * (v - l))/(1 - abs(2 * l - 1))
    if C == 0:
        h = 0
    elif v == colArray[0]:
        h = 60 * (0 + (colArray[1] - colArray[2]) / C)
    elif v == colArray[1]:
        h = 60 * (2 + (colArray[2] - colArray[0]) / C)
    elif v == colArray[2]:
        h = 60 * (4 + (colArray[0] - colArray[1]) / C)

    return np.array([h, s, l])

def lighten(colString, p):
    import numpy as np
    if p > 1:
        p = p / 100
    hsl = rgbToHSL(colString)
    hsl[2] = 1 - (1 - hsl[2]) * (1 - p)
    rgb = hslToRGB(hsl)
    return "#{:02X}{:02X}{:02X}".format(int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255))

def darken(colString, p):
    import numpy as np
    if p > 1:
        p = p / 100
    hsl = rgbToHSL(colString)
    hsl[2] = hsl[2] * (1 - p)
    rgb = hslToRGB(hsl)
    return "#{:02X}{:02X}{:02X}".format(int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255))

def init(docType = "report", dark = None, scheme = "twilight"):
    class Scheme(NamedTuple):
        ForegroundColour : str
        BackgroundColour : str
        Accent1 : str
        Accent2 : str
        Accent3 : str
        Accent4 : str
        Accent5 : str
        Accent6 : str
        Hyperlink : str
        FollowedHyperlink : str

    # Verify type of docType and scheme
    if not isinstance(docType, str):
        raise TypeError("\n\n\tArgument \"docType\" must be of type \"str\"\n\n")
    if not isinstance(scheme, str):
        raise TypeError("\n\n\tArgument \"scheme\" must be of type \"str\"\n\n")
    # Allow capital and lowercase versions
    scheme = scheme.lower()
    docType = docType.lower()
    if docType not in ["report", "presentation"]:
        raise ValueError("\n\n\tUnknown document type \"{}\"\n\n".format(docType))
    # Automatically use dark mode for presentations and light mode for reports unless otherwise specified.
    if dark == None:
        dark = not(docType == "report")
    # Find and read the colour schemes
    pypath=os.path.dirname(__file__)
    with open(pypath + "/colourSchemes.json", "r") as colourFile:
        colourSchemes = json.load(colourFile)

    if not(scheme in colourSchemes):
        raise Exception("\n\n\tColour scheme \"{}\" is not recognised.\n\n".format(scheme))

    colScheme = colourSchemes[scheme]

    if dark:
        tempCol = colScheme["ForegroundColour"]
        colScheme["ForegroundColour"] = colScheme["BackgroundColour"]
        colScheme["BackgroundColour"] = tempCol

    linewidths = {'presentation' : 1.4, 'report' : 0.8}
    markerSizes = {'presentation' : 4, 'report' : 6}

    formatting = {
        'presentation' : {
            'text.color' : colScheme["ForegroundColour"],
            'axes.labelcolor' : colScheme["ForegroundColour"],
            'axes.edgecolor' : colScheme["Accent1"],
            'xtick.color' : colScheme["Accent1"],
            'ytick.color' : colScheme["Accent1"],
            'axes.facecolor' : colScheme["BackgroundColour"],
            'figure.facecolor' : colScheme["BackgroundColour"],
            'axes.facecolor' : colScheme["BackgroundColour"],
            'legend.edgecolor' : colScheme["ForegroundColour"],
            'legend.facecolor' : colScheme["BackgroundColour"],
            'axes.spines.top' : False,
            'axes.spines.right' : False,
            'axes.prop_cycle' : cycler(
                'color',
                [colScheme["Accent" + str(i)] for i in range(1, 7)] +
                [lighten(
                    colScheme["Accent" + str(i)],
                    0.3
                ) for i in range(1, 7)]
            ),
            'axes.linewidth' : linewidths['presentation'],
            'xtick.major.width' : linewidths['presentation'],
            'ytick.major.width' : linewidths['presentation'],
            'lines.markersize' : markerSizes['presentation'],
            'figure.figsize' : (6.4, 3.6),
            'text.latex.preamble' : "\\usepackage{amsmath, amssymb}",
            'text.usetex' : True,
            'savefig.facecolor' : colScheme["BackgroundColour"],
            'savefig.edgecolor' : 'none',
            'font.family' : 'serif'
        },
        'report' : {
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
                [lighten(
                    colScheme["Accent" + str(i)],
                    0.3
                ) for i in range(1, 7)]
            ) if not(dark) else cycler(
                'color',
                [colScheme["Accent" + str(i)] for i in range(1, 7)] +
                [darken(
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
    }

    global schemeColours
    schemeColours = Scheme(
        ForegroundColour = colScheme["ForegroundColour"],
        BackgroundColour = colScheme["BackgroundColour"],
        Accent1 = colScheme["Accent1"],
        Accent2 = colScheme["Accent2"],
        Accent3 = colScheme["Accent3"],
        Accent4 = colScheme["Accent4"],
        Accent5 = colScheme["Accent5"],
        Accent6 = colScheme["Accent6"],
        Hyperlink = colScheme["Hyperlink"] if "Hyperlink" in colScheme else "#0000FF",
        FollowedHyperlink = colScheme["FollowedHyperlink"] if "FollowedHyperlink" in colScheme else "#FF00FF"
    )

    for key, val in formatting[docType].items():
        rcParams[key] = val

def getScheme():
    if 'schemeColours' in globals():
        return schemeColours
    else:
        raise ValueError("No scheme available. You must call qoplots.init() first.")

def getAvailableSchemes():
    pypath=os.path.dirname(__file__)
    with open(pypath + "/colourSchemes.json", "r") as colourFile:
        colourSchemes = json.load(colourFile)
    return list(colourSchemes.keys())
