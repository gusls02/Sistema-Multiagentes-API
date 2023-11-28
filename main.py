from mesa import Agent, Model
from mesa.space import MultiGrid
from mesa.time import SimultaneousActivation
from mesa.datacollection import DataCollector
import random
import math
from flask import Flask, request, jsonify

# %matplotlib inline
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.animation as animation
plt.rcParams["animation.html"] = "jshtml"
matplotlib.rcParams['animation.embed_limit'] = 2**128

import numpy as np
import pandas as pd
import json
import time
import datetime

from IPython.display import HTML


def get_grid(model):
    grid = np.zeros((model.grid.width, model.grid.height))
    for cell in model.grid.coord_iter():
        cell_content, (x, y) = cell
        for obj in cell_content:
            if isinstance(obj, Pasajero):
                grid[x][y] = 1  #utilizaremos el valor 1 para los pasajeros
            elif isinstance(obj, Estacion):
                grid[x][y] = 2
            elif isinstance(obj, Brt):
                grid[x][y] = 3  #utilizaremos el valor 3 para los brt
            # elif isinstance(obj, Automovil):
            #     grid[x][y] = 4 #utilizaremos el valor 4 para los Automoviles
    return grid



#creamos clase Pasajero.
class Pasajero(Agent):
    def __init__(self, unique_id, model, pos, estacion_pos, estado, destino, velocidad):
        super().__init__(unique_id, model)
        self.pos = pos
        self.estacion_pos = estacion_pos  # Posición de la estación del pasajero
        self.estado = estado
        self.tipo = 'Pasajero'
        self.destino = destino
        self.velocidad = 1
        self.a_bordo = False


#Metodo step clase Pasajero
    def step(self):
        brt = self.model.brts[0]  #Solo deber haber un BRT en la simulacion

        #Si el BRT esta en la estacion del pasajero y la cantidad de pasajeros en pasajeros_a_bordo es menor que la capacidad del brt
        if brt.pos == self.estacion_pos and len(brt.pasajeros_a_bordo) < brt.capacidad:

            #Si el pasajero no esta en el brt inicia movimiento hacia el
            if not self.a_bordo:
                self.mover_hacia(brt.pos, self.velocidad)

                #Si el pasajero llego al brt
                if self.pos == brt.pos:
                    #apend pasjero a la lista de pasajeros a bordo
                    brt.pasajeros_a_bordo.append(self)
                    #Bandera de personaje a bordo
                    self.a_bordo = True
            else: 
                self.pos = (1,1)
        





    def mover_hacia(self, objetivo, velocidad):
        dx, dy = objetivo[0] - self.pos[0], objetivo[1] - self.pos[1]
        distancia = math.sqrt(dx**2 + dy**2)

        if distancia > 0:
            dx /= distancia
            dy /= distancia

        nueva_pos_x = int(self.pos[0] + dx * velocidad)
        nueva_pos_y = int(self.pos[1] + dy * velocidad)

        nueva_pos_x = max(0, min(self.model.grid.width - 1, nueva_pos_x))
        nueva_pos_y = max(0, min(self.model.grid.height - 1, nueva_pos_y))

        nueva_pos = (nueva_pos_x, nueva_pos_y)
        self.model.grid.move_agent(self, nueva_pos)
        self.pos = nueva_pos

#creamos clase Estacion
class Estacion(Agent):
    def __init__(self, unique_id, model, pos):
      super().__init__(unique_id, model)
      self.pos = pos
      self.tipo = 'Estacion'



# class Automovil(Agent):
#     def __init__(self, unique_id, model, pos):
#       super().__init__(unique_id, model)
#       self.pos = pos
#       self.tipo = "Automovil"
#       self.velocidad = 1

#     def step(self):
#         self.mover_hacia((50,180), self.velocidad)

#     def mover_hacia(self, objetivo, velocidad):
#         dx, dy = objetivo[0] - self.pos[0], objetivo[1] - self.pos[1]
#         distancia = math.sqrt(dx**2 + dy**2)

#         if distancia > 0:
#             dx /= distancia
#             dy /= distancia

#         nueva_pos_x = int(self.pos[0] + dx * velocidad)
#         nueva_pos_y = int(self.pos[1] + dy * velocidad)

#         nueva_pos_x = max(0, min(self.model.grid.width - 1, nueva_pos_x))
#         nueva_pos_y = max(0, min(self.model.grid.height - 1, nueva_pos_y))

#         nueva_pos = (nueva_pos_x, nueva_pos_y)
#         self.model.grid.move_agent(self, nueva_pos)
#         self.pos = nueva_pos




#creamos clase BRT
class Brt(Agent):
    def __init__(self, unique_id, model, pos):
        super().__init__(unique_id, model)
        self.tipo = 'Brt'
        self.capacidad = 30
        self.pos = pos
        self.estaciones = []
        self.estacion_actual = 0
        self.vel_movimiento = 2
        self.cont_tiempo_espera = 0
        self.tiempo_espera_maximo = 15
        self.pasajeros_a_bordo = []


#Metodo step clase BRT
# En la clase Brt
    def step(self):
        #Si aun quedan estaciones por visitar
        if self.estacion_actual < len(self.estaciones):
            #Posicion de la proxima estacion por visitar.
            estacion_objetivo = self.estaciones[self.estacion_actual]

            #Si brt no esta en la siguiente posicion inicia movimiento hacia ella.
            if self.pos != estacion_objetivo:
                self.mover_hacia(estacion_objetivo, self.vel_movimiento)
            else:
                #Si brt se encuentra en la estacion el contador empieza a aumentar 1 por step
                if self.cont_tiempo_espera < self.tiempo_espera_maximo:
                    #tiempo de espera +1
                    self.cont_tiempo_espera += 1
                else:
                    #Cuando se alcance el tiempo de espera se comienza a preparar variables para avanzar a siguiente estacion
                    self.estacion_actual += 1  #Se actualiza el indice de la estacion
                    self.cont_tiempo_espera = 0  #Se reinicia el contador a 0
        else:
            #Si todas las estaciones fueron visitadas el brt se dijire a y = 180
            if self.pos[1] < 180:
                self.mover_hacia((65, 180), self.vel_movimiento)  #Se mueve el BRT
        #print para revisar que el brt se este moviendo correctamente
        #print(self.pos)

        #Si brt esta en una estacion
        if self.pos in self.estaciones:
            # #Se recorre la lista de pasajeros a bordo
            for pasajero in self.pasajeros_a_bordo[:]:
            #     #Si el destino del pasajero es la estación actual
                if pasajero.destino == self.pos:
                    nueva_pos = (self.pos[0] + 1, self.pos[1])  # Ajustar la posición
                    pasajero.pos = nueva_pos
                    pasajero.a_bordo = False
                    if pasajero in self.pasajeros_a_bordo:
                        self.pasajeros_a_bordo.remove(pasajero)

            #         #Definicio nueva posicion para que el pasajero baje cerca de la estacion actual(destino)
            #         nueva_pos = (self.pos[0] + 1, self.pos[1])

            #         #Mover al pasajero a la nueva posicion
            #         self.model.grid.move_agent(pasajero, nueva_pos)

            #         #Actualizar la posición del pasajero
            #         pasajero.pos = nueva_pos

            #         #Bandera pasajero a bordo apagada
            #         pasajero.a_bordo = False

            #         #Quitamos al pasajero de la lista de pasajeros a bordo del BRT
            #         self.pasajeros_a_bordo.remove(pasajero)

#Metodo de BRT mover hacia
    def mover_hacia(self, objetivo, velocidad):
        dx, dy = objetivo[0] - self.pos[0], objetivo[1] - self.pos[1]
        distancia = math.sqrt(dx**2 + dy**2)

        if distancia > 0:
            dx /= distancia
            dy /= distancia

        nueva_pos_x = int(self.pos[0] + dx * velocidad)
        nueva_pos_y = int(self.pos[1] + dy * velocidad)

        nueva_pos_x = max(0, min(self.model.grid.width - 1, nueva_pos_x))
        nueva_pos_y = max(0, min(self.model.grid.height - 1, nueva_pos_y))

        nueva_pos = (nueva_pos_x, nueva_pos_y)
        self.model.grid.move_agent(self, nueva_pos)
        self.pos = nueva_pos




#creacion clase Garza_Sada
class Garza_Sada(Model):
    def __init__(self, num_pasajeros, M, N, num_estaciones, num_brt):
        super().__init__()
        self.num_pasajeros = num_pasajeros
        self.num_brt = num_brt
        self.num_estaciones = num_estaciones
        #self.num_automoviles = num_automoviles
        self.grid = MultiGrid(M, N, False)
        self.schedule = SimultaneousActivation(self)
        self.brts = []
        self.all_agent_positions = {}
#Creacion de las estaciones:
#se crean en base a la cantidad que el usuario ingrese, todas se generan sobre el eje x = 64 y el eje y se multiplica cada ves que se genere una nueva estacion, comenzando en 40-80-120...
        for i in range(int(num_estaciones)):
            x = 64
            y = 40 * (i + 1)
            pos_inicial = (x, y)
            estacion_id = f"estacion_{i}"
            estacion = Estacion(estacion_id, self, pos_inicial)
            self.grid.place_agent(estacion, pos_inicial)
            self.schedule.add(estacion)


        self.crear_pasajeros()

#creacion de los pasajeros
    def crear_pasajeros(self):
        pasajeros_por_estacion = self.num_pasajeros // self.num_estaciones
        for estacion_numero in range(self.num_estaciones):
            for i in range(pasajeros_por_estacion):
                # ango para la posición x del pasajero (59 a 62)
                x = random.randint(59, 62)

                #Base y de la estación
                base_y = 40 * (estacion_numero + 1)
                estacion_pos = (64, (40 * (estacion_numero + 1)))

                y = base_y + random.choice([0, 1, 2])

                pos_inicial = (x, y)

                #Se genera un destino aleatorio que sea una estacion adelante
                destino_estacion_numero = random.randint(estacion_numero + 1, self.num_estaciones)
                destino_y = 40 * (destino_estacion_numero + 1)
                destino = (64, destino_y)  # Posicion x del destino en la linea de la estacion

                pasajero_id = f"pasajero_{estacion_numero * pasajeros_por_estacion + i}"
                pasajero = Pasajero(pasajero_id, self, pos_inicial, estacion_pos , "esperando", destino, 1)
                self.grid.place_agent(pasajero, pos_inicial)
                self.schedule.add(pasajero)
                #print("el pasajero ", pasajero_id, "tiene como estacionPOs " ,estacion_pos, "y origen ", pos_inicial )


#creacion del unico Brt
        for i in range(self.num_brt):
            posicion_inicial = (64,10)
            Brt_id = "Brt_0"
            brt = Brt(Brt_id, self, posicion_inicial)
            
            brt.estaciones = [(64, 40 * (j + 1)) for j in range(self.num_estaciones)]  #Asigna las posiciones de las estaciones
            self.grid.place_agent(brt, posicion_inicial)
            self.schedule.add(brt)
            self.brts.append(brt)  # Guarda la referencia al BRT
            #print("referencia = ", self.brts[0])


        # for i in range(num_automoviles):
        #     x = 50
        #     y = 10 * (i + 1)
        #     pos_inicial = (x, y)
        #     Automovil_id = f"Automovil_{i}"
        #     automovil = Automovil(Automovil_id, self, pos_inicial)
        #     self.grid.place_agent(automovil, pos_inicial)
        #     self.schedule.add(automovil)



        self.datacollector = DataCollector(
            model_reporters={"Grid": get_grid}
        )


    def collect_agent_positions(self):
        agent_positions = []
        for agent in self.schedule.agents:
            if agent.pos is not None:  #Revisamos que el agente tenga una posicion
                #Se guarda una copia de la posicion, no una referencia al agente
                agent_positions.append([agent.unique_id, list(agent.pos)])
        return agent_positions

    def step(self):
        self.schedule.step()  # Actualiza todos los agentes
        self.datacollector.collect(self)

        # ecolectamos posiciones
        agent_positions = self.collect_agent_positions()
        self.all_agent_positions[str(self.schedule.steps)] = agent_positions

    def save_positions_to_file(self, filename='agent_positions.json'):
        # Guardar todas las posiciones en un archivo JSON
        with open(filename, 'w') as file:
            json.dump(self.all_agent_positions, file, indent=4)


num_pasajeros = 100
num_estaciones = 13
M = 140
N = int(40 * num_estaciones + 30)
num_brt = 1
model = Garza_Sada(num_pasajeros, M, N, num_estaciones, num_brt)


app = Flask(__name__)

@app.route("/")
def test():
    return "Home"

@app.route("/getSteps/<stepsGiven>")
def getSteps(stepsGiven):

    #num_automoviles = 3
    # Crear y ejecutar el modelo


    # Por cada paso (Este es el for loop donde se dan los pasos)
    if int(stepsGiven) < 500:
        storage = {"steps": []}
        storage.get("steps").append({"positions": []})
        storage["capacity"] = len(model.brts[0].pasajeros_a_bordo)

        # Por cada espacio en el grid
        for j in model.grid.coord_iter():
            # Si hay un agente en ese espacio
            if j[0]:
                # Por cada objeto en el grid
                for item in j:
                    # Si es un entero (su posicion)
                    if isinstance(item[0], int):
                        continue
                    # Si es un agente
                    else:
                        # Por cada agente en ese espacio
                        aux = {}
                        for x in range(len(item)):
                            # Guardar sus atributos en variable (AÑADIR AQUI VARIABLES DE AGENTE ADICIONALES)
                            if isinstance(item[x], Pasajero):
                                storage.get("steps")[0].get("positions").append({"id": item[x].unique_id, "pos": item[x].pos, "a_bordo": item[x].a_bordo})
        
                            else:
                                storage.get("steps")[0].get("positions").append({"id": item[x].unique_id, "pos": item[x].pos})

                            # # Guardar en diccionario, que tiene como llave el step
                            # if stepsGiven in storage:
                            #     storage.get("steps").append(aux)
                            # else:
                            #     storage[stepsGiven] = [aux]
            # Genera un json del diccionario con las posiciones por step
    

    # Dar siguiente step
    # jFile = json.dumps(storage, indent=4)
    # with open(f"sample{stepsGiven}.json", "w") as outfile:
    #     outfile.write(jFile)
    #     outfile.close()
    model.step()
    return jsonify(storage), 200

    all_grid = model.datacollector.get_model_vars_dataframe()

    model.save_positions_to_file()



if __name__ == "__main__":
    app.run(debug=True)
