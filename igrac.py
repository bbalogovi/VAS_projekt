#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import random
import datetime
import spade
import sys

from spade.agent import Agent
from spade.message import Message
from spade.behaviour import FSMBehaviour, State
from argparse import ArgumentParser


playerId = ""
igracAgent = ""

class Igrac(Agent):
    class IgracPonasanje(FSMBehaviour):
        async def on_start(self):
            print(f"{playerId} spreman.")

        async def on_end(self):
            await self.agent.stop()

    class UdiUIgru(State):
        async def run(self):
            msg = Message(
                to="server@localhost",
                body=igracAgent
            )
            await self.send(msg)
            self.set_next_state("CEKAJ")
    
    class CekajServer(State):
        async def run(self):
            msg = await self.receive(timeout=60)
            if (msg):
                print(f"Igra započinje - {msg.body}")
                self.set_next_state("IGRAJ")
            else:
                self.set_next_state("CEKAJ")

    class Igraj(State):
        async def run(self):
            msg = await self.receive(timeout=120)
            temp = False
            if (msg):
                body = msg.body
                print(body)
                if "Pobjednik" in body:
                    temp = True
                elif "Biraj" in body:
                    userInput = 99
                    num = body.split("[1 - ")[1].split("]")[0]
                    while (int(userInput) > int(num) or int(userInput) < 1):
                        userInput = input(f"[1 - {num}]: ")
                
                    msg = Message(
                        to="server@localhost",
                        body=userInput
                    )
                    await self.send(msg)
            
            if (temp != True):
                self.set_next_state("IGRAJ")

    async def setup(self):
        fsm = self.IgracPonasanje()

        fsm.add_state(name="UDI", state=self.UdiUIgru(), initial=True)
        fsm.add_state(name="CEKAJ", state=self.CekajServer())
        fsm.add_state(name="IGRAJ", state=self.Igraj())

        fsm.add_transition(source="UDI", dest="CEKAJ")
        fsm.add_transition(source="CEKAJ", dest="CEKAJ")
        fsm.add_transition(source="CEKAJ", dest="IGRAJ")
        fsm.add_transition(source="IGRAJ", dest="IGRAJ")

        self.add_behaviour(fsm)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("-id", type=str, help="ID igrača.")
    args = parser.parse_args()
    playerId = args.id
    igracAgent = f"{playerId}@localhost"

    igrac = Igrac(igracAgent, "password")
    igracKraj = igrac.start()
    igracKraj.result()

    while igrac.is_alive():
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            break

    igrac.stop()

    spade.quit_spade()
