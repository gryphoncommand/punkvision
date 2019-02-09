"""

Copyright 2018 LN STEMpunks & ChemicalDevelopment

  This file is part of the punkvision project

  punkvision, punkvision Documentation, and any other resources in this 
project are free software; you are free to redistribute it and/or modify 
them under  the terms of the GNU General Public License; either version 
3 of the license, or any later version.

  These programs are hopefully useful and reliable, but it is understood 
that these are provided WITHOUT ANY WARRANTY, or MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE. See the GPLv3 or email at 
<info@chemicaldevelopment.us> for more info on this.

  Here is a copy of the GPL v3, which this software is licensed under. You 
can also find a copy at http://www.gnu.org/licenses/.


"""


__all__ = ["all", "defines", "basic", "io", "streaming", "fun"]


try:
    from vpl import opencl
    __all__ += ["opencl"]
except:
    # do nothing, opencl not supported
    pass

from vpl.defines import VPL, cv2, Pipeline
from vpl import basic
from vpl import fun
from vpl import streaming
from vpl import io
from vpl import util

from enum import Enum
import time
import threading
import math
import os
import glob
import pathlib

