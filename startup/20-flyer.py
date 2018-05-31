import bluesky.plans as bps
import bluesky.preprocessors as bpp
import itertools
import time
from ophyd import EpicsMotor, MotorBundle, Component, EpicsSignal, Device
from ophyd.status import SubscriptionStatus
from ophyd import set_and_wait


class XYMotor(MotorBundle):
    x = Component(EpicsMotor, 'X')
    y = Component(EpicsMotor, 'Y')


motor = XYMotor('HXN{2DStage}V', name='motor')
set_scanning = EpicsSignal('HXN{2DStage}SetScanning', name='set_scanning')
scan_in_progress = EpicsSignal('HXN{2DStage}ScanInProgress', name='scan_in_progress')


class HXNStage(Device):
    x_start = Component(EpicsSignal, 'XStart-RB', write_pv='XStart')
    x_stop = Component(EpicsSignal, 'XStop-RB', write_pv='XStop')
    nx = Component(EpicsSignal, 'NX-RB', write_pv='NX')
    y_start = Component(EpicsSignal, 'YStart-RB', write_pv='YStart')
    y_stop = Component(EpicsSignal, 'YStop-RB', write_pv='YStop')
    ny = Component(EpicsSignal, 'NX-RB', write_pv='NX')
    trigger_rate = Component(EpicsSignal, 'TriggerRate-RB', write_pv='TriggerRate')
    start_scan = Component(EpicsSignal, 'StartScan.PROC')
    set_up_motors_a_different_way = Component(EpicsSignal, 'PLC20.PROC')
    start_fake_scan = Component(EpicsSignal, 'StartFakeScan.PROC')

hxn_stage = HXNStage('HXN{2DStage}', name='hxn_stage')


class Flyer:
    def __init__(self, detector, hxn_stage, motor):
        self.name = 'flyer'
        self.parent = None
        self.detector = detector
        self.hxn_stage = hxn_stage
        self.motor = motor
        self._traj_info = {}
        self._datum_ids = []

    def stage(self):
        # This sets a filepath (template for TIFFs) and generates a Resource
        # document in the detector.tiff Device's asset cache.
        self.detector.stage()

    def unstage(self):
        # This sets a filepath (template for TIFFs) and generates a Resource
        # document in the detector.tiff Device's asset cache.
        self.detector.unstage()


    def kickoff(self):
        set_scanning.put(1)

        def is_started(value, **kwargs):
            print(f'===== is_started: {value}')
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
            print(f'====== is_done: {value}')
            return not value

        x_moving  = SubscriptionStatus(scan_in_progress,
                                       is_done)
        return x_moving

    def describe_collect(self):
        return {
            'hxn_stage_flyer':
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
        print('====== starting collection... ')
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
        print(f'====== asset_docs_cache:\n{asset_docs_cache}, {len(asset_docs_cache)}')
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
            print(f'===== is_started: {value}')
            return bool(value)
        ready_to_scan  = SubscriptionStatus(scan_in_progress,
                                            is_started)

        self._traj_info.update({'nx': int(self.hxn_stage.nx.get()),
                                'ny': int(self.hxn_stage.ny.get())})
        return ready_to_scan & self.hxn_stage.start_fake_scan.set(1)


flyer = FakeFlyer(vis_eye1, hxn_stage, motor)


@bpp.stage_decorator([flyer])
def plan():
    yield from bps.fly([flyer])
