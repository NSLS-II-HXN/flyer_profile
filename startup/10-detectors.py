import time as ttime  # tea time
from types import SimpleNamespace
from datetime import datetime
from ophyd import (ProsilicaDetector, ProsilicaDetectorCam,
                   SingleTrigger, TIFFPlugin,
                   ImagePlugin, StatsPlugin, DetectorBase, HDF5Plugin,
                   AreaDetector, EpicsSignal, EpicsSignalRO, ROIPlugin,
                   TransformPlugin, ProcessPlugin, Device)
from ophyd.areadetector.cam import AreaDetectorCam
from ophyd.areadetector.base import ADComponent, EpicsSignalWithRBV
from ophyd.areadetector.filestore_mixins import (FileStoreTIFFIterativeWrite,
                                                 FileStoreHDF5IterativeWrite,
                                                 FileStoreBase, new_short_uid,
                                                 FileStoreIterativeWrite)
from ophyd import Component as Cpt, Signal
from ophyd.utils import set_and_wait
from pathlib import PurePath
from bluesky.plan_stubs import stage, unstage, open_run, close_run, trigger_and_read, pause

from nslsii.ad33 import SingleTriggerV33, StatsPluginV33


class ProsilicaDetectorCamV33(ProsilicaDetectorCam):
    wait_for_plugins = Cpt(EpicsSignal, 'WaitForPlugins',
                           string=True, kind='config')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stage_sigs['wait_for_plugins'] = 'Yes'

    def ensure_nonblocking(self):
        self.stage_sigs['wait_for_plugins'] = 'Yes'
        for c in self.parent.component_names:
            cpt = getattr(self.parent, c)
            if cpt is self:
                continue
            if hasattr(cpt, 'ensure_nonblocking'):
                cpt.ensure_nonblocking()


class ProsilicaDetectorV33(ProsilicaDetector):
    cam = Cpt(ProsilicaDetectorCamV33, 'cam1:')


class TIFFPluginWithFileStore(TIFFPlugin, FileStoreTIFFIterativeWrite):
    """Add this as a component to detectors that write TIFFs."""
    pass


class HDF5PluginWithFileStore(HDF5Plugin, FileStoreHDF5IterativeWrite):
    """Add this as a component to detectors that write HDF5s."""
    def get_frames_per_point(self):
        if not self.parent.is_flying:
            return self.parent.cam.num_images.get()
        else:
            return 1


class TIFFPluginEnsuredOff(TIFFPlugin):
    """Add this as a component to detectors that do not write TIFFs."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stage_sigs.update([('auto_save', 'No')])


class StandardProsilica(SingleTriggerV33, ProsilicaDetectorV33):
    image = Cpt(ImagePlugin, 'image1:')
    stats1 = Cpt(StatsPluginV33, 'Stats1:')
    stats2 = Cpt(StatsPluginV33, 'Stats2:')
    stats3 = Cpt(StatsPluginV33, 'Stats3:')
    stats4 = Cpt(StatsPluginV33, 'Stats4:')
    stats5 = Cpt(StatsPluginV33, 'Stats5:')
    trans1 = Cpt(TransformPlugin, 'Trans1:')
    roi1 = Cpt(ROIPlugin, 'ROI1:')
    roi2 = Cpt(ROIPlugin, 'ROI2:')
    roi3 = Cpt(ROIPlugin, 'ROI3:')
    roi4 = Cpt(ROIPlugin, 'ROI4:')
    proc1 = Cpt(ProcessPlugin, 'Proc1:')

    # This class does not save TIFFs. We make it aware of the TIFF plugin
    # only so that it can ensure that the plugin is not auto-saving.
    tiff = Cpt(TIFFPluginEnsuredOff, suffix='TIFF1:')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._is_flying = False

    @property
    def is_flying(self):
        return self._is_flying

    @is_flying.setter
    def is_flying(self, is_flying):
        self._is_flying = is_flying


class CustomTIFFPluginWithFileStore(TIFFPluginWithFileStore):
    def get_frames_per_point(self):
        if not self.parent.is_flying:
            return self.parent.cam.num_images.get()
        else:
            return 1


class StandardProsilicaWithTIFF(StandardProsilica):
    tiff = Cpt(CustomTIFFPluginWithFileStore,
               suffix='TIFF1:',
               write_path_template='/DATA/cam/%Y/%m/%d/',
               root='/DATA/cam')


class StandardProsilicaWithHDF5(StandardProsilica):
    hdf5 = Cpt(HDF5PluginWithFileStore,
               suffix='HDF1:',
               write_path_template='/DATA/cam/%Y/%m/%d/',
               root='/DATA/cam')


# vis_eye1 = StandardProsilica('XF:03ID-BI{CAM:1}', name='vis_eye1')
vis_eye1 = StandardProsilicaWithTIFF('XF:03ID-BI{CAM:1}', name='vis_eye1')
vis_eye1.cam.ensure_nonblocking()

vis_eye1_hdf5 = StandardProsilicaWithHDF5('XF:03ID-BI{CAM:1}', name='vis_eye1_hdf5')


for camera in [vis_eye1, vis_eye1_hdf5]:
    camera.read_attrs = ['stats1', 'stats2', 'stats3', 'stats4', 'stats5']
    if 'hdf' not in camera.name:
        camera.read_attrs.append('tiff')
    else:
        camera.read_attrs.append('hdf5')

    camera.tiff.read_attrs = []  # leaving just the 'image'
    for stats_name in ['stats1', 'stats2', 'stats3', 'stats4', 'stats5']:
        stats_plugin = getattr(camera, stats_name)
        stats_plugin.read_attrs = ['total']
        # camera.stage_sigs[stats_plugin.blocking_callbacks] = 1

    # camera.stage_sigs[camera.roi1.blocking_callbacks] = 1
    # camera.stage_sigs[camera.trans1.blocking_callbacks] = 1

    camera.stage_sigs[camera.cam.image_mode] = 'Multiple'

    # 'Sync In 2' is used for fly scans:
    # camera.stage_sigs[camera.cam.trigger_mode] = 'Sync In 2'

    # 'Fixed Rate' is used for step scans:
    camera.stage_sigs[camera.cam.trigger_mode] = 'Fixed Rate'

    camera.stage_sigs[camera.cam.array_counter] = 0
    camera.stage_sigs[camera.tiff.array_counter] = 0
    camera.stats1.total.kind = 'hinted'

