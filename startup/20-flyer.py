import bluesky.plans as bp
import bluesky.plan_stubs as bps
import bluesky.preprocessors as bpp
import itertools
import time
from ophyd import EpicsMotor, MotorBundle, Component, EpicsSignal, Device
from ophyd.status import SubscriptionStatus
from ophyd import set_and_wait


class Flyer:
    def __init__(self, detector, hxn_stage):
        self.name = 'flyer'
        self.parent = None
        self.detector = detector
        self.hxn_stage = hxn_stage
        self._traj_info = {}
        self._array_size = {}
        self._datum_ids = []

    def stage(self):
        # This sets a filepath (template for TIFFs) and generates a Resource
        # document in the detector.tiff Device's asset cache.
        self.detector.is_flying = True
        self.detector.stage_sigs['cam.image_mode'] = 'Multiple'
        self.detector.stage_sigs['cam.trigger_mode'] = 'Sync In 2'
        self.detector.stage()
        self.detector.cam.acquire.put(1)
        # self.detector.tiff.capture.put(1)

    def unstage(self):
        # This sets a filepath (template for TIFFs) and generates a Resource
        # document in the detector.tiff Device's asset cache.
        self.detector.unstage()
        self.detector.is_flying = False
        self.detector.cam.acquire.put(0)

    def kickoff(self):
        set_scanning.put(1)

        def is_started(value, **kwargs):
            return bool(value)
        ready_to_scan  = SubscriptionStatus(scan_in_progress,
                                            is_started)
        self._traj_info.update({'nx': int(self.hxn_stage.nx.get()),
                                'ny': int(self.hxn_stage.ny.get()),
                                'x_start': self.hxn_stage.x_start.get(),
                                'x_stop': self.hxn_stage.x_stop.get(),
                                'y_start': self.hxn_stage.y_start.get(),
                                'y_stop': self.hxn_stage.y_stop.get(),
                                })

        self._array_size.update({'height': self.detector.tiff.array_size.height.get(),
                                 'width': self.detector.tiff.array_size.width.get()})

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
                       'shape': [self._traj_info['nx']]},
                 'y': {'source': '',
                       'dtype': 'number',
                       'shape': [self._traj_info['ny']]},
                 'image': {'source': '...',
                           'dtype': 'array',
                           'shape': [self._array_size['height'],
                                     self._array_size['width']],
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
        assert len(self._datum_ids) == self._traj_info['nx'] * self._traj_info['ny']

        nx = self._traj_info['nx']
        x_start = self._traj_info['x_start']
        x_stop = self._traj_info['x_stop']

        ny = self._traj_info['ny']
        y_start = self._traj_info['y_start']
        y_stop = self._traj_info['y_stop']

        i = 0
        # y is a slow axis
        for y in np.linspace(y_start, y_stop, ny):
            # x is a fast axis
            for x in np.linspace(x_start, x_stop, nx):
                datum_id = self._datum_ids[i]
                i += 1
                now = time.time()
                yield {
                    'data': {
                        'x': x,
                        'y': y,
                        'image': datum_id},
                    'timestamps': {
                        'x': now,
                        'y': now,
                        'image': now},
                    'time': now,
                    'seq_num': i,
                    'filled': {'image': False}}


class HXNStage(Device):
    x_start = Component(EpicsSignal, 'XStart-RB', write_pv='XStart')
    x_stop = Component(EpicsSignal, 'XStop-RB', write_pv='XStop')
    nx = Component(EpicsSignal, 'NX-RB', write_pv='NX')
    y_start = Component(EpicsSignal, 'YStart-RB', write_pv='YStart')
    y_stop = Component(EpicsSignal, 'YStop-RB', write_pv='YStop')
    ny = Component(EpicsSignal, 'NY-RB', write_pv='NY')
    trigger_rate = Component(EpicsSignal, 'TriggerRate-RB', write_pv='TriggerRate')
    start_scan = Component(EpicsSignal, 'StartScan.PROC')


# Objects for the scan
set_scanning = EpicsSignal('XF:03IDC-CT{MC:01}SetScanning', name='set_scanning')
scan_in_progress = EpicsSignal('XF:03IDC-CT{MC:01}ScanInProgress', name='scan_in_progress')
hxn_stage = HXNStage('XF:03IDC-CT{MC:01}', name='hxn_stage')
flyer = Flyer(vis_eye1, hxn_stage)


def fly_scan(*, x_start, x_stop, nx, y_start, y_stop, ny, exp_time, trigger_rate=7, md={}):
    """Fly scan plan with a stage (X and Y motors) and a camera.

    How to run:
    -----------
    RE(fly_scan(x_start=0, x_stop=0.1, nx=50, y_start=0, y_stop=0.1, ny=4,
                exp_time=0.01, trigger_rate=5))

    Parameters
    ----------
    x_start : float
        start position of the X-motor of the stage
    x_stop : float
        stop position of the X-motor of the stage
    nx : integer
        number of points for the X-motor
    y_start : float
        start position of the X-motor of the stage
    y_stop : float
        stop position of the Y-motor of the stage
    ny : integer
        number of points for the Y-motor
    exp_time : float
        exposure time of the camera
    trigger_rate : integer, optional
        trigger rate of the camera
    md : dict, optional
        metadata
    """

    yield from bps.mv(
        # X motor:
        flyer.hxn_stage.x_start, x_start,
        flyer.hxn_stage.x_stop, x_stop,
        flyer.hxn_stage.nx, nx,

        # Y motor:
        flyer.hxn_stage.y_start, y_start,
        flyer.hxn_stage.y_stop, y_stop,
        flyer.hxn_stage.ny, ny,

        # Trigger rate:
        flyer.hxn_stage.trigger_rate, trigger_rate,
    )

    yield from bps.sleep(1.0)
    for c in flyer.hxn_stage.component_names:
        print(f'{getattr(flyer.hxn_stage, c).read()}')

    yield from bps.mv(flyer.detector.cam.acquire_time, exp_time)
    yield from bps.mv(flyer.detector.cam.num_images,
        int(flyer.hxn_stage.nx.get()) * int(flyer.hxn_stage.ny.get())
    )

    # md.update({'x_start': x_start, 'x_stop': x_stop, 'nx': nx,
    #            'y_start': y_start, 'y_stop': y_stop, 'ny': nx,
    #            'exp_time': exp_time, 'trigger_rate': trigger_rate,
    #            })

    yield from bps.sleep(1.0)

    @bpp.stage_decorator([flyer])
    def _fly_scan():
        yield from bp.fly([flyer])

    yield from _fly_scan()

