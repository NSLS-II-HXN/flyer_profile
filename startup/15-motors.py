from ophyd import EpicsMotor, Device, Component as Cpt


class MotorBundle(Device):
    sx = Cpt(EpicsMotor, 'X}Mtr')
    sy = Cpt(EpicsMotor, 'Y}Mtr')


stage = MotorBundle('XF:03IDC-ES{Smpl:1-Ax:', name='stage')
