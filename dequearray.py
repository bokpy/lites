#!/usr/bin/python3
from collections import deque


class Deque2dArray(deque):
	def __init__(S,rows,columns): #d2=deque([deque([0 for __ in range(0,7)]) for _ in range(0,5)])
		deque.__init__(S,[deque([0 for __ in range(0,columns)]) for _ in range(0,rows)])

def main() -> None:
    dqa=Deque2dArray(4,5)
    print(dqa)


if __name__ == '__main__':
	main()
