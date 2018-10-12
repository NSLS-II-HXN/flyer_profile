def tomo_scan(angle_start,angle_end,angle_num):
    x0 = -5.77
    y0 = -4.6
    angle_list = np.linspace(angle_start,angle_end,angle_num)
    print(angle_list)
    #'''
    for i in range(angle_num):
        print('taking data at ', angle_list[i],' deg')
        yield from bps.mov(sample.sth,angle_list[i])
        yield from fly_scan(x_start=x0-0.7, x_stop=x0+0.7, nx=36, y_start=y0-0.5, y_stop=y0+0.5, ny=26, exp_time=0.1, trigger_rate=9)
        yield from bps.mov(sample.sx, x0)
        yield from bps.mov(sample.sy, y0)
    #'''
        

        
