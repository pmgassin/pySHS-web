


import matplotlib.pyplot as plt
import numpy as np
import matplotlib as mpl
import csv
import sys
import random
from scipy.integrate import tplquad
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.colors import ListedColormap


uu=sys.argv[1]
#dimx=int(input("Number of dimensionX?"))
#dimy=int(input("Number of dimensionY?"))
NR1=int(input("Number of dipole on one row1?"))
NR2=int(input("Number of dipole on one row2?"))
NR3=int(input("Number of dipole on one row3?"))
a=float(input("cube size1 in nm?"))
b=float(input("cube size2 in nm?"))
c=float(input("cube size3 in nm?"))
hj=0#float(input("%dissymetrie?"))
nombre=(NR1*NR2*NR3)
#b=a/5

with open(uu, "w") as f:
    f.write("")

phi=np.zeros(nombre)
theta=np.zeros(nombre)
psi=np.zeros(nombre)
x=np.zeros(nombre)
y=np.zeros(nombre)
z=np.zeros(nombre)

#***************************************
kkk=0
pas1=a/NR1
pas2=b/NR2
pas3=c/NR3


compteurplus=0
compteurmoins=0
#aaa=int(NR1/a)
#bbb=int(NR2/b)

grille = np.zeros((NR2, NR1), dtype=bool)
total_points = NR1 * NR2
nb_selection = total_points // 2
#print(grille)
# Sélection aléatoire des indices
indices = [(xx, yy) for xx in range(NR1) for yy in range(NR2)]
selection = random.sample(indices, nb_selection)

for xx, yy in selection:
    grille[yy,xx] = True


# Remplissage de la grille
#grille[indices_x, indices_y] = True

#print(grille)



for pm in range(NR3):
    for i in range(0,NR1):
        for j in range(0,NR2):
            if grille[j,i]==True:
                theta[kkk]=0.0*(np.random.randn())#+0.01*np.random.randn()
                compteurplus=compteurplus+1
                phi[kkk]=0#np.pi/2
                psi[kkk]=0.0
                x[kkk]=(i*pas1)#+ii*pas1#(1+np.sin(np.pi*i/500))
                y[kkk]=j*pas2#+jj*pas2
                z[kkk]=pm*pas3
                kkk=kkk+1

            else:
                theta[kkk]=np.pi+0.0*(np.random.randn())#+0.01*np.random.randn()
                compteurmoins=compteurmoins+1
                phi[kkk]=0#np.pi/2
                psi[kkk]=0.0
                x[kkk]=(i*pas1)#+ii*pas1#(1+np.sin(np.pi*i/500))
                y[kkk]=j*pas2#+jj*pas2
                z[kkk]=pm*pas3
                kkk=kkk+1



# Visualisation

nb_noir = np.sum(grille)           # Cases noires (sélectionnées)
nb_blanc = total_points - nb_noir  # Cases blanches

print(f"Grille {NR1} × {NR2} → Total = {total_points} points")
print(f"Cases noires (sélectionnées) : {nb_noir}")
print(f"Cases blanches (non sélectionnées) : {nb_blanc}")
print(f"Équilibre : {'✅ Parfait' if nb_noir == nb_blanc else '❌ Déséquilibré'}")

# ================== VISUALISATION ==================
cmap_perso = ListedColormap(['green', 'orange'])
plt.figure(figsize=(12, 10))
plt.imshow(grille, cmap=cmap_perso, interpolation='nearest')
plt.title(f"Grille {NR1} × {NR2} - Exactement {nb_selection} points sélectionnés")
plt.xlabel("X")
plt.ylabel("Y")
plt.colorbar(label='Noir = Sélectionné')
plt.grid(False)

plt.savefig(f"grille_selection_{NR1}x{NR2}.png", dpi=300, bbox_inches='tight')
plt.show()


    
xmax=np.amax(x)
ymax=np.amax(y)
zmax=np.amax(z)
bip=1#(a/3)#0.5#(xmax+ymax+zmax)/10      
print("nombre de dipole")
print(nombre)
print(compteurplus)
print(compteurmoins)
for j in range(nombre):
    with open(uu, "a") as f:
        valeurs = "%12.6f %12.6f %12.6f %12.6f %12.6f %12.6f\n" % (phi[j],theta[j],psi[j],x[j],y[j],z[j]) 
        f.write(valeurs)
  #  xiO=np.zeros(nombre)
  #  yiO=np.zeros(nombre)
   # ziO=np.zeros(nombre)

    #xiH1=np.zeros(nombre)
    #yiH1=np.zeros(nombre)
    #ziH1=np.zeros(nombre)

   # xiH2=np.zeros(nombre)
    #yiH2=np.zeros(nombre)
    #ziH2=np.zeros(nombre)

ax= plt.figure().add_subplot(projection='3d')#Axes3D(fig)
ax._axis3don = False
#ax = fig.gca(projection='3d')
ax.quiver(x,y,z,bip*np.cos(phi)*np.sin(theta),bip*np.sin(phi)*np.sin(theta),bip*np.cos(theta),color='r')
ax.grid(visible=0)
plt.savefig(uu)
plt.show()
        


