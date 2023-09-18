from krita import *
from .comic_panels_plugin import comicPanelsPlugin

Krita.instance().addExtension(comicPanelsPlugin(Krita.instance()))
