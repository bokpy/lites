#!/usr/bin/python3
import subprocess
from collections import deque
import json
import re
from services import *

B=0  # border width

#Id_re     =r'Window id: *(0x\d+)'
AulX_re     =r'Absolute upper-left X: *(\d+)'
AulY_re     =r'Absolute upper-left Y: *(\d+)'
Width_re    =r'Width: *(\d+)'
Height_re   =r'Height:*(\d+)'
Xwin_re     ='|'.join([AulX_re,AulY_re,Width_re,Height_re])
Re_Xwin=re.compile(Xwin_re,re.MULTILINE)
Re_Number=re.compile(r'\D*(\d+)$')

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

re_extents = re.compile(r'^_NET_FRAME_EXTENTS\D*(\d+)\D*(\d+)\D*(\d+)\D*(\d+).*')
def xprop_borders(id):
	for line in service_call("xprop","-len","128","-id",str(id)):
		frame_extents=re_extents.match(line)
		if frame_extents:
			ret=[int(frame_extents.group(i)) for i in range(1,5)]
			DEBUGPRINT(f'{id:10}: {ret}')
			return ret
	raise RuntimeError (f'xprop_borders({id}) no border info found.')

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
		if '_NET_WM_DESKTOP'  in line:
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

def get_real_frame_sizes():
	DEBUGPRINT(f'get_real_frame_sizes NOT FUCTIONAL!!!')
	ids=xwininfo_tree_ids()
	for id in ids:
		count=-1
		for line in xprop_frame(id):
			count+=1
			region=re_region.match(line)
			if region:
				DEBUGPRINT(f'{id:>10} {count:4} ',end='')
				DEBUGPRINT(line)
			extents=re_extents.match(line)
			if extents:
				DEBUGPRINT(f'{id:>10} {count:4} ',end='')
				DEBUGPRINT(line)


# def wmctrl(*args) -> str:
# 	call = ["wmctrl"] + list(args)
# 	try:
# 		res = subprocess.check_output(call)
# 	except subprocess.SubprocessError as e:
# 		print(f'wmctrl {args} failed')
# 		print(f'subprocess.SubprocessError {e}')
# 		return ''
# 	return res.decode('utf-8')

miniX=0 # X Upper Left
miniY=1 # Y Upper Left
maxiX=2 # X Lower Rigth
maxiY=3 # Y Lower Rigth


def square_distance(ax,ay,bx,by):
	dx=ax-bx
	dy=ay-by
	return dx*dx+dy*dy

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

	def corners(S):
		x0,y0,x1,y1=S
		return x0,y0,x1,y0,x1,y1,x1,y1

	def difference(S,realsize):
		DEBUGPRINT(f'difference {str(S)}')
		DEBUGPRINT(f'           {str(realsize)}')
		ret = [Q-P for Q,P in zip(S,realsize)]
		DEBUGPRINT(f'           {ret}')
		return [Q-P for Q,P in zip(S,realsize)]

	# def to_dict(S):
	# 	# Convert instance to dictionary for JSON serialization
	# 	return {'frame': S.frame}
	#
	# @classmethod
	# def from_dict(cls, data):
	# 	# Create instance from dictionary
	# 	return cls(frame=data['frame'])

	def duplicate(S):
		return WindowFrame(S)

	def shrink(S,pixels):
		SminX,SminY,SmaxX,SmaxY=S
		S.set(SminX+pixels,SminY+pixels,SmaxX-pixels,SmaxY-pixels)

	def grow(S,pixels):
		S.shrink(-pixels)

	def subtract_panel(S,panel):
		if not S.common(panel):
			return
		#DEBUGPRINT(f'S     {str(WindowFrame(S))}')
		w,h=panel.width_heigth()
		#DEBUGPRINT(f'panel {str(panel)} {w:4} {h:4}')

		SminX,SminY,SmaxX,SmaxY=S
		T___X,T___Y,B___X,B___Y=panel
		if w > h: # horizonal panel
			if between(T___Y,SminY,B___Y): # top panel
				S.set(SminX,B___Y,SmaxX,SmaxY)
				return
			if between(T___Y,SmaxY,B___Y): # bottom panel
				S.set(SminX,SminY,SmaxX,T___Y)
				return
		if between(T___X,SminX,B___X): # left panel
			S.set(B___X,SminY,SmaxX,SmaxY)
			return
		if between(T___X,SmaxX,B___X): # right panel
			S.set(SminX,SminY,T___X,SmaxY)
			return

	def holds(S,x,y):
		Sx0,Sy0,Sx1,Sy1=S
		if x < Sx0 or x > Sx1: return False
		if y < Sy0 or y > Sy1: return False
		return True

	def divide_width(S):
		#DEBUGPRINT (f'divide_width')
		#DEBUGPRINT (f'org   : {str(S)}')
		ominx,ominy,omaxx,omaxy=S
		xmidmin=(ominx+omaxx)//2-B
		xmidmax=xmidmin+B+B
		S.set(xmidmax,ominy,omaxx,omaxy)
		ret = WindowFrame(ominx,ominy,xmidmin,omaxy)
		#DEBUGPRINT (f'org/2 : {str(S)}')
		#DEBUGPRINT (f'ret/2 : {str(ret)}')
		return ret

	def divide_heigth(S):
		#DEBUGPRINT (f'divide_heigth')
		#DEBUGPRINT (f'org   : {str(S)}')
		ominx,ominy,omaxx,omaxy=S
		ymidmin=(ominy+omaxy)//2-B
		ymidmax=ymidmin+B+B
		S.set(ominx,ominy,omaxx,ymidmin)
		ret = WindowFrame(ominx,ymidmax,omaxx,omaxy)
		#DEBUGPRINT (f'org/2 : {str(S)}')
		#DEBUGPRINT (f'ret/2 : {str(ret)}')
		return ret

	def frame_divide(S,parts):
		pieces=[]
		def divide(frame,P):
			P1=P//2
			P2=P-P1
			#DEBUGPRINT(f'{P=:<2}{P1=:<2}{P2=:<2}')
			if P<1 :
				return
			if P==1:
				#DEBUGPRINT('Append')
				pieces.append(frame)
				return
			w,h=frame.width_heigth()
			# this is gold 89 55
			if w*5 < h*6:
				half=frame.divide_heigth()
			else:
				half=frame.divide_width()
			divide(frame,P1)
			divide(half ,P2)
		frame=S.duplicate()
		divide(frame,parts)
		if len(pieces) != parts:
			raise RuntimeError (f'frame_divide({parts=}) made {len(pieces)} parts')
		#DEBUGPRINT(f'frame_divide({parts=}) made {len(pieces)} parts')
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

	def common_frame(S,O:"WindowFrame")->"WindowFrame":
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
			return None  # No overlap
		return WindowFrame(left_edge,top_edge,right_edge,bottom_edge )

	def common(S,O:"WindowFrame")->int:
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

def group_by_common_aeria(herders,flok):
	count=len(herders)
	range_herders=range(0,count)
	pen = [ [] for _ in range_herders]
	#pen= [[]]*count
	for sheep in flok:
		best_herder=-1
		best_pasture=-1
		for herder,i in zip(herders,range_herders):
			pasture=herder.common(sheep)
			if pasture > best_pasture:
				best_herder=i
				best_pasture=pasture
		pen[best_herder].append(sheep)
		DEBUGPRINT(f'herder {best_herder} gets {sheep}')
	return pen

def make_match_in_hell(virgins,suitors):
	marriages=[]
	for bride, groom in zip(virgins,suitors):
		couple=Lite(bride.get_id(),bride.get_desktop(),groom)
		marriages.append(couple)
	return marriages

def make_match_in_heaven(virgins,suitors):

	WOMAN=0 ; MAN=1 ; DOWRY=2
	#DEBUGPRINT(f'{virgins=} , {suitors=}')
	lo=len(virgins) ; ln=len(suitors)
	DEBUGPRINT(f'{lo} virgins , {ln} suitors')
	if lo!=ln:
		raise ValueError ('best_match "virgins" and "suitors" must come in equal numbers.')

	# calculate common ground
	haeven=[[old.common(new) for old in virgins] for new in suitors ]
	elysians_range=range(0,lo)
	#DEBUG_SHOW_INT_ARRAY(haeven,'haeven')
	countdown=lo*lo #+lo # number of array elements + one dim extra for elements that get 2 times crossed out.
	marriages=[]
	def wedding(eve,adam):
		nonlocal countdown
		# spoil it for the rest of the Elysians
		for woman in elysians_range:
			if haeven[woman][adam] < 0:
				continue
			countdown-=1
			haeven[woman][adam]=-1
		for man in elysians_range:
			if haeven[eve][man] < 0:
				continue
			countdown-=1
			haeven[eve][man]=-1

	while countdown > 0:
		for eve in elysians_range:
			# if haeven[eve][0]<0:
			# 	continue
			# find the best match for Eve (if she profits from the dowry that is.)
			best_adam_for_eve=None
			for adam in elysians_range:
				if not best_adam_for_eve:
					best_adam_for_eve=[eve,adam,haeven[eve][adam]]
				if haeven[eve][adam]<0:
					continue
				if haeven[eve][adam] > best_adam_for_eve[DOWRY]:
					best_adam_for_eve=[eve,adam,haeven[eve][adam]]

			# Is what is best for Eve also best for Adam?
			best_bride=best_adam_for_eve
			groom=best_adam_for_eve[MAN]
			for eve in elysians_range:
				# if haeven[eve][this_adam]<0:
				# 	continue
				if haeven[eve][groom] > best_bride[DOWRY]:
					# bigger dowry change bride
					best_bride=[eve,groom,haeven[eve][groom]]
			bride=best_bride[WOMAN]
			DEBUG_SHOW_INT_ARRAY(haeven, f'haeven{countdown:3}')
			DEBUGPRINT(f'Wedding {bride=} {groom=}')
			wedding(bride,groom)
			# DEBUGPRINT(f'Before wedding({bride=:>3}X{groom=:<3}): {virgins=} , {suitors=}')
			# DEBUGPRINT(f'{virgins[bride]=}')
			# DEBUGPRINT(f'{suitors[groom]=}')
			bride_lite=virgins[bride]
			groom_frame=suitors[groom]
			id=bride_lite.id
			desk=bride_lite.desk
			couple=Lite(id,desk,groom_frame)
			marriages.append(couple)
	DEBUG_SHOW_INT_ARRAY(haeven,f'left over heaven')		#DEBUG_SHOW_INT_ARRAY(haeven)
	return marriages

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
		DEBUGPRINT(f'Borders {borders}')
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
		# wmctrl -i -r 0x0340003e -e '0,3500,100,500,700'
		DEBUGPRINT(f'place {str(S)}')
		x, y, w, h = S.x_y_width_heigth()
		DEBUGPRINT(f'at [{x:4},{y:4}] {w:4}x{h:4}')
		service_call('wmctrl','-i', '-r',str(S.id), '-e', f"0,{x},{y},{w},{h}" )

		xwin=xwininfo_frame(S.id)

		DEBUGPRINT(f'xwininfo Difference {S.difference(xwin)}')
		DEBUGPRINT(f'xwininfo {xwin}')
		xdo=xdotool_frame(S.id)
		DEBUGPRINT(f'xdotool {xdo}')

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
			DEBUGPRINT(f'{monitor=},{ width=},{ height=},{ x_offset=},{ y_offset=}')
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
				screen.subtract_panel(panel)
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

	def _make_json_friendly_match_frames_dict(S):
		i=0
		S.match_frames={}
		for frame in S.frames:
			S.match_frames[i]={'frame':frame,'lites':[]}
			i+=1

	def divide_lites(S):
		DEBUGPRINT(f'divide_lites {S=}')
		front_lites=S.get_surface_lites()
		lite_division=group_by_common_aeria(S.screens,front_lites)
		for div in lite_division:
			DEBUGPRINT(div)

		for screen,lites in zip(S.screens,lite_division):
			DEBUGPRINT(f'{screen.name()}')
			wanted_frames=len(lites)
			if not wanted_frames:
				continue
			screen_tiles=screen.frame_divide(wanted_frames)
			matched=make_match_in_heaven(lites,screen_tiles)
			for match in matched:
				match.shrink(B)
				match.place()
				DEBUGPRINT(f'{str(match )}')

def divide_test(x0,y0,x1,y1,parts):
	f=WindowFrame(x0,y0,x1,y1)
	f.frame_divide(5)

def main() -> None:
	#divide_test(0,0,1024,2048,5)
	lunnets=Lunettes()
	lunnets.divide_lites()
	#lunnets.show_lites()

if __name__ == '__main__':
	# for id in xprop_tree_xwins():
	# 	xprop_show(id)
	# for id in xprop_tree_xwins():
	# 	xprop_show(id,'_NET_WM_STATE')
	# 	xprop_show(id,'_NET_WM_DESKTOP')
	# DEBUGEXIT(0)
	main()
	DEBUGEXIT(0)
	ids=xwininfo_tree_ids()

	for id in ids:
		xprop_frame=decorated_frame_size(id,)
		xdo_frame  =xdotool_frame(id)
		xwin_frame =xwininfo_frame(id)
		if xprop_frame:
			print(f'{xprop_frame=}')
		print(f'{xdo_frame=}')
		print(f'{xwin_frame=}')
	#get_real_frame_sizes()
	#main()

