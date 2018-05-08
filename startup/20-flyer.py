import bluesky.plans as bps
import bluesky.preprocessors as bpp
import itertools
import time
from ophyd import EpicsMotor, MotorBundle, Component, EpicsSignal, Device
from ophyd.status import SubscriptionStatus
from ophyd.areadetector.filestore_mixins import resource_factory


class XYMotor(MotorBundle):
    x = Component(EpicsMotor, 'X')
    y = Component(EpicsMotor, 'Y')


motor = XYMotor('HXN{2DStage}V', name='motor')


class Stage(Device):
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

stage = Stage('HXN{2DStage}', name='stage')


"""
HXN{2DStage-MtrVY}.RBV
HXN{2DStage-MtrX}
HXN{2DStage-MtrX}.MOVN
HXN{2DStage-MtrX}.RBV
HXN{2DStage-MtrX}.STOP
HXN{2DStage-MtrY}
HXN{2DStage-MtrY}.MOVN
HXN{2DStage-MtrY}.RBV
HXN{2DStage-MtrY}.STOP
HXN{2DStage}-Asyn.AOUT
HXN{2DStage}-Asyn.TINP
HXN{2DStage}Home.PROC
HXN{2DStage}NX
HXN{2DStage}NX-RB
HXN{2DStage}NY
HXN{2DStage}NY-RB
HXN{2DStage}PLC20.PROC
HXN{2DStage}ResetPMAC.PROC
HXN{2DStage}StartFakeScan.PROC
HXN{2DStage}StartScan.PROC
HXN{2DStage}TriggerRate
HXN{2DStage}TriggerRate-RB
HXN{2DStage}VX
HXN{2DStage}VX.MOVN
HXN{2DStage}VX.RBV
HXN{2DStage}VX.STOP
HXN{2DStage}VY
HXN{2DStage}VY.MOVN
HXN{2DStage}VY.RBV
HXN{2DStage}X
HXN{2DStage}X.MOVN
HXN{2DStage}X.RBV
HXN{2DStage}X.STOP
HXN{2DStage}XStart-RB
HXN{2DStage}XStop
HXN{2DStage}XStop-RB
HXN{2DStage}Y
HXN{2DStage}Y.MOVN
HXN{2DStage}Y.RBV
HXN{2DStage}YStart
HXN{2DStage}YStart-RB
HXN{2DStage}YStop
HXN{2DStage}YStop-RB
"""


class Flyer:
    def __init__(self, detector, stage, motor):
        self.name = 'flyer'
        self.parent = None
        self.detector = detector
        self.hxn_stage = stage
        self.motor = motor
        self._traj_info = {}
        self._datum_ids = []

    def stage(self):
        self.detector.stage()
    

    def kickoff(self):
        self._traj_info.update({'nx': int(self.hxn_stage.nx.get()),
                                'ny': int(self.hxn_stage.ny.get())})
        return self.hxn_stage.start_scan.set(1)

    def complete(self):
        # Use whether X in the coordinate system is moving
        # as a proxy for whether the total flyscan is done.
        # This might be brittle but there is no straightforward way
        # to check for done-ness, and this is easy to put together.
        # Should probably be improved to account for y also.
        x_moving  = SubscriptionStatus(self.motor.x.motor_is_moving,
                                       lambda value, **kwargs: not(value))
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
        # Get the Resource which was produced when the detector was staged.
        (name, resource), = self.detector.tiff.collect_asset_docs()
        assert name == 'resource'
        self._datum_ids.clear()
        # Generate Datum documents from scratch here, because the detector was
        # triggered externally by the DeltaTau, never by ophyd.
        _, datum_factory = resource_factory(
            spec=resource['spec'],
            root=resource['root'],
            resource_path=resource['resource_path'],
            resource_kwargs=resource['resource_kwargs'],
            path_semantics=resource['path_semantics'])
        num_points = self._traj_info['nx'] * self._traj_info['ny']
        for i in range(num_points):
            datum = datum_factory({'point_number': i})
            self._datum_ids.append(datum['datum_id'])
            yield 'datum', datum

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
        self._traj_info.update({'nx': int(self.hxn_stage.nx.get()),
                                'ny': int(self.hxn_stage.ny.get())})
        self.hxn_stage.set_up_motors_a_different_way.set(1)
        time.sleep(1)  # DONT IMMITATE THIS -- BAD IDEA
        return self.hxn_stage.start_fake_scan.set(1)


flyer = FakeFlyer(vis_eye1, stage, motor)


@bpp.stage_decorator([flyer])
def plan():
    yield from bps.fly([flyer])
