import random
import time
from typing import Set

from mpi4py import MPI

comm = MPI.COMM_WORLD

class Philosopher:
    def __init__(self, rank, size):
        self._rank = rank
        self._size = size
        self._left_neighbor = (rank - 1 + size) % size
        self._right_neighbor = (rank + 1) % size
        self._has_left_fork = rank < self._left_neighbor
        self._has_right_fork = rank < self._right_neighbor
        self._left_fork_dirty = True
        self._right_fork_dirty = True
        self._requests = set()

    def request_forks(self):
        while not self._has_left_fork and not self._has_right_fork:
            if not self._has_left_fork:
                self.request_fork(self._left_neighbor)
                self.wait(self._left_neighbor)
            if not self._has_right_fork:
                self.request_fork(self._right_neighbor)
                self.wait(self._right_neighbor)

    def request_fork(self, neighbor):
        print("  " * self._rank + f"[Philosopher {self._rank}]: Requesting fork from philosopher {neighbor}")
        comm.send(self._rank, dest=neighbor, tag=0)

    def wait(self, fork_id):
        if fork_id == self._left_neighbor:
            while not self._has_left_fork:
                self.process_messages()
                time.sleep(0.5)
        elif fork_id == self._right_neighbor:
            while not self._has_right_fork:
                self.process_messages()
                time.sleep(0.5)

    def handle_request(self, source):
        if source == self._left_neighbor:
            if self._has_left_fork and self._left_fork_dirty:
                self.send_fork(source)
            elif self._has_left_fork and not self._left_fork_dirty:
                self._requests.add(source)
                print("  " * self._rank + f"[Philosopher {self._rank}]: Request for fork from philosopher {source}")
            elif not self._has_left_fork:
                self._requests.add(source)
                print("  " * self._rank + f"[Philosopher {self._rank}]: Request for fork from philosopher {source}")

        elif source == self._right_neighbor:
            if self._has_right_fork and self._right_fork_dirty:
                self.send_fork(source)
            elif self._has_right_fork and not self._right_fork_dirty:
                self._requests.add(source)
                print("  " * self._rank + f"[Philosopher {self._rank}]: Got request for fork from philosopher {source}")
            elif not self._has_right_fork:
                self._requests.add(source)
                print("  " * self._rank + f"[Philosopher {self._rank}]: Got request for fork from philosopher {source}")

    def send_fork(self, neighbor):
        print("  " * self._rank + f"[Philosopher {self._rank}]: Sending fork to philosopher {neighbor}")
        if neighbor == self._left_neighbor:
            self._has_left_fork = False
            self._left_fork_dirty = True
        elif neighbor == self._right_neighbor:
            self._has_right_fork = False
            self._right_fork_dirty = True
        comm.send(self._rank, dest=neighbor, tag=1)

    def receive_fork(self, source):
        if source == self._left_neighbor:
            self._left_fork_dirty = False
            self._has_left_fork = True
            print("  " * self._rank + f"[Philosopher {self._rank}]: Received left fork from philosopher {source}")

        elif source == self._right_neighbor:
            self._right_fork_dirty = False
            self._has_right_fork = True
            print("  " * self._rank + f"[Philosopher {self._rank}]: Received right fork from philosopher {source}")

    def eat(self):
        if not self._has_left_fork and not self._has_right_fork:
            self.request_forks()
        eat_time = random.randint(1, 3)
        print("  " * self._rank + f"[Philosopher {self._rank}]: Eating")
        time.sleep(eat_time)
        self._left_fork_dirty = self._right_fork_dirty = True
        print("  " * self._rank + f"[Philosopher {self._rank}]: Finished eating")

    def think(self):
        thinking_time: int = random.randint(1, 3)
        print("  " * self._rank + f"[Philosopher {self._rank}]: Thinking")
        end_time: float = time.time() + thinking_time
        while time.time() < end_time:
            self.process_messages()
            time.sleep(0.5)

    def check_requests(self):
        for request in self._requests:
            if request == self._left_neighbor and self._left_fork_dirty:
                self.send_fork(request)
            elif request == self._right_neighbor and self._right_fork_dirty:
                self.send_fork(request)
        self._requests.clear()

    def process_messages(self):
        status = MPI.Status()
        while comm.Iprobe(source=MPI.ANY_SOURCE, tag=MPI.ANY_TAG, status=status):
            source = status.Get_source()
            tag = status.Get_tag()
            message = comm.recv(source=source, tag=tag)
            if tag == 0:
                self.handle_request(source)
            elif tag == 1:
                self.receive_fork(source)

    def run(self):
        while True:
            self.think()
            self.request_forks()
            self.eat()
            self.check_requests()
            time.sleep(1)

if __name__ == "__main__":
    rank = comm.Get_rank()
    size = comm.Get_size()

    philosopher = Philosopher(rank=rank, size=size)
    philosopher.run()