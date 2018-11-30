import os
import bpy
import psutil
import pandas as pd
import multiprocessing as mp
import pathlib
import time


#get the number of physical cpu
cores = psutil.cpu_count(logical=False)

csv_dump_file = os.path.dirname(os.path.realpath(__file__)) + '/bshw.csv'

param = {
    'resolution': ((1920, 1080), (1280, 720)),
    'tiles': (4, 16),
    'tilesize': (64, 128),
    'samplepixel': (100, 300),
    'maxreflexions': (12, 24)
}

default_test_count = 10

result_table_cols = ['Experimento' ,'Resolução', 'Tiles', 'TamTile', 'SamplePixel', 'MaxReflexões', 'CPU', 'MaxMem']
resultset = pd.DataFrame(columns=result_table_cols)


#set cycles rendering
bpy.context.scene.render.engine = 'CYCLES'

#set CPU rendering device
bpy.context.scene.cycles.device = 'CPU'

bpy.context.scene.cycles.feature_set = 'SUPPORTED'

bpy.context.scene.render.resolution_percentage = 50

def proc_mon(target):
    worker_process = mp.Process(target=target)
    worker_process.start()
    p = psutil.Process(worker_process.pid)

    p.cpu_percent()
    cpu_usage = 0.0
    tick_count = 0
    max_mem_usage = p.memory_percent()
    while worker_process.is_alive():
        cpu_usage = cpu_usage + (p.cpu_percent() / psutil.cpu_count())
        tick_count = tick_count + 1;        

        mem_usage = p.memory_percent(memtype='vms')
        if mem_usage > max_mem_usage:
            max_mem_usage = mem_usage

        time.sleep(0.1)

    worker_process.join()

    print((cpu_usage / tick_count))

    return (cpu_usage / tick_count), max_mem_usage

for res in param['resolution']:
    for tc in param['tiles']:
        for ts in param['tilesize']:
            for sp in param['samplepixel']:
                for mr in param['maxreflexions']:
                    bpy.context.scene.render.resolution_x = res[0]
                    bpy.context.scene.render.resolution_y = res[1]
                    bpy.context.scene.render.threads_mode = 'FIXED'
                    bpy.context.scene.render.threads = tc
                    bpy.context.scene.render.tile_x = ts
                    bpy.context.scene.render.tile_y = ts
                    bpy.context.scene.cycles.samples = sp
                    bpy.context.scene.cycles.max_bounces = mr

                    for i in range(default_test_count):
                        results = proc_mon(target=bpy.ops.render.render)
                        resultset = resultset.append(pd.DataFrame(data=[[i, "{0} x {1}".format(res[0], res[1]), tc, ts, sp, mr, results[0], results[1]]], columns=result_table_cols), ignore_index=True)

resultset.to_csv(path_or_buf=open(csv_dump_file, 'w'))