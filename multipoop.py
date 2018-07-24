import numpy
import time
import multiprocessing

x0 = numpy.linspace(0, 120245, 1000000)
t0 = time.time()

def f0(x):
    return x**2 + numpy.cos(x)

y0 = f0(x0)

t1 = time.time()

nprocess = 12

first_idx = lambda i: i * len(x0) // nprocess
last_idx = lambda i: (i + 1) * len(x0) // nprocess

def f(x, i, queue):
    ret = numpy.empty((last_idx(i) - first_idx(i),))
    ret = x[first_idx(i):last_idx(i)]**2 + numpy.cos(x[first_idx(i):last_idx(i)])
    queue.put(ret)

queues = [multiprocessing.Queue() for _ in range(nprocess)]
processes = [multiprocessing.Process(target=f, args=(x0, i, queues[i])) for i in range(nprocess)]

for i in range(nprocess):
    processes[i].start()

y1 = numpy.empty_like(x0)
for i, q in enumerate(queues):
    y1[first_idx(i):last_idx(i)] =  q.get()

t2 = time.time()

print("Numpy time", (t1 - t0))
print("multiprocessing time", (t2 - t1))
assert numpy.allclose(y0, y1)

