#!/usr/bin/python3

import subprocess
import json

DEBUGEXIT=exit
DEBUGPRINT=print

def DEBUG_SHOW_INT_ARRAY(a,title=''):
	print(title)
	for r in a:
		for i in r:
			if isinstance(i,int):
				if abs(i) > 1000:
					print(f'{i//1000:5}k',end='')
					continue
				print(f'{i:6}',end='')
				continue
			print(f'{i}',end='')
		print()

def SHOWFRAME(x, y=0, width=0, height=0,pend='\n'):
	if not isinstance(x,int):
		x,y, width, height = x
	print (f'X({x:4}) Y({y:4}) W({width:4}) H({height:4})',end=pend)

def JDUMP(dct,title=''):
	jd=json.dumps(dct,indent=4)
	if(title): print(title)
	print(f'{jd}')

def try_int(val):
	try:
		return int(val)
	except ValueError:
		return val.strip()

def service_call(*args):
	try:
		info = subprocess.check_output(args)
	except subprocess.SubprocessError as e:
		print(f'{args} failed')
		print(f'subprocess.SubprocessError {e}')
		return None
	str_info=info.decode('utf-8')
	return str_info.splitlines()

def main() -> None:
	pass


if __name__ == '__main__':
	main()
