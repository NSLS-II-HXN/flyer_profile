import bluesky.plans as bp
import bluesky.plan_stubs as bps
import bluesky.preprocessors as bpp
import itertools
import time
from ophyd import EpicsMotor, MotorBundle, Component, EpicsSignal, Device
from ophyd.status import SubscriptionStatus
from ophyd import set_and_wait


class XYMotor(MotorBundle):
    x = Component(EpicsMotor, 'X')
    y = Component(EpicsMotor, 'Y')


# motor = XYMotor('XF:03IDC-CT{MC:01}V', name='motor')
set_scanning = EpicsSignal('XF:03IDC-CT{MC:01}SetScanning', name='set_scanning')
scan_in_progress = EpicsSignal('XF:03IDC-CT{MC:01}ScanInProgress', name='scan_in_progress')


class HXNStage(Device):
    x_start = Component(EpicsSignal, 'XStart-RB', write_pv='XStart')
    x_stop = Component(EpicsSignal, 'XStop-RB', write_pv='XStop')
    nx = Component(EpicsSignal, 'NX-RB', write_pv='NX')
    y_start = Component(EpicsSignal, 'YStart-RB', write_pv='YStart')
    y_stop = Component(EpicsSignal, 'YStop-RB', write_pv='YStop')
    ny = Component(EpicsSignal, 'NY-RB', write_pv='NY')
    trigger_rate = Component(EpicsSignal, 'TriggerRate-RB', write_pv='TriggerRate')
    start_scan = Component(EpicsSignal, 'StartScan.PROC')
    # start_fake_scan = Component(EpicsSignal, 'StartFakeScan.PROC')

hxn_stage = HXNStage('XF:03IDC-CT{MC:01}', name='hxn_stage')


class Flyer:
    def __init__(self, detector, hxn_stage):
        self.name = 'flyer'
        self.parent = None
        self.detector = detector
        self.hxn_stage = hxn_stage
        self._traj_info = {}
        self._datum_ids = []

    def stage(self):
        # This sets a filepath (template for TIFFs) and generates a Resource
        # document in the detector.tiff Device's asset cache.
        self.detector.stage_sigs['cam.image_mode'] = 'Multiple'
        self.detector.stage_sigs['cam.trigger_mode'] = 'Sync In 2'
        self.detector.stage()
        self.detector.cam.acquire.put(1)
        # self.detector.tiff.capture.put(1)

    def unstage(self):
        # This sets a filepath (template for TIFFs) and generates a Resource
        # document in the detector.tiff Device's asset cache.
        self.detector.unstage()
        self.detector.cam.acquire.put(0)

    def kickoff(self):
        set_scanning.put(1)

        def is_started(value, **kwargs):
            return bool(value)
        ready_to_scan  = SubscriptionStatus(scan_in_progress,
                                            is_started)
        self._traj_info.update({'nx': int(self.hxn_stage.nx.get()),
                                'ny': int(self.hxn_stage.ny.get())})

        return ready_to_scan & self.hxn_stage.start_scan.set(1)

    def complete(self):
        # Use whether X in the coordinate system is moving
        # as a proxy for whether the total flyscan is done.
        # This might be brittle but there is no straightforward way
        # to check for done-ness, and this is easy to put together.
        # Should probably be improved to account for y also.

        def is_done(value, **kwargs):
            return not value

        x_moving  = SubscriptionStatus(scan_in_progress,
                                       is_done)
        return x_moving

    def describe_collect(self):
        return {
            'primary':
                {'x': {'source': '',
                       'dtype': 'number',
                       'shape': []},
                 'y': {'source': '',
                       'dtype': 'number',
                       'shape': []},
                 'image': {'source': '...',
                           'dtype': 'array',
                           'shape': [],  # TODO
                           'external': 'FILESTORE:'}
                 }
                }

    def collect_asset_docs(self):
        asset_docs_cache = []
        # Get the Resource which was produced when the detector was staged.
        (name, resource), = self.detector.tiff.collect_asset_docs()
        assert name == 'resource'
        asset_docs_cache.append(('resource', resource))
        self._datum_ids.clear()
        # Generate Datum documents from scratch here, because the detector was
        # triggered externally by the DeltaTau, never by ophyd.
        resource_uid = resource['uid']
        num_points = self._traj_info['nx'] * self._traj_info['ny']
        for i in range(num_points):
            datum_id = '{}/{}'.format(resource_uid, i)
            self._datum_ids.append(datum_id)
            datum = {'resource': resource_uid,
                     'datum_id': datum_id,
                     'datum_kwargs': {'point_number': i}}
            asset_docs_cache.append(('datum', datum))
        return tuple(asset_docs_cache)

    def collect(self):
        for i, datum_id in enumerate(self._datum_ids):
            now = time.time()
            yield {
                'data': {
                    'x': 0,  # TODO interpolate
                    'y': 0,  # TODO interpolate
                    'image': datum_id},
                'timestamps': {
                    'x': now,
                    'y': now,
                    'image': now},
                'time': now,
                'seq_num': 1 + i,
                'filled': {'image': False}}


class FakeFlyer(Flyer):
    def kickoff(self):
        
        set_scanning.put(1)

        def is_started(value, **kwargs):
            return bool(value)
        ready_to_scan  = SubscriptionStatus(scan_in_progress,
                                            is_started)

        self._traj_info.update({'nx': int(self.hxn_stage.nx.get()),
                                'ny': int(self.hxn_stage.ny.get())})
        return ready_to_scan & self.hxn_stage.start_fake_scan.set(1)


flyer = Flyer(vis_eye1, hxn_stage)


@bpp.stage_decorator([flyer])
def fly_scan(*, nx, ny, exp_time):
    yield from bps.mv(flyer.hxn_stage.nx, nx,
                      flyer.hxn_stage.ny, ny)

    yield from bps.mv(flyer.detector.cam.acquire_time, exp_time)
    yield from bps.mv(flyer.detector.cam.num_images,
        int(flyer.hxn_stage.nx.get()) * int(flyer.hxn_stage.ny.get())
    )

    yield from bp.fly([flyer])
