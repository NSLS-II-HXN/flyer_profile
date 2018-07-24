# Make ophyd listen to pyepics.
# from ophyd import setup_ophyd
# setup_ophyd()

# Set up a RunEngine and use metadata backed by a sqlite file.
from bluesky import RunEngine
from bluesky.utils import get_history
RE = RunEngine(get_history())

# Set up a Broker backed by a temporary directory.
# In production, a Broker is usually backed by a Mongo database.
import os

config = {'description': 'HXN lab MongoDB on ws10',
          'metadatastore': {
              'module': 'databroker.headersource.mongo',
              'class': 'MDS',
              'config': {
                  'host': 'localhost',
                  'port': 27017,
                  'database': 'datastore-hxnlab',
                  'timezone': 'US/Eastern'}
              },
          'assets': {
              'module': 'databroker.assets.mongo',
              'class': 'Registry',
              'config': {
                  'host': 'localhost',
                  'port': 27017,
                  'database': 'filestore-hxnlab'}
              }
          }

from databroker import Broker
db = Broker.from_config(config)

# Subscribe metadatastore to documents.
# If this is removed, data is not saved to metadatastore.
RE.subscribe(db.insert)

# Set up SupplementalData.
from bluesky import SupplementalData
sd = SupplementalData()
RE.preprocessors.append(sd)

# Add a progress bar.
from bluesky.utils import ProgressBarManager
pbar_manager = ProgressBarManager()
RE.waiting_hook = pbar_manager

# Register bluesky IPython magics.
from bluesky.magics import BlueskyMagics
get_ipython().register_magics(BlueskyMagics)

# Set up the BestEffortCallback.
from bluesky.callbacks.best_effort import BestEffortCallback
bec = BestEffortCallback()
RE.subscribe(bec)
bec.disable_plots()
peaks = bec.peaks  # just as alias for less typing

# At the end of every run, verify that files were saved and
# print a confirmation message.
from bluesky.callbacks.broker import verify_files_saved
# RE.subscribe(post_run(verify_files_saved), 'stop')

# Import matplotlib and put it in interactive mode.
import matplotlib.pyplot as plt
plt.ion()

# Make plots update live while scans run.
from bluesky.utils import install_kicker
install_kicker()

# Optional: set any metadata that rarely changes.
# RE.md['beamline_id'] = 'YOUR_BEAMLINE_HERE'

# convenience imports
from bluesky.callbacks import *
from bluesky.callbacks.broker import *
from bluesky.simulators import *
from bluesky.plans import *
from bluesky.plan_stubs import mv, mvr
import numpy as np
import bluesky.plans as bp
import bluesky.plan_stubs as bps
import bluesky.preprocessors as bpp


def ts_msg_hook(msg):
    t = '{:%H:%M:%S.%f}'.format(datetime.datetime.now())
    msg_fmt = '{: <17s} -> {!s: <15s} args: {}, kwargs: {}'.format(
        msg.command,
        msg.obj.name if hasattr(msg.obj, 'name') else msg.obj,
        msg.args,
        msg.kwargs)
    print('{} {}'.format(t, msg_fmt))
