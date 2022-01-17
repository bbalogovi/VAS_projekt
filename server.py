#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import random
import datetime
import pickle

import spade
from spade.agent import Agent
from spade.message import Message
from spade.behaviour import FSMBehaviour, State


kartice = ["A", "A", "B", "B", "C", "C", "D", "D", "E", "E", "F", "F", "G", "G"]
poznateKartice = ["-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-"]
igraci = []
rezultat = [0, 0]
trenutnoIgra = 0

class Server(Agent):
    class ServerPonasanje(FSMBehaviour):
        async def on_start(self):
            print(f"Server spreman.")

        async def on_end(self):
            print(f"Igra je završena.")

    class CekajIgrace(State):
        async def run(self):
            msg = await self.receive(timeout=120)
            if (msg):
                igraci.append(msg.body)

                if (len(igraci) == 2):
                    print("Igra ide u fazu pripreme.")

                    random.shuffle(kartice)
                    print(kartice)

                    for player in igraci:
                        msg = Message(
                            to=player,
                            body=str(poznateKartice)
                        )
                        await self.send(msg)

                    self.set_next_state("IGRAJ")
                else:
                    self.set_next_state("CEKAJ")
            else:
                self.set_next_state("CEKAJ")
            
    class Igraj(State):
        async def run(self):
            global trenutnoIgra

            if (len(poznateKartice) > 0):
                msg = Message(
                    to=igraci[trenutnoIgra],
                    body=f"Tvoj red za igranje. Biraj karticu za okretanje [1 - {len(poznateKartice)}].\nPoznate kartice - {str(poznateKartice)}"
                )
                await self.send(msg)

                indeks1 = 0
                indeks2 = 0

                msg = await self.receive(timeout=120)
                if (msg):
                    indeks1 = int(msg.body) - 1
                    if poznateKartice[indeks1] == "-":
                        poznateKartice[indeks1] = kartice[indeks1]
                    msg = Message(
                        to=igraci[trenutnoIgra],
                        body=f"Tvoj red za igranje (još jednom). Biraj karticu za okretanje [1 - {len(poznateKartice)}].\nPoznate kartice - {str(poznateKartice)}"
                    )
                    await self.send(msg)
                else:
                    self.set_next_state("IGRAJ")

                msg = await self.receive(timeout=120)
                if (msg):
                    indeks2 = int(msg.body) - 1
                    if poznateKartice[indeks2] == "-":
                        poznateKartice[indeks2] = kartice[indeks2]
                    msg = Message(
                        to=igraci[trenutnoIgra],
                        body=f"Poznate kartice - {str(poznateKartice)}"
                    )
                    await self.send(msg)

                    if poznateKartice[indeks1] == poznateKartice[indeks2]:
                        znak = poznateKartice[indeks1]
                        for i in range(0, 2):
                            poznateKartice.remove(znak)
                            kartice.remove(znak)
                        rezultat[trenutnoIgra] += 1
                    else:
                        trenutnoIgra = 1 if trenutnoIgra == 0 else 0

                    if (len(poznateKartice) == 0):
                        pobjednik = 0 if rezultat[0] > rezultat[1] else 1
                        for player in igraci:
                            msg = Message(
                                to=player,
                                body=f"Pobjednik je {igraci[pobjednik]}."
                            )
                            await self.send(msg)
                        print("Igra je gotova.")
                    else:
                        self.set_next_state("IGRAJ")
                else:
                    self.set_next_state("IGRAJ")

    async def setup(self):
        fsm = self.ServerPonasanje()

        fsm.add_state(name="CEKAJ", state=self.CekajIgrace(), initial=True)
        fsm.add_state(name="IGRAJ", state=self.Igraj())

        fsm.add_transition(source="CEKAJ", dest="CEKAJ")
        fsm.add_transition(source="CEKAJ", dest="IGRAJ")
        fsm.add_transition(source="IGRAJ", dest="IGRAJ")

        self.add_behaviour(fsm)


if __name__ == '__main__':
    server = Server("server@localhost", "password")
    serverEnd = server.start()
    serverEnd.result()

    while server.is_alive():
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            break

    server.stop()
    spade.quit_spade()
