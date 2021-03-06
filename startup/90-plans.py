import bluesky.preprocessors as bpp
from bluesky.plan_stubs import sleep, abs_set
import bluesky
from bluesky.plans import rel_spiral_square, rel_spiral_fermat, rel_spiral
from ophyd import EpicsScaler, EpicsSignal


xstart = EpicsSignal(read_pv='HXN{2DStage}XStart-RB', write_pv='HXN{2DStage}XStart')
xstop  = EpicsSignal(read_pv='HXN{2DStage}XStop-RB', write_pv='HXN{2DStage}XStop')
ystart = EpicsSignal(read_pv='HXN{2DStage}YStart-RB', write_pv='HXN{2DStage}YStart')
ystop  = EpicsSignal(read_pv='HXN{2DStage}YStop-RB', write_pv='HXN{2DStage}YStop')

nx = EpicsSignal(read_pv='HXN{2DStage}NX-RB', write_pv='HXN{2DStage}NX')
ny = EpicsSignal(read_pv='HXN{2DStage}NY-RB', write_pv='HXN{2DStage}NY')


go = EpicsSignal(read_pv='HXN{2DStage}StartScan.PROC', write_pv='HXN{2DStage}StartScan.PROC')

'''
def fly_plan():
    """This is my plan"""

    yield from bluesky.plan_stubs.mv(xstart, 0.100)
    yield from bluesky.plan_stubs.mv(xstop,  0.200)
    yield from bluesky.plan_stubs.mv(ystart, 0.100)
    yield from bluesky.plan_stubs.mv(ystop,  0.200)
    yield from bluesky.plan_stubs.mv(nx, 3)
    yield from bluesky.plan_stubs.mv(ny, 3)
    yield from bluesky.plan_stubs.mv(go, 1)

    print('hello')
    yield from sleep(2)
    # Read image: XF:03ID-BI{CAM:1}image1:ArrayData
    print('done')
'''

def step_scan(*, detector,
              x_motor, y_motor,
              x_start=-5, x_end=5, x_num=11,
              y_start=-5, y_end=5, y_num=11,
              exposure_time=0.01, num_images=1):
    yield from bps.mv(detector.cam.num_images, num_images)
    yield from bps.mv(flyer.detector.cam.acquire_time, exposure_time)
    yield from rel_grid_scan([detector], y_motor, y_start, y_end, y_num, x_motor, x_start, x_end, x_num, False)


def spiral(*, detector,
           x_motor, y_motor,
           x_range = 1, x_num=11,
           y_range = 1, y_num=11,
           dr = 0.1, dr_y = None,
           nth = 5,
           exposure_time=0.01, num_images=1):
    yield from bps.mv(detector.cam.num_images, num_images)
    yield from bps.mv(flyer.detector.cam.acquire_time, exposure_time)
    yield from rel_spiral([det], motor1, motor2, x_range=x_range,y_range=y_range, dr=dr,dr_y= dr_y, nth=nth)

def fermat(*, detector,
           x_motor, y_motor,
           x_range = 1, x_num=11,
           y_range = 1,y_num=11,
           dr = 0.1, factor = 1,
           exposure_time=0.01, num_images=1):
    yield from bps.mv(detector.cam.num_images, num_images)
    yield from bps.mv(flyer.detector.cam.acquire_time, exposure_time)
    yield from rel_spiral_fermat([det], motor1, motor2,
                     x_range=x_range, y_range=y_range, dr=dr, factor=factor, tilt=0.0)

def spiral_square(*, detector,
           x_motor, y_motor,
           x_range = 1, x_num=11,
           y_range = 1, y_num=11,
           exposure_time=0.01, num_images=1):
    yield from bps.mv(detector.cam.num_images, num_images)
    yield from bps.mv(flyer.detector.cam.acquire_time, exposure_time)
    yield from rel_spiral_square([det], motor1, motor2,x_range=x_range, y_range=y_range, x_num=x_num, y_num=y_num)

'''
def step_scan(*, cam,
              x_motor=None, x_start=-5, x_end=5, x_num=11,
              y_motor=None, y_start=-5, y_end=5, y_num=11,
              exposure_time=0.01):

    assert x_motor, 'Provide x_motor object'
    assert y_motor, 'Provide y_motor object'

    x_home = x_motor.position
    y_home = y_motor.position

    def move_home():
        yield from bps.mov(x_motor, x_home,
                           y_motor, y_home)

    def main():
        yield from bps.mov(cam.cam.acquire_time, exposure_time)
        yield from bp.grid_scan([cam],
                                y_motor, y_home+y_start, y_home+y_end, y_num,
                                x_motor, x_home+x_start, x_home+x_end, x_num,
                                False)
        yield from bps.mov(x_motor, x_home, y_motor, y_home)

    yield from bpp.finalize_wrapper(main(), move_home())
'''
