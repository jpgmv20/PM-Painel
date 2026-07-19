import matplotlib.pyplot as plt
import numpy as np

notas = np.array([[8, 1, 10, 4], [7, 9, 3, 10] ,[2, 9, 7, 0], [3, 9, 10, 4]])


disciplinas = ["Calculo 1", "AlgLinear", "Prog", "Fisica"]
alunos = ["Gilmar", "Gustavo", "Nicolas", "Miguel"]

fig, ax = plt.subplots()
im = ax.imshow(notas, cmap='Reds')

ax.set_xticks(np.arange(len(disciplinas)))
ax.set_yticks(np.arange(len(alunos)))

plt.colorbar(im)
plt.title("Mapa de calor")
plt.savefig("mapa.jpg")
plt.show()