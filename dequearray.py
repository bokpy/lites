#!/usr/bin/python3
from collections import deque


class Deque2dArray(deque):
	def __init__(S,rows,columns): #d2=deque([deque([0 for __ in range(0,7)]) for _ in range(0,5)])
		deque.__init__(S,[deque([0 for __ in range(0,columns)]) for _ in range(0,rows)])

def main() -> None:
    dqa=Deque2dArray(4,5)
    print(dqa)

def divide(P):
	P1=P//2
	P2=P-P1
	if P1==P2 :
		print(f'even {P:2} {P1:2} == {P2:2}')
		return
	print(f'odd  {P:2} {P1:2} == {P2:2}')


if __name__ == '__main__':
	for i in range(0,18):
		divide(i)
	#main()
