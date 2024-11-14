#!/usr/bin/python3
import subprocess
from collections import deque
import re

from services import DEBUGPRINT

pseudo_toss=deque([56, 22, 60, 71, 50, 66, 90, 0, 26, 64, 98, 14, 12, 8, 73, 4, 7, 45, 0, 36, 76, 4, 85, 42, 65, 67, 66, 23, 11, 67, 56, 27, 77, 39, 0, 27, 9, 53, 72, 82, 50, 18, 15, 74, 69, 55, 71, 18, 48, 21, 2, 73, 67, 32, 44, 12, 35, 44, 61, 4, 0, 33, 62, 98, 79, 76, 83, 73, 39, 40, 20, 42, 15, 59, 95, 40, 20, 27, 40, 36, 14, 41])
def somewhat_random():
	for _ in range(0,3):
		val=pseudo_toss.pop()
		pseudo_toss.appendleft(val)
		#DEBUGPRINT(f'somewhat_random {val}')
	return val

#B=4 # border width
def squared_distance(x0,y0,x1,y1):
	dx=x0-x1 ; dy=y0-y1
	return dx*dx + dy*dy

#Id_re     =r'Window id: *(0x\d+)'
AulX_re     =r'Absolute upper-left X: *(\d+)'
AulY_re     =r'Absolute upper-left Y: *(\d+)'
Width_re    =r'Width: *(\d+)'
Height_re   =r'Height:*(\d+)'
Xwin_re     ='|'.join([AulX_re,AulY_re,Width_re,Height_re])
Re_Xwin     =re.compile(Xwin_re,re.MULTILINE)
Re_Number   =re.compile(r'\D*(\d+)$')

def service_call(*args):
	try:
		info = subprocess.check_output(args)
	except subprocess.SubprocessError as e:
		print(f'{args} failed')
		print(f'subprocess.SubprocessError {e}')
		return None
	str_info=info.decode('utf-8')
	return str_info.splitlines()

# xdotool getwindowgeometry 121634861
# Window 121634861
# Position: 4436,341 (screen: 0)
# Geometry: 601x282

Re_Position=re.compile(r'\s*Position:\D*(\d+),(\d+).*')
Re_Geometry=re.compile(r'\s*Geometry:\D*(\d+)x(\d+).*')

def xdotool_frame(id):
	lines=service_call("xdotool","getwindowgeometry",str(id))
	# for i,line in zip(range(0,10),lines):
	# 	DEBUGPRINT(f'{i:2} "{line}"')
	position=Re_Position.match(lines[1])
	geometry=Re_Geometry.match(lines[2])
	xu=int(position.group(1))
	yu=int(position.group(2))
	w =int(geometry.group(1))
	h =int(geometry.group(2))
	return WindowFrame(xu,yu,w,h,True)

def xwininfo_frame(id)->"WindowFrame":
	def extract_number(string):
		#DEBUGPRINT(f'extract_number("{string }") ')
		num=Re_Number.match(string)
		# if not num:
		# 	print(f'"{string }" with no number.')
		# 	DEBUGEXIT(0)
		return int(num.group(1))

	#DEBUGPRINT(f'<--- xwininfo({id}) --->')
	lines=service_call("xwininfo", "-id", str(id))
	# for i in range(0,8):
	# 	DEBUGPRINT(f'{i:2} "{lines[i]}"')
	xu=extract_number(lines[3])
	yu=extract_number(lines[4])
	w =extract_number(lines[7])
	h =extract_number(lines[8])
	#DEBUGPRINT(f'{xu=} {yu=} {w =} {h =}')
	# DEBUGPRINT(grps)
	return WindowFrame(xu,yu,w,h,True)

def xwininfo_tree_ids():
	ids=deque()
	re_id=re.compile(r'([0-9]{5,})')
	lines=service_call("xwininfo","-int","-root","-tree")
	for line in lines:
		if '(has no name):' in line :
			continue
		id_list=re_id.findall(line)
		if not id_list:
			continue
		ids.append(int(id_list[0]))
	return ids

geometry_re=re.compile(r'\D*(\d+)x(\d+)(.\d+).(.\d+).*')
def xwininfo_geometry(id):
	#-geometry 1076x1305+1178--58
	for line in service_call("xwininfo", "-id", str(id)):
		if '-geometry' in line:
			break
	match=geometry_re.match(line)
	return [int(x) for x in match.groups()]

def xwininfo_corners(id):
	for line in service_call("xwininfo", "-id", str(id)):
		if 'Corners:' in line:
			return parse_xwininfo_corners(line)

# 	match=geometry_re.match(line)
# 	return [int(x) for x in match.groups() ]
corner_re=re.compile(r"([-+]?\d+)([-+]\d+)")
def parse_xwininfo_corners(corners_string):
	matches =corner_re.findall(corners_string)
	DEBUGPRINT(f'{matches=}')	# Extract each corner's coordinates as (x, y) tuples
	X0 = int(matches[0][0])
	Y0 = int(matches[0][1])
	X1 = int(matches[1][0])
	Y1 = int(matches[1][1])
	return X0,Y0,X1,Y1

# # Example usage
# xwininfo_output = "Corners:  +3466+23  -26+23  -26-29  +3466-29"
# upper_left, lower_right = parse_xwininfo_corners(xwininfo_output)
#
# print(f"Upper Left: {upper_left}")
# print(f"Lower Right: {lower_right}")


#re_region=re.compile(r'^_NET_WM_OPAQUE_REGION\(CARDINAL\) =\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+).*')
re_region  = re.compile(r'^_NET_WM_OPAQUE_REGION\D*(\d+)\D*(\d+)\D*(\d+)\D*(\d+).*')

re_frame=re.compile(r'^(_NET_FRAME_EXTENTS|WM_CLASS)')
def xprop_tree_xwins():
	ids=deque()
	re_id=re.compile(r'([0-9]{5,})')
	for line in service_call("xwininfo","-int","-root","-tree"):
		if '(has no name):' in line :
			continue
		id_list=re_id.findall(line)
		if not id_list:
			continue
		ids.append(int(id_list[0]))
	return ids

re_extents = re.compile(r'.*FRAME_EXTENTS\(CARDINAL\) =\D*(\d+)\D*(\d+)\D*(\d+)\D*(\d+).*')
def xprop_borders(id):
	borders=[0,0,0,0]
	for line in service_call("xprop","-len","128","-id",str(id)):
		frame_extents=re_extents.match(line)
		if frame_extents:
			#DEBUGPRINT(f'{line}\n{frame_extents.groups()}')
			brims=[int(value) for value in frame_extents.groups()]
			for brim,border in zip(brims,borders):
				if brim > border:
					borders=brims
	#DEBUGPRINT(f'return {borders}\n')
	return borders

def xprop_in_view(id):
	"""
	test the visibility of a X11 window
	:param id: id of the window
	:return: the number of the desktop that displays the window when visible else -1
	"""
	desk=-1
	for line in service_call("xprop","-len","128","-id",str(id)):
		if '_NET_WM_STATE_HIDDEN' in line:
			return -1
		if '_NET_WM_DESKTOP(CARDINAL)'  in line:
			equal=line.rfind('=')
			desk=int(line[equal+1:])
			if (desk < 0) or (desk>32):
				return -1
	return desk

def xprop_show(id,prop=None):
	if not prop:
		print(f'xprop_show({id}):')
	i=-1
	for line in service_call("xprop","-len","128","-id",str(id)):
		i+=1
		if not prop:
			print(f'{i:4}:"{line}"')
			continue
		if prop in line:
			print(f'{id:10} {i:4}:"{line}"')
	if not prop:
		print(f'end xprop_show({id}):')

miniX=0 # X Upper Left
miniY=1 # Y Upper Left
maxiX=2 # X Lower Rigth
maxiY=3 # Y Lower Rigth

def square_distance(ax,ay,bx,by):
	dx=ax-bx
	dy=ay-by
	return dx*dx+dy*dy

def manhattan_distance(ax,ay,bx,by):
	return abs(ax-bx)+abs(ay-by)

def between(lo,mid,hi):
	return (lo<=mid) and (hi>=mid)

class WindowFrame(list):
	def __init__(S,x0,y0=None,x1=None,y1=None,xywh=False):
		#list.__init__(S,[0,0,0,0])
		if xywh:
			if isinstance(y1,int):
				list.__init__(S,[x0,y0,x0+x1,y0+y1])
				return
			else:
				x0,y0,w,h=x0
				list.__init__(S,[x0,y0,x0+w,y0+h])
			return
		if isinstance(y1,int):
			list.__init__(S,[x0,y0,x1,y1])
			return
		list.__init__(S,list(x0))

	def set(S,*args):
		if isinstance(args[0],int):
			for i in range(0,4):
				S[i]=args[i]
			return
		for i in range(0,4):
			S[i]=args[0][i]

	def __str__(S):
		x0,y0,x1,y1=S
		return f'[{x0:5},{y0:5}][{x1:5},{y1:5}]'

	def points_str(S):
		return f'{S[0]:4},{S[1]:4},{S[2]:4},{S[3]:4}'

	def corners(S):
		x0,y0,x1,y1=S
		return x0,y0,x1,y0,x1,y1,x1,y1

	# def difference(S,realsize):
	# 	#DEBUGPRINT(f'difference {str(S)}')
	# 	#DEBUGPRINT(f'           {str(realsize)}')
	# 	ret = [Q-P for Q,P in zip(S,realsize)]
	# 	#DEBUGPRINT(f'           {ret}')
	# 	return [Q-P for Q,P in zip(S,realsize)]

	def duplicate(S):
		return WindowFrame(S)

	def shrink(S,pixels):
		SminX,SminY,SmaxX,SmaxY=S
		S.set(SminX+pixels,SminY+pixels,SmaxX-pixels,SmaxY-pixels)

	def grow(S,pixels):
		S.shrink(-pixels)

	def subtract_panel(S,panel):
		if not S.common_area(panel):
			return
		w,h=panel.width_heigth()
		Sx0,Sy0,Sx1,Sy1=S
		Ox0,Oy0,Ox1,Oy1=panel
		if w > h: # horizontal
			if Sy0==Oy0: # top horizontal
				S[1]=Oy1
				return
			S[3]=Oy0
			return
		# vertical
		if Sx0==Ox0: # Left
			S[0]=Ox1
			return
		S[2]=Ox0

	# def subtract_panel(S,panel):
	# 	if not S.common_area(panel):
	# 		return
	# 	#DEBUGPRINT(f'S     {str(WindowFrame(S))}')
	# 	w,h=panel.width_heigth()
	# 	#DEBUGPRINT(f'panel {str(panel)} {w:4} {h:4}')
	#
	# 	SminX,SminY,SmaxX,SmaxY=S
	# 	T___X,T___Y,B___X,B___Y=panel
	# 	if w > h: # horizonal panel
	# 		if between(T___Y,SminY,B___Y): # top panel
	# 			S.set(SminX,B___Y,SmaxX,SmaxY)
	# 			return
	# 		if between(T___Y,SmaxY,B___Y): # bottom panel
	# 			S.set(SminX,SminY,SmaxX,T___Y)
	# 			return
	# 	if between(T___X,SminX,B___X): # left panel
	# 		S.set(B___X,SminY,SmaxX,SmaxY)
	# 		return
	# 	if between(T___X,SmaxX,B___X): # right panel
	# 		S.set(SminX,SminY,T___X,SmaxY)
	# 		return

	def holds(S,x,y):
		Sx0,Sy0,Sx1,Sy1=S
		if x < Sx0 or x > Sx1: return False
		if y < Sy0 or y > Sy1: return False
		return True

	def manhattan_distance(S,O):
		Sx0,Sy0,Sx1,Sy1=S
		Ox0,Oy0,Ox1,Oy1=O
		return manhattan_distance(Sx0,Sy0,Ox0,Oy0) + manhattan_distance(Sx1,Sy1,Ox1,Oy1)

	def divide_width(S):
		#DEBUGPRINT (f'divide_width')
		#DEBUGPRINT (f'org   : {str(S)}')
		ominx,ominy,omaxx,omaxy=S
		x_sum=ominx+omaxx
		xmidmin=x_sum//2
		xmidmax=x_sum-xmidmin
		S.set(xmidmax,ominy,omaxx,omaxy)
		ret = WindowFrame(ominx,ominy,xmidmin,omaxy)
		#DEBUGPRINT (f'org/2 : {str(S)}')
		#DEBUGPRINT (f'ret/2 : {str(ret)}')
		return ret

	def divide_heigth(S):
		#DEBUGPRINT (f'divide_heigth')
		#DEBUGPRINT (f'org   : {str(S)}')
		ominx,ominy,omaxx,omaxy=S
		y_sum=ominy+omaxy
		ymidmin=y_sum//2
		ymidmax=y_sum-ymidmin
		S.set(ominx,ominy,omaxx,ymidmin)
		ret = WindowFrame(ominx,ymidmax,omaxx,omaxy)
		#DEBUGPRINT (f'org/2 : {str(S)}')
		#DEBUGPRINT (f'ret/2 : {str(ret)}')
		return ret

	def frame_divide(S, parts):
		pieces = []

		def divide(frame, P):
			P1 = P // 2
			P2 = P - P1
			# DEBUGPRINT(f'{P=:<2}{P1=:<2}{P2=:<2}')
			if P < 1:
				return
			if P == 1:
				# DEBUGPRINT('Append')
				pieces.append(frame)
				return
			w, h = frame.width_heigth()
			# this is gold 89 55
			if w * 5 < h * 6:
				half = frame.divide_heigth()
			else:
				half = frame.divide_width()
			divide(frame, P1)
			divide(half, P2)

		frame = S.duplicate()
		divide(frame, parts)
		if len(pieces) != parts:
			raise RuntimeError(f'frame_divide({parts=}) made {len(pieces)} parts')
		# DEBUGPRINT(f'frame_divide({parts=}) made {len(pieces)} parts')
		return pieces

	def ratio_divide(S, parts):
		pieces = []
		def divide(frame, P):
			if P < 1:
				return
			if P == 1:
				# DEBUGPRINT('Append')
				pieces.append(frame)
				return
			P1 = P // 2
			P2 = P - P1
			w, h = frame.width_heigth()
			if P1 == P2: # even parts divide in two
			# DEBUGPRINT(f'{P=:<2}{P1=:<2}{P2=:<2}')
				if w < h :
					half = frame.divide_heigth()
				else:
					half = frame.divide_width()
			else: # odd parts divide 1 : 2 ratio
				# P2 > P1
				ominx,ominy,omaxx,omaxy=frame
				splitXmid = ( w*P2 //P)  + ominx
				splitYmid = ( h*P2 //P)  + ominy
				if squared_distance(ominx,ominy,splitXmid,omaxy) > squared_distance(ominx,ominy,omaxx,splitYmid):
					# horizontal split gives the shortest diagonal is prefered
					frame.set(ominx,ominy,omaxx,splitYmid)
					half = WindowFrame(ominx,splitYmid+1,omaxx,omaxy)
				else:
					frame.set(ominx,ominy,splitXmid,omaxy)
					half = WindowFrame(splitXmid+1,ominy,omaxx,omaxy)

			divide(frame, P2)
			divide(half, P1)

		frame = S.duplicate()
		divide(frame, parts)
		if len(pieces) != parts:
			raise RuntimeError(f'frame_divide({parts=}) made {len(pieces)} parts')
		# DEBUGPRINT(f'frame_divide({parts=}) made {len(pieces)} parts')
		return pieces

	def size(S):
		w,h=S.width_heigth()
		return w*h

	def width_heigth(S):
		x1,y1,x2,y2=S
		return x2-x1,y2-y1

	def x_y_width_heigth(S):
		x1,y1,x2,y2=S
		return x1,y1,x2-x1,y2-y1

	# def common_area(S,O:"WindowFrame")->"WindowFrame":
	# 	Slux,Sluy,Srlx,Srly=S
	# 	Olux,Oluy,Orlx,Orly=O
	#
	# 	# Determine the edges of the overlapping region
	# 	left_edge   = max(Slux,Olux)
	# 	right_edge  = min(Srlx,Orlx)
	# 	top_edge    = max(Sluy,Oluy)
	# 	bottom_edge = min(Srly,Orly)
	#
	# 	# Calculate the width and height of the overlap
	# 	overlap_width  = right_edge - left_edge
	# 	overlap_height = bottom_edge - top_edge
	# 	# Check if there is an overlap
	# 	if overlap_width <= 0 or overlap_height <= 0:
	# 		return None  # No overlap
	# 	return WindowFrame(left_edge,top_edge,right_edge,bottom_edge )

	def common_area(S,O:"WindowFrame")->int:
		Slux,Sluy,Srlx,Srly=S
		Olux,Oluy,Orlx,Orly=O

		# Determine the edges of the overlapping region
		left_edge   = max(Slux,Olux)
		right_edge  = min(Srlx,Orlx)
		top_edge    = max(Sluy,Oluy)
		bottom_edge = min(Srly,Orly)

		# Calculate the width and height of the overlap
		overlap_width  = right_edge - left_edge
		overlap_height = bottom_edge - top_edge
		# Check if there is an overlap
		if overlap_width <= 0 or overlap_height <= 0:
			return 0  # No overlap
		# Calculate the area of the overlapping region
		return overlap_width * overlap_height

def group_by_common_area(herders,flok):
	count=len(herders)
	range_herders=range(0,count)
	pen = [ [] for _ in range_herders]
	#pen= [[]]*count
	for sheep in flok:
		best_herder=-1
		best_pasture=-1
		for herder,i in zip(herders,range_herders):
			pasture=herder.common_area(sheep)
			if pasture > best_pasture:
				best_herder=i
				best_pasture=pasture
		pen[best_herder].append(sheep)
		#DEBUGPRINT(f'herder {best_herder} gets {sheep}')
	return pen

def make_match_in_hell(virgins,suitors):
	marriages=[]
	for bride, groom in zip(virgins,suitors):
		couple=Lite(bride.get_id(),bride.get_desktop(),groom)
		marriages.append(couple)
	return marriages

def make_match_in_heaven(virgins,suitors):
	VIRGIN=0 ; SUITOR=1 ; DOWRY = 2
	lo=len(virgins) ; ln=len(suitors)
	if lo!=ln:
		raise ValueError ('best_match "virgins" and "suitors" must come in equal numbers.')
	genesis=[]
	for virgin in virgins:
		for suitor in suitors:
			dowry=virgin.common_area(suitor)
			genesis.append((virgin,suitor,dowry))
	genesis.sort(key=lambda tup: -tup[DOWRY])
	#DEBUGPRINT(f'{genesis=}')
	heaven=deque(genesis)
	paradise=deque()
	#DEBUGPRINT(f'{heaven=}')
	while True:
		pair=heaven.pop()
		paradise.append(Lite(pair[VIRGIN].get_id(),pair[VIRGIN].get_desktop(),pair[SUITOR]))
		if not heaven:
			return paradise
		new_heaven=deque()
		bride=pair[VIRGIN]
		groom=pair[SUITOR]
		for single_pair in heaven:
			if bride == single_pair[VIRGIN]:
				continue
			if groom == single_pair[SUITOR]:
				continue
			new_heaven.append(single_pair)
		heaven=new_heaven

def make_match_in_manhattan(virgins,suitors):
	"""
	Find each "virgin" a "suitor" clossed arround the corner.
	"dowry" is the manhattan distance = virgin(left,top) to suitor(left,top) + virgin(right,bottom) to suitor(right,bottom)
	modern times small "dowry" best match.
	:param virgins: lites on display on a desktop screen
	:param suitors: frames dividing the screen
	:return: list of best matches best
	"""
	VIRGIN=0 ; SUITOR=1 ; DOWRY = 2
	lo=len(virgins) ; ln=len(suitors)
	if lo!=ln:
		raise ValueError ('best_match "virgins" and "suitors" must come in equal numbers.')

	# calculate the "dowry" for each possible pair
	genesis=[]
	for virgin in virgins:
		for suitor in suitors:
			# somewhat_random() as tie breaker for windows that overlap exactly.
			dowry=virgin.manhattan_distance(suitor)+somewhat_random()
			genesis.append((virgin,suitor,dowry))
	genesis.sort(key=lambda tup: -tup[DOWRY])
	#DEBUGPRINT(f'{genesis=}')
	heaven=deque(genesis)
	paradise=deque()
	#DEBUGPRINT(f'{heaven=}')
	while heaven:
		pair=heaven.pop()
		paradise.append(Lite(pair[VIRGIN].get_id(),pair[VIRGIN].get_desktop(),pair[SUITOR]))
		if not heaven:
			break
		# remove the losing matches with the "virgin" or "suitor" of the happy couple
		batchelors=deque()
		while heaven:
			pair_of_singles=heaven.pop()
			if (pair_of_singles[VIRGIN] == pair[VIRGIN]) or (pair_of_singles[SUITOR] == pair[SUITOR]):
				continue
			batchelors.appendleft(pair_of_singles)
		heaven=batchelors
	return paradise

class Lite(WindowFrame):
		# S.id='0x01800003'
		# S.desk=int()
		# frame=xwininfo(id)
		# WindowFrame.__init__(S,frame)
	def __init__(S,*args):
		if isinstance(args[0],str):
			l=args[0]
			# 0x01800003 -1 69   0    3302 65
			# 012345678901234567
			S.id  =int(l[:10],16)
			S.desk=int(l[11:13])
			n=14
			ux=int(l[n:n+4])
			n+=5
			uy=int(l[n:n+4])
			n+=5
			lx=ux+int(l[n:n+4])
			n+=5
			ly=uy+int(l[n:n+4])
		elif isinstance(args[0],int):
			S.id  = args[0]
			S.desk= args[1]
			if isinstance(args[2],WindowFrame):
				ux,uy,lx,ly=args[2]
		else:
			ux,uy,lx,ly=args[3],args[4],args[5],args[6]
		borders=xprop_borders(S.id)
		#DEBUGPRINT(f'Borders {borders}')
		WindowFrame.__init__(S,ux,uy,lx,ly)

	def __str__(S):
		sid=f'{S.id:#08x}'[5:]
		return f'Lite [{sid}]@[{S.desk:1}] {str(WindowFrame(S))}'
		#return f'Lite [{S.id:#08x}]@[{S.desk:1}] {str(WindowFrame(S))}'

	def __repr__(S):
		# 0x03e0003e  1 3440 0    3440 1440
		a,b,c,d=S
		w=c-a ; h = d-b
		return f'Lite("{S.id:#08x} {S.desk:2} {a:4} {b:4} {w:4} {h:4}")'

	def get_id(S):
		return S.id

	def get_desktop(S):
		return S.desk

	def get_frame(S):
		return WindowFrame.S

	def is_lit_on(S,desktop):
		if desktop != S.desk:
			return False
		if xprop_in_view(S.id)<0:
			return False
		return True

	def place(S):
		DEBUGPRINT(f'\nplace {S.points_str()}')
		# wmctrl -i -r 0x0340003e -e '0,3500,100,500,700'
		east,west,north,south=xprop_borders(S.id)
		x, y, w, h = S.x_y_width_heigth()
		x+=east
		y+=north
		w-=(east+west)
		h-=(north+south)
		DEBUGPRINT(f'at [{x:4},{y:4}] {w:4}x{h:4} after border correction.')
		service_call('wmctrl','-i', '-r',str(S.id), '-e', f"0,{x},{y},{w},{h}" )
		dX0,dY0,dX1,dY1=xwininfo_corners(S.id)
		# DEBUGPRINT(f'{S.points_str()} was wanted.')
		DEBUGPRINT(f'Corner delta {dX0=},{dY0=},{dX1=},{dY1=}.')
		a,b,s,t=xwininfo_geometry(S.id)
		DEBUGPRINT(f'geometry:{ a=},{b=},{s=},{t=}' )
		correct=False
		if s < 0:
			correct=True
			x=x+s
		if t < 0:
			correct=True
			y=y+t
		if correct:
			service_call('wmctrl','-i', '-r',str(S.id), '-e', f"0,{x},{y},{w},{h}" )
		# if dY1 < 0:
		# 	DEBUGPRINT(f'corection {dY1=}')
		# 	service_call('wmctrl','-i', '-r',str(S.id), '-e', f"0,{x},{y+dY1},{w},{h}" )

#-geometry 1076x1305+1178--58
class Monitor(WindowFrame):
	count=-1
	def __init__(S,name,x,y,w,h):
		WindowFrame.__init__(S,x,y,w,h,xywh=True)
		S.myname=name
		S.count+=1

	def __str__(S):
		x0,y0,x1,y1=S
		return f'{S.myname:10} {S.count:2}[{x0:4},{y0:4}],[{x1:4},{y1:4}]'

	def name(S):
		return S.myname

def xrandr_monitors()->list:
	monitor_regex = re.compile(r'(\S+) connected.*? (\d+)x(\d+)\+(\d+)\+(\d+)')
	screens=[]
	for line in service_call("xrandr"):
		match = monitor_regex.search(line)
		if match:
			monitor, width, height, x_offset, y_offset = match.groups()
			#DEBUGPRINT(f'{monitor=},{ width=},{ height=},{ x_offset=},{ y_offset=}')
			screens.append(Monitor(monitor,int(x_offset),int(y_offset),int(width),int(height)))
	return screens

class Lunettes:
	def __init__(S):
		S.screens=xrandr_monitors()
		S.lites=S.list_lites() # list_lites skips the root desktop
		#S.show_screens()
		panels=[panel for panel in S.lites if panel.desk < 0] # displayed on all screen leave them alone
		for screen in S.screens:
			for panel in panels:
				#DEBUGPRINT(f'{str(screen)} minus {panel} ')
				screen.subtract_panel(panel)
				#DEBUGPRINT(f'result {str(screen)}\n')
		#DEBUGPRINT(str(S))

	def __str__(S):
		ret=f'Lunettes {len(S.screens)}'
		for s in S.screens:
			ret+=','+str(s)
		return ret

	def monitor(S,i):
		return S.screens[i]

	def show_screens(S):
		for screen in S.screens:
			print(str(screen))

	def show_lites(S):
		for lite in S.lites:
			print(str(lite))

	def _show_array(S, a, title='Lunettes:array'):
		print(f'{title}:')
		l = len(a[0])
		column = [0 for _ in range(0, l + 1)]
		# print(f'{column=}')
		for l in a:
			pos = 0
			for j in l:
				# print(f'{j=}, {pos=}')
				j=str(j)
				lngt = len(j)
				if lngt > column[pos]:
					column[pos] = lngt
				pos += 1
		
		for l in a:
			pos = 0
			for j in l:
				width = column[pos] + 1
				print(f'{str(j):>{width}}', end='')
				pos += 1
			print()
		print()
	
	def _array(S, datastring, fields=0):
		def to_int(x):
			try:
				return int(x)
			except ValueError:
				return x

		ret = []
		lines = datastring.split('\n')
		# print(f'{lines=}')
		for line in lines:
			if line:
				clean = [to_int(x) for x in line.split(' ') if x]

				if fields:
					ret.append(clean[:fields])
					continue
				ret.append(clean)
		return ret
	
	def list_lites(S):
		"""
		Create a the list of Lites on all screen(s).
		Except the "Desktop"
		:return: list of Lites
		"""
		#DEBUGPRINT('list_windows')
		# 0x01a0009c -1 0    0    6880 1440 Morfine Desktop
		lines = service_call('wmctrl','-l', '-G')
		return [Lite(lt) for lt in lines if not ((' -1 ' in lt ) and ('Desktop' in lt))]

	def show_lites(S):
		for lite in S.lites:
			print(lite.__repr__())
	
	def active_desktop(S):
		"""
		Find the active window in de output of wmctrl -d
		0  - DG: 6880x1440  VP: N/A  WA: 0,0 6880x1440  cad
		1  * DG: 6880x1440  VP: 0,0  WA: 0,0 6880x1440  inet
		2  - DG: 6880x1440  VP: N/A  WA: 0,0 6880x1440  file
		the line with the asterix
		:return: the line with tha asterix split into a list at the whitespaces.
		"""
		for line in service_call('wmctrl','-d'):
			if line[3:4] == '*':
				# eg ['1', '*', 'DG:', '6880x1440', 'VP:', '0,0', 'WA:', '0,0', '6880x1440', 'inet']
				return int(line[:2])
		raise RuntimeError (f"Lunettes did not find an active window")
		return -1
	
	def get_surface_lites(S):
		# ['1', '*', 'DG:', '6880x1440', 'VP:', '0,0', 'WA:', '0,0', '6880x1440', 'inet']
		# first field is the window number
		active_desktop = S.active_desktop()
		for fl in S.lites:
			if fl.is_lit_on(active_desktop):
				yield fl
		#return [fl for fl in S.lites if fl.desktop() == active]

	def divide_lites(S):
		#DEBUGPRINT(f'divide_lites {S=}')
		front_lites=S.get_surface_lites()
		lite_division=group_by_common_area(S.screens,front_lites)
		# for div in lite_division:
		# 	#DEBUGPRINT(div)

		for screen,lites in zip(S.screens,lite_division):
			#DEBUGPRINT(f'{screen.name()}')
			wanted_frames=len(lites)
			if not wanted_frames:
				continue
			#screen_tiles=screen.frame_divide(wanted_frames)
			screen_tiles = screen.ratio_divide(wanted_frames)
			#matched=make_match_in_heaven(lites,screen_tiles)
			matched = make_match_in_manhattan(lites, screen_tiles)
			for match in matched:
				match.place()
				#DEBUGPRINT(f'{str(match )}')

def divide_test(x0,y0,x1,y1,parts):
	f=WindowFrame(x0,y0,x1,y1)
	f.frame_divide(5)

if __name__ == '__main__':
	lunnets=Lunettes()
	lunnets.divide_lites()
