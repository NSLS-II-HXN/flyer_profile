from ophyd import EpicsMotor, Device, Component as Cpt


class SampleMotors(Device):
    sx = Cpt(EpicsMotor, 'X}Mtr')
    sy = Cpt(EpicsMotor, 'Y}Mtr')
    sth = Cpt(EpicsMotor, 'Theta}Mtr')

class LaserMotors(Device):
    lx = Cpt(EpicsMotor, 'X}Mtr')
    ly = Cpt(EpicsMotor, 'Y}Mtr')

class MotorBundle(Device):
    x = Cpt(EpicsMotor, 'X}Mtr')
    y = Cpt(EpicsMotor, 'Y}Mtr')
    z = Cpt(EpicsMotor, 'Z}Mtr')

class SampleCentering(Device):
    x = Cpt(EpicsMotor, 'XF}Mtr')
    z = Cpt(EpicsMotor, 'ZF}Mtr')


# Motors in [mc01:10.3.0.111] Kohzu Stage1:
sample = SampleMotors('XF:03IDC-ES{Smpl:1-Ax:', name='sample')
laser = LaserMotors('XF:03IDC-ES{Laser:1-Ax:', name='laser')
cam_motors = MotorBundle('XF:03IDC-ES{Cam:1-Ax:', name='cam_motors')

# Filter motors in mc03-smartact.opi:
osa = MotorBundle('XF:03IDC-ES{Fltr:1-Ax:', name='osa')

# Sample centering in mc02-ecc100.opi:
smp_cntr = SampleCentering('XF:03IDC-ES{Smpl:1-Ax:', name='smp_cntr')


sd.baseline = [sample, laser, cam_motors,
               osa,
               smp_cntr,
              ]

