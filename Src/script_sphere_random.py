#!/usr/bin/env python3
import math
import random
import sys
import numpy as np

if len(sys.argv) < 5:
    print("Usage: python script_sphere_random.py <output_file> <radius_nm> <n_dipoles> <sigma>")
    sys.exit(1)

output_file = sys.argv[1]
a = float(sys.argv[2])          # radius
nombre = int(sys.argv[3])       # number of dipoles
ind = float(sys.argv[4])        # sigma (disorder)

def fibonacci_sphere(samples=1, randomize=True):
    rnd = 1.
    if randomize:
        rnd = random.random() * samples
    points = []
    offset = 2. / samples
    increment = math.pi * (3. - math.sqrt(5.))
    for i in range(samples):
        y = ((i * offset) - 1) + (offset / 2)
        r = math.sqrt(1 - pow(y, 2))
        phi = ((i + rnd) % samples) * increment
        x = math.cos(phi) * r
        z = math.sin(phi) * r
        points.append([x, y, z])
    return points

points = fibonacci_sphere(nombre)

with open(output_file, "w") as f:
    for i in range(nombre):
        x = a * points[i][0]
        y = a * points[i][1]
        z = a * points[i][2]

        theta = np.arccos(z / a)
        psi = 0.0


        if y>0:
            phi=(np.arccos(x/(a*np.sin(theta))))
        else:
            phi=-(np.arccos(x/(a*np.sin(theta))))


        # Ajout du désordre
        theta += np.random.randn() * ind
        phi   += np.random.randn() * ind

        f.write("%12.6f %12.6f %12.6f %12.6f %12.6f %12.6f\n" %
                (phi, theta, psi, x, y, z))

print(f"Fichier d'orientation généré : {output_file} ({nombre} dipôles)")
