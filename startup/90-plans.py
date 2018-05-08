from bluesky.plan_stubs import sleep, abs_set
import bluesky
from ophyd import EpicsScaler, EpicsSignal


xstart = EpicsSignal(read_pv='HXN{2DStage}XStart-RB', write_pv='HXN{2DStage}XStart')
xstop  = EpicsSignal(read_pv='HXN{2DStage}XStop-RB', write_pv='HXN{2DStage}XStop')
ystart = EpicsSignal(read_pv='HXN{2DStage}YStart-RB', write_pv='HXN{2DStage}YStart')
ystop  = EpicsSignal(read_pv='HXN{2DStage}YStop-RB', write_pv='HXN{2DStage}YStop')

nx = EpicsSignal(read_pv='HXN{2DStage}NX-RB', write_pv='HXN{2DStage}NX')
ny = EpicsSignal(read_pv='HXN{2DStage}NY-RB', write_pv='HXN{2DStage}NY')


go = EpicsSignal(read_pv='HXN{2DStage}StartScan.PROC', write_pv='HXN{2DStage}StartScan.PROC')

def myplan():
    """This is my plan"""

    yield from bluesky.plan_stubs.mv(xstart, 100)
    yield from bluesky.plan_stubs.mv(xstop,  200)
    yield from bluesky.plan_stubs.mv(ystart, 100)
    yield from bluesky.plan_stubs.mv(ystop,  200)
    yield from bluesky.plan_stubs.mv(nx, 3)
    yield from bluesky.plan_stubs.mv(ny, 3)
    yield from bluesky.plan_stubs.mv(go, 1)

    print('hello')
    yield from sleep(2)
    # Read image: XF:03ID-BI{CAM:1}image1:ArrayData
    print('done')
