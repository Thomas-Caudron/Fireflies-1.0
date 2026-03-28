import sys
import subprocess

# Required Python version
MIN_VER = (3, 7)

if sys.version_info[:2] < MIN_VER:
    sys.exit("This game requires Python {}.{} or newer.".format(*MIN_VER))

# Launch the actual game
subprocess.run([sys.executable, "main.py"])