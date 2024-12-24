#!/usr/bin/python3

import os.path
import subprocess
from collections import deque
import time
import re
import atexit
#from inspect import currentframe, getframeinfo

#cf = currentframe()

from services import JDUMP

# def CONTEXT():
# 	cf = currentframe()
# 	cfinf=getframeinfo(cf)
# 	print(f'\n{cfinf.function} line {cfinf.lineno}')

#DEBUGPRINT=print

HANG_AROUND_TIME = 4 # sec
HANG_AROUND_FILE = os.path.expanduser('~/lites_on')
HANG_AROUND_FILE = HANG_AROUND_FILE.replace('/home/','/tmp/')
KEEP_AROUND = True
PastRound= None
FileTime = None
TotalScreenSize = None
CALM_DOWN=0.15

def remove_hang_around():
	os.remove(HANG_AROUND_FILE)
	print(f'Stopped: removed "{HANG_AROUND_FILE}"')

pseudo_toss=deque([56, 22, 60, 71, 50, 66, 90, 0, 26, 64, 98, 14, 12, 8, 73, 4, 7, 45, 0, 36, 76, 4, 85, 42, 65, 67, 66, 23, 11, 67, 56, 27, 77, 39, 0, 27, 9, 53, 72, 82, 50, 18, 15, 74, 69, 55, 71, 18, 48, 21, 2, 73, 67, 32, 44, 12, 35, 44, 61, 4, 0, 33, 62, 98, 79, 76, 83, 73, 39, 40, 20, 42, 15, 59, 95, 40, 20, 27, 40, 36, 14, 41])
def somewhat_random():
	for _ in range(0,3):
		val=pseudo_toss.pop()
		pseudo_toss.appendleft(val)
		#OFF_DEBUG_PRINT(f'somewhat_random {val}')
	return val

def match_ints_without_sign(string):
	"""
	Search the string for integers and return them in a list
	:param string: string to search
	:return: list with integers found
	"""
	match=re.findall('(\d+)',string)
	if not match:
		return []
	return 	[int(x) for x in match]

def match_ints_with_sign(string):
	"""
	Search the string for signed and unsigned integers and return them in a list
	:param string: string to search
	:return: list with integers found
	"""
	match=re.findall(r'([+-]?\d+)',string)
	if not match:
		return []
	return 	[int(x) for x in match]

#B=4 # border width
def squared_distance(x0,y0,x1,y1):
	dx=x0-x1 ; dy=y0-y1
	return dx*dx + dy*dy
#
# def points_str(S):
# 		return f'{S[0]:4},{S[1]:4},{S[2]:4},{S[3]:4}'

def int_list_format(lst,ln):
	string = [f'{x:{ln}}' for x in lst]
	string = ', '.join(string)
	return string

def width_heigth(leftX,topY,rightX,botY):
	return rightX-leftX,botY-topY

def right_bottom(leftX,topY, width, height):
	return leftX + width, topY + height

def service_call(*args):
	try:
		info = subprocess.check_output(args)
	except subprocess.SubprocessError as e:
		print(f'{args} failed')
		print(f'subprocess.SubprocessError {e}')
		return None
	str_info=info.decode('utf-8')
	return str_info.splitlines()

def xdpyinfo_dimensions():
	"""
	retrieve the total screen size of the x server root
	"""
	lines = service_call("xdpyinfo")
	for line in lines:
		if "dimensions" in line:
			break
	width,heigth,wmm,hmm=match_ints_without_sign(line)
	return width,heigth

TotalScreenSize = xdpyinfo_dimensions()

def show_all_geometry(id):
	xdo_frame    =xdotool_get_lite_position(id)
	xdo_frame.SHOW_ROW("xdotool")
	wmctrl_frame =WindowFrame(*wmctrl_position(id))
	wmctrl_frame.SHOW_ROW("wmctrl")
	xw_stats=xwininfo_stats_coordinate(id)
	#JDUMP(xw_stats,'<<< xw_stats >>>>')
	absX,absY=xw_stats["abs"]
	w=xw_stats["width"]
	h=xw_stats["height"]
	WindowFrame(absX, absY, absX + w, absY + h).SHOW_ROW("xwin abs")
	relX,relY=xw_stats["rel"]
	WindowFrame(relX, relY, relX + w, relY + h).SHOW_ROW("xwin rel")
	xw_stats["geo_to_xy"].SHOW_ROW("xwin geo")
	xw_stats["corner_points"].SHOW_ROW("xwin corners")
	div=xw_stats["corner_points"].subtract(xw_stats["geo_to_xy"])
	WindowFrame(*div,check=False).SHOW_ROW("difference")
	print(f'      geometry {int_list_format(xw_stats["geometry"],4)}')

#
#   xdotool >---< xdotool >---< xdotool >---< xdotool >---< xdotool >---< xdotool >---<
#
##########################################################################################

def xdotool_place(id,leftX,topY,rightX,botY):
	w,h=width_heigth(leftX,topY,rightX,botY)
	#OFF_DEBUG_PRINT(f'xdotool_place [0x{id:06x}] ({leftX},{topY},{rightX},{botY}) {w}x{h}')
	service_call("xdotool","windowmove",str(id),str(leftX),str(topY))
	#time.sleep(CALM_DOWN)
	service_call("xdotool","windowsize",str(id),str(w),str(h))
	#time.sleep(CALM_DOWN)

def xdotool_getactivewindow():
	list_id=service_call("xdotool","getactivewindow")
	return int(list_id[0])

def xdotool_get_lite_position(id):
	lines=service_call("xdotool","getwindowgeometry",str(id))
	position=re.findall(r'(\d+)',lines[1])
	geometry=re.findall(r'(\d+)',lines[2])
	if position and geometry:
		left_x,top_y,_screen = [int(p) for p in position]
		width,heigth = [int(p) for p in geometry]
		right_x,bot_y=right_bottom(left_x,top_y,width,heigth )
		return WindowFrame(left_x,top_y,right_x,bot_y)
	return None

#
#   wmctrl >---< wmctrl >---< wmctrl >---< wmctrl >---< wmctrl >---< wmctrl >---<
#
##########################################################################################

def wmctrl_active_desktop_lites_list():
	"""
	Create a the list of lites on the active desktop
	Except the "Desktop" but with "-1" = visible on all desktops like panels
	:return: list of Lites
	"""
	#OFF_DEBUG_PRINT('list_windows')
	# 0x01a0009c -1 0    0    6880 1440 Morfine Desktop
	list_of_lites=[]
	active_desktop=wmctrl_active_desktop()
	# DEBUGPRINT(f'{active_desktop=}')
	lines = service_call('wmctrl','-l', '-G')
	for line in lines:
		# DEBUGPRINT(f'"{line}"')
		#OFF_DEBUG_PRINT(f'wmctrl_active_desktop_lites_list; "{line}"')
		if 'Desktop' in line:
			continue
		deskno=int(line[10:14])
		#DEBUGPRINT(f'{deskno=}')
		if ( deskno == -1 ) or ( deskno == active_desktop):
			list_of_lites.append(Lite(line))
	return list_of_lites

def wmctrl_place(id,leftX,topY,rightX,botY):
	w,h=width_heigth(leftX,topY,rightX,botY)
	service_call('wmctrl','-i', '-r',str(id), '-e', f"0,{leftX},{topY},{w},{h}" )

def wmctrl_active_desktop():
	"""
	Find the active window in de output of wmctrl -d
	0  - DG: 6880x1440  VP: N/A  WA: 0,0 6880x1440  cad
	1  * DG: 6880x1440  VP: 0,0  WA: 0,0 6880x1440  inet
	2  - DG: 6880x1440  VP: N/A  WA: 0,0 6880x1440  file
	the line with the asterix
	:return: the active desktop number.
	"""
	for line in service_call('wmctrl','-d'):
		if line[3:4] == '*':
			# eg ['1', '*', 'DG:', '6880x1440', 'VP:', '0,0', 'WA:', '0,0', '6880x1440', 'inet']
			return int(line[:2])
	raise RuntimeError (f"wmctrl_active_desktop did not find an active window")

def wmctrl_position(id):
	lines = service_call("wmctrl","-l","-G")
	split_line=''
	for line in lines:
		split_line=line.split()
		if int(split_line[0],16) == id:
			break
	#OFF_DEBUG_PRINT(f'get_wmctrl_position {split_line}')
	leftX,  topY, width, height = [ int(_) for _ in split_line[2:6] ]
	rightX, botY  = right_bottom(leftX,  topY, width, height)
	return leftX,  topY,rightX, botY

	"""
	-r <WIN> -e <MVARG>  Resize and move the window around the desktop.
                       The format of the <MVARG> argument is described below.
	<MVARG>              Specifies a change to the position and size
                       of the window. The format of the argument is:

                       <G>,<X>,<Y>,<W>,<H>

                       <G>: Gravity specified as a number. The numbers are
                          defined in the EWMH specification. The value of
                          zero is particularly useful, it means "use the
                          default gravity of the window".
                       <X>,<Y>: Coordinates of new position of the window.
                       <W>,<H>: New width and height of the window.

                       The value of -1 may appear in place of
                       any of the <X>, <Y>, <W> and <H> properties
                       to left the property unchanged.
                       """
#
#   xwininfo >---< xwininfo >---< xwininfo >---< xwininfo >---< xwininfo >---< xwininfo
#
##########################################################################################

def xwininfo_stats(id:int)->dict:
	lines=service_call("xwininfo","-id", str(id),"-stats")
	info={}
	for line in lines:
		#OFF_DEBUG_PRINT(f'\t"{line}"')
		if 'xwininfo' in line:
			continue
		if not ':' in line:
			continue
		key,value=line.split(':')
		key=key.strip()
		value=value.strip()
		info[key]=value
		try:
			value = int(value)
			info[key]=value
		except ValueError:
			#OFF_DEBUG_PRINT(f'ValueError {key=} {value=}')
			if key == 'Corners':
				#OFF_DEBUG_PRINT('Corners')
				match=re.findall('(\d+)',value)
				if match:
					info[key]=[int(x) for x in match]
	info['geometry']=match_ints_without_sign(lines[len(lines)-2])
	#JDUMP(info,'xwininfo_stats')
	#OFF_DEBUG_PRINT(f'{line}')
	return info

def xwininfo_corners_to_points(corners):
	"""
	:param corners: list of 8 integers for 4 corners of a window
	:return: WindowFrame(leftX,topY,rigthX,bottomY)
	"""
	global TotalScreenSize
	screen_left= screen_top= 0
	screen_rigth,screen_bottom=TotalScreenSize
	"""
Corners:  +3466+23  -26+23  -26-29  +3466-29

osition relative to the entire screen dimensions.

    Top-left corner: +3466+23
        +3466 is the X-coordinate from the left edge of the screen.
        +23 is the Y-coordinate from the top edge of the screen.
"""
	top_left_X =screen_left + corners[0]
	top_left_Y =screen_top  + corners[1]
	"""

    Top-right corner: -26+23
        -26 means 26 pixels from the right edge of the screen (X coordinate).
        +23 is the Y-coordinate from the top edge of the screen.
    """
	top_rigth_X = screen_rigth + corners[2]
	top_rigth_Y = screen_top   + corners[3]
	"""
    Bottom-right corner: -26-29
        -26 is the X-coordinate, 26 pixels from the right edge of the screen.
        -29 is the Y-coordinate, 29 pixels from the bottom edge of the screen.
	"""
	bottom_rigth_X = screen_rigth + corners[4]
	bottom_rigth_Y = screen_bottom+ corners[5]
	"""
    Bottom-left corner: +3466-29
        +3466 is the X-coordinate from the left edge of the screen.
        -29 is the Y-coordinate, 29 pixels from the bottom edge of the screen.
	"""
	bottom_left_X = screen_left  + corners[6]
	bottom_left_Y = screen_bottom+ corners[7]
	return WindowFrame(top_left_X,top_left_Y,bottom_rigth_X,bottom_rigth_Y)

def xwininfo_geometry_frame(id):
	lines=service_call("xwininfo","-id", str(id))
	line=''
	while not "geometry" in line:
		line = lines.pop()
	w,h,x,y =  match_ints_with_sign(line)
	return WindowFrame(x,y,x+w,y+h)

def xwininfo_stats_coordinate(id):
	lines=service_call("xwininfo","-id", str(id),"-stats")
	ret={}
	geometry = ''
	while geometry == '':
		geometry=lines.pop()
	#OFF_DEBUG_PRINT(f'{geometry=}')
	ret["geometry"]=match_ints_with_sign(geometry)
	for line in lines:
		if not line:
			continue
		try:
			key,value=line.split(':')
		except ValueError:
			#OFF_DEBUG_PRINT(f'ValueError "{line}"')
			continue
		key   = key.strip()
		value = value.strip()
		if key == 'Absolute upper-left X':
			ret["abs"]=[int(value)]
			continue
		if key == 'Absolute upper-left Y':
			ret["abs"].append(int(value))
			continue
		if key == 'Relative upper-left X':
			ret["rel"]=[int(value)]
			continue
		if key == 'Relative upper-left Y':
			ret["rel"].append(int(value))
			continue
		if key == 'Width':
			ret["width"]=int(value)
			continue
		if key == 'Height':
			ret["height"]=int(value)
			continue
		if key == 'Corners':
			ret["corners"]=match_ints_with_sign(value)

	#Corners:  +1735+65  -3525   +65  -3525 -0  +1735 -0
	corners=ret['corners']
	# corner_points=xwininfo_corners_to_points(corners)
	# corner_points.SHOW_ROW("xwininfo_corners_to_points")
	ret["corner_points"]=xwininfo_corners_to_points(corners)

	# geometry
	width,heigth,left_x,top_y=ret['geometry']
	rigth_x,bot_y = right_bottom(left_x,top_y,width,heigth)
	ret["geo_to_xy"]=WindowFrame(left_x,top_y,rigth_x,bot_y)
	return ret

def xwininfo_stats_show(info,just=12,digits=4):
	print(f'{"Abs: ".rjust(just)}{info["Absolute upper-left X"]:{digits}},{info["Absolute upper-left Y"]:{digits}}')
	print(f'{"Rel: ".rjust(just)}{info["Relative upper-left X"]:{digits}},{info["Relative upper-left Y"]:{digits}}')
	print(f'{"Width: ".rjust(just)}{info["Width"]:{digits}} Height: {info["Height"]:{digits}}')
	print(f'{"Border: ".rjust(just)}{info["Border width"]:{digits}}')
	print(f'{"Corners: ".rjust(just)}{int_list_format(info["Corners"],digits)}')
	print(f'{"geometry: ".rjust(just)}{int_list_format(info["geometry"],digits)}')

"""

geometry_re=re.compile(r'\D*(\d+)x(\d+)\D*(\d+).(.\d+).*')
def xwininfo_geometry(id):
	#-geometry 1076x1305+1178--58
	for line in service_call("xwininfo", "-id", str(id)):
		if '-geometry' in line:
			break
	match=geometry_re.match(line)
	if not match:
		for line in service_call("xwininfo", "-id", str(id)):
			print(f'{line}')
		print('Does not have a "-geometry" entry.')
		raise RuntimeError

	return [int(x) for x in match.groups()]
"""

#
#    xprop --**X**-- xprop --**X**-- xprop --**X**-- xprop --**X**-- xprop --**X**--
#
########################################################################################

def xprop_query(id,query):
	"""
	Make a call to xprop to get the value of a named property eg _NET_WM_STATE_HIDDEN
	:param id: window id
	:param query: property name
	:return: xprop answer string
	"""
	line =service_call("xprop","-notype", "-id",str(id),query)[0]
	if ':' in line:
		res=line.split(':')
	elif '=' in line:
		res=line.split('=')
	else:
		return ''
	return res[1].strip()

def xprop_active_window():
	line = service_call("xprop","-notype","-root","_NET_ACTIVE_WINDOW")[0]
	#DEBUGPRINT(f'xprop_active_window {line}')
	# _NET_ACTIVE_WINDOW: window id # 0x4e00007, 0x0
	match=re.findall(r'(0x[0-9a-fA-F]+)',line)
	#DEBUGPRINT(f'{match=}')
	# input(419)
	if not match:
		return -1
	return int(match[0],16)

# re_region  = re.compile(r'^_NET_WM_OPAQUE_REGION\D*(\d+)\D*(\d+)\D*(\d+)\D*(\d+).*')
#
# re_frame=re.compile(r'^(_NET_FRAME_EXTENTS|WM_CLASS)')
# def xprop_tree_xwins():
# 	ids=deque()
# 	re_id=re.compile(r'([0-9]{5,})')
# 	for line in service_call("xwininfo","-int","-root","-tree"):
# 		if '(has no name):' in line :
# 			continue
# 		id_list=re_id.findall(line)
# 		if not id_list:
# 			continue
# 		ids.append(int(id_list[0]))
# 	return ids

#re_extents = re.compile(r'.*FRAME_EXTENTS\(CARDINAL\) =\D*(\d+)\D*(\d+)\D*(\d+)\D*(\d+).*')
def xprop_borders(id):
	lines=service_call("xprop","-id",str(id),"_NET_FRAME_EXTENTS")
	match=re.findall(r'(\d+)',lines[0])
	zero=True
	ret=[]
	if not match:
		return None
	for x in match:
		x=int(x)
		if x:
			zero=False
		ret.append(x)
	if zero:
		return None
	return WindowFrame(*ret,False)

def xprop_in_view(id):
	"""
	test the visibility of a X11 window
	:param id: id of the window
	:return: the number of the desktop that displays the window when visible else -1
	"""
	answer=xprop_query(id,'_NET_WM_STATE_HIDDEN')
	return (answer == 'not found.')

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
#
# miniX=0 # X Upper Left
# miniY=1 # Y Upper Left
# maxiX=2 # X Lower Rigth
# maxiY=3 # Y Lower Rigth

def square_distance(ax,ay,bx,by):
	dx=ax-bx
	dy=ay-by
	return dx*dx+dy*dy

def manhattan_distance(ax,ay,bx,by):
	return abs(ax-bx)+abs(ay-by)

def between(lo,mid,hi):
	return (lo<=mid) and (hi>=mid)

class WindowFrame(list):
	"""
	Holds the coordinates 2 window frame points
	a list [left x, upper y, rigth x, lower y]
	"""
	def __init__(S,leftX,topY,rightX,botY,check=True):
		list.__init__(S)
		if check:
			if leftX > rightX:
				raise ValueError (f'leftX > rightX {leftX} > {rightX}')
			if topY > botY:
				raise ValueError (f'topY > botY {topY} {botY}')
		S+=[leftX,topY,rightX,botY]

	def __eq__(S,O):
		for s,o in zip(S,O):
			if s != o:
				return False
		return True
	def __gt__(S,O):
		"""
		S is greater than O,
		if the element with the maximum value in S is
		greater than the maximum of value in O
		:param O:
		:return:
		"""
		return max(S) > max(O)

	def zeros(S):
		for i in S:
			if i:
				return False
		return True

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

	def NO_SHOW_ROW(S,head:str,adjust_dec=5,adjust_head=12):
		head=head[-adjust_head:]
		numbers= [f'{x:{adjust_dec}}' for x in S]
		print(f'{head.rjust(adjust_head)}: {",".join(numbers)}')

	def copy(S,O):
		for i in range(0,4):
			S[i]=O[i]

	def duplicate(S):
		return WindowFrame(*S)

	def corners(S):
		x0,y0,x1,y1=S
		return x0,y0,x1,y0,x1,y1,x1,y1

	def subtract(S,O):
		ret = [a-b for a,b in zip(S,O)]
		return WindowFrame(*ret)

	def subtract_panel(S,panel):
		if not S.common_area(panel):
			return
		panel_w,panel_h=width_heigth(*panel)
		S_left_x,S_top_y,S_right_x,S_bottom_y=S
		panel_left_x,panel_top_y,panel_right_x,panel_bottom_y=panel
		panel_w,panel_h=width_heigth(panel_left_x,panel_top_y,panel_right_x,panel_bottom_y)
		if panel_w > panel_h: # horizontal
			if S_top_y == panel_top_y: # top horizontal
				S[1] = panel_bottom_y # top of S (monitor) = bottom of panel
				return
			if S_bottom_y == panel_bottom_y: # bottom horizontal
				S[3]=panel_top_y # panel at the bottom of the monitor bottom of screen = top of panel
				return
			return # horizontal but no contact with top or bottom
		# vertical
		if S_left_x==panel_left_x: # Left
			S[0] = panel_right_x # left x monitor right x panel
			return
		if S_right_x == panel_right_x: # right
			S[2]=panel_left_x # righth x monitor = left x panelpanel
		# done or it is a wandering window on all screens desktop -1
	
	def left_top_distance2(S,O):
		dx = S[0] - O[0]
		dy = S[1] - O[1]
		return dx*dx + dy*dy

	def holds(S,x,y):
		Sx0,Sy0,Srigth_x,Sy1=S
		if x < Sx0 or x > Srigth_x: return False
		if y < Sy0 or y > Sy1: return False
		return True

	def manhattan_distance(S,O):
		Sx0,Sy0,Sx1,Sy1=S
		Ox0,Oy0,Ox1,Oy1=O
		return manhattan_distance(Sx0,Sy0,Ox0,Oy0) + manhattan_distance(Sx1,Sy1,Ox1,Oy1)

	def divide_width(S):
		#OFF_DEBUG_PRINT (f'divide_width')
		#OFF_DEBUG_PRINT (f'org   : {str(S)}')
		ominx,ominy,omaxx,omaxy=S
		x_sum=ominx+omaxx
		xmidmin=x_sum//2
		xmidmax=x_sum-xmidmin
		S.set(xmidmax,ominy,omaxx,omaxy)
		ret = WindowFrame(ominx,ominy,xmidmin,omaxy)
		#OFF_DEBUG_PRINT (f'org/2 : {str(S)}')
		#OFF_DEBUG_PRINT (f'ret/2 : {str(ret)}')
		return ret

	def divide_heigth(S):
		#OFF_DEBUG_PRINT (f'divide_heigth')
		#OFF_DEBUG_PRINT (f'org   : {str(S)}')
		ominx,ominy,omaxx,omaxy=S
		y_sum=ominy+omaxy
		ymidmin=y_sum//2
		ymidmax=y_sum-ymidmin
		S.set(ominx,ominy,omaxx,ymidmin)
		ret = WindowFrame(ominx,ymidmax,omaxx,omaxy)
		#OFF_DEBUG_PRINT (f'org/2 : {str(S)}')
		#OFF_DEBUG_PRINT (f'ret/2 : {str(ret)}')
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

	def divide_recursive(S,stretches,horizontal=False,divide_left=True):
		frames=deque()
		divide_left = True
		def recursor(frame,stretches,horizontal):
			nonlocal divide_left
			if not stretches:
				return
			if stretches == 1:
				frames.append(frame)
				return
			left_x,  top_y , right_x, bot_y = frame

			if divide_left:
				div_right = stretches // 2
				div_left  = stretches - div_right
			else:
				div_left  = stretches // 2
				div_right = stretches - div_left

			if horizontal:
				mid_x = (left_x + right_x ) // 2
				recursor(WindowFrame(left_x,   top_y , mid_x,   bot_y ),div_left, False)
				recursor(WindowFrame(mid_x+1,  top_y , right_x, bot_y ),div_right,False)
				return
			div_low  = stretches // 2
			div_high = stretches - div_low
			mid_y = (top_y + bot_y) // 2
			recursor(WindowFrame(left_x,   top_y   , right_x, mid_y ),div_low, True)
			recursor(WindowFrame(left_x,   mid_y+1 , right_x, bot_y ),div_high,True)
		if not stretches:
			return frames
		if stretches == 1:
			frames.append(WindowFrame(*S))
			return frames
		recursor(S,stretches,horizontal)
		return frames

	def size(S):
		w,h=S.width_heigth()
		return w*h

	def width_heigth(S):
		x1,y1,x2,y2=S
		return x2-x1,y2-y1

	def common_area(S,O:"WindowFrame")->int:
		SleftX,StopY,SrightX,SbotY=S
		OleftX,OtopY,OrightX,ObotY=O

		# Determine the edges of the overlapping region
		leftX   = max(SleftX,  OleftX  )
		rightX  = min(SrightX, OrightX )
		topY    = max(StopY,   OtopY   )
		botY    = min(SbotY,   ObotY   )

		# DEBUGPRINT(f'S {str(S)}')
		# DEBUGPRINT(f'O {str(O)}')
		# DEBUGPRINT(f'{leftX=},{rightX=},{topY=},{botY=}')
		# DEBUGPRINT(f'common_width={rightX - leftX}  common_height ={botY - topY} ')

		common_width  = rightX - leftX
		if common_width <=0 :
			return 0
		common_height = botY - topY
		if common_height <= 0 :
			return 0
		return common_width * common_height

# def group_by_common_area(herders,flok):
# 	"""
# 	Find the screen where the biggest area of a window is placed.
# 	:param herders: list of Monitor instances
# 	:param flok: Lunnetes.surface_lites_iterator.
# 	             iterates windows that are assigned to a "herder" screen.
# 	:return: list[[window,...],[window,...],...]
# 	         list with a list of windows per monitor screen
# 	"""
# 	count=len(herders)
# 	range_herders=range(0,count)
# 	pen = [ [] for _ in range_herders]
# 	#pen= [[]]*count
# 	for sheep in flok:
# 		best_herder=-1
# 		best_pasture=-1
# 		for herder,i in zip(herders,range_herders):
# 			pasture=herder.common_area(sheep)
# 			if pasture > best_pasture:
# 				best_herder=i
# 				best_pasture=pasture
# 		pen[best_herder].append(sheep)
# 		#OFF_DEBUG_PRINT(f'herder {best_herder} gets {sheep}')
# 	return pen

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
	#OFF_DEBUG_PRINT(f'{genesis=}')
	heaven=deque(genesis)
	paradise=deque()
	#OFF_DEBUG_PRINT(f'{heaven=}')
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

def make_match_in_manhattan(virgins:WindowFrame,suitors:WindowFrame):
	"""
	virgin and suitor closed to each other by some measure here manhattan distance
	make that the virgin gets frame takes the same coordinates as the suitor
	:param virgins: reciever WindowFrames
	:param suitors: donor WindowFrames
	:return:
	"""
	VIRGIN=0 ; SUITOR=1 ; DOWRY = 2
	lo=len(virgins) ; ln=len(suitors)
	if lo!=ln:
		raise ValueError ('best_match "virgins" and "suitors" must come in equal numbers.')

	# genesis=[(virgin,suitor,distance),...]
	genesis=[]
	for virgin in virgins:
		for suitor in suitors:
			# somewhat_random() as tie breaker for windows that overlap exactly.
			dowry=virgin.manhattan_distance(suitor)+somewhat_random()
			genesis.append((virgin,suitor,dowry))
	# sort the genesis list on distance small on top
	genesis.sort(key=lambda tup: -tup[DOWRY])

	#OFF_DEBUG_PRINT(f'{genesis=}')
	heaven=deque(genesis)
	paradise=deque()
	#OFF_DEBUG_PRINT(f'{heaven=}')
	while True:
		pair=heaven.pop() # top match
		pair[VIRGIN].copy(pair[SUITOR])
		paradise.append(pair[VIRGIN])
		if not heaven:
			return paradise
		new_heaven=deque()
		bride=pair[VIRGIN]
		groom=pair[SUITOR]
		# remove all couples related with one of the members of
		# the chosen pair.
		for single_pair in heaven:
			if bride == single_pair[VIRGIN]:
				continue
			if groom == single_pair[SUITOR]:
				continue
			new_heaven.append(single_pair)
		heaven=new_heaven

class Lite(WindowFrame):
	"""
	is a WindowFrame
	S.id      = window id
	S.name    =
	S.borders =
	S.desk    = desktop of the window
	S.xwininfo_data = xwininfo_stats(S.id)
	"""
		# S.id='0x01800003'
		# S.desk=int()
		# frame=xwininfo(id)
		# WindowFrame.__init__(S,frame)

	def __init__(S,wmctrl=''):
		#OFF_DEBUG_PRINT(f'Lite init "{wmctrl=}")')
		# S.INIT_ARGS=[wmctrl]
		if wmctrl:
			# 0x01800003 -1 69   0    3302 65
			match = re.findall(r'([^ ]+) +', wmctrl)
			# DEBUGPRINT(match)
			if not match:
				raise ValueError(f'class Lite("{wmctrl}")')
			S.id      = int(match[0],16)
			S.name    = xprop_query(S.id,"WM_NAME")
			S.name    = S.name.replace('"','')
			S.wm_class= xprop_query(S.id,"WM_CLASS")
			S.wm_client_leader =  xprop_query(S.id,"WM_CLIENT_LEADER")
			#OFF_DEBUG_PRINT(f'{S.wm_client_leader =}')
			S.desk    = int(match[1])
			S.borders = xprop_borders(S.id)
			match=match[:6]
			leftX , topY, width, height = [ int(_) for _ in match[2:]]
			rightX, botY  = right_bottom(leftX,  topY, width, height)
			#OFF_DEBUG_PRINT(f'Lite init {int_list_format([leftX,topY,rightX,botY],4)}')
		else:
			raise ValueError ( 'Valid Lite init.')
		WindowFrame.__init__(S,leftX,topY,rightX,botY)

	def compensate_borders(S):
		if not S.borders:
			return S.duplicate()
		left_border, rigth_border, top_title, bottom_border = S.borders
		#OFF_DEBUG_PRINT(f'compensate_borders{int_list_format([left_border, rigth_border, top_title, bottom_border],4)}')
		left_x  = S[0] + left_border
		rigth_x = S[2] - rigth_border # - left_border

		top_y   = S[1] + top_title #+ bottom_border
		bot_y   = S[3] - bottom_border #- top_title -
		#OFF_DEBUG_PRINT(f'result: {int_list_format([left_x,top_y,rigth_x,bot_y],4)}')
		return WindowFrame(left_x,top_y,rigth_x,bot_y)

	def __str__(S):
		sid=f'{S.id:#08x}'[5:]
		borders='none'
		if S.borders:
			borders=f'{int_list_format(S.borders,2)}'
		return f'Lite: id[0x{S.id:07x}] desk[{S.desk:3}] {super().__str__()} borders {borders} {S.wm_client_leader} "{S.name[:12].ljust(12)}"'
		#return f'Lite [{S.id:#08x}]@[{S.desk:1}] {str(WindowFrame(S))}'

	def show_place(S):
		p=5
		print(f'left,top: ({S[0]:{p}},{S[1]:{p}}) right,bottom: ({S[2]:{p}},{S[3]:{p}}) width,height: ({S[2]-S[0]:{p}},{S[3]-S[1]:{p}})')

	def __repr__(S):
		"""
		__repr__ for the str type parameter constructor.
		:return: repr string
		"""
		# 0x03e0003e  1 3440 0    3440 1440
		a,b,c,d=S
		w=c-a ; h = d-b
		return f'Lite("{S.id:#08x} {S.desk:2} {a:4} {b:4} {w:4} {h:4}")'

	def windowframe(S):
		return WindowFrame(*S)

	def get_location(S,utility,subtype=None):
		if utility == 'xdotool':
			return  xdotool_get_lite_position(S.id)
		if utility == 'wmctrl':
			return WindowFrame(*wmctrl_position(S.id))
		if utility == 'xwininfo':
			xw_stats = xwininfo_stats_coordinate(S.id)
			w = xw_stats["width"]
			h = xw_stats["height"]
			if subtype == 'abs':
				absX, absY = xw_stats["abs"]
				return WindowFrame(absX, absY, absX + w, absY + h)
			if subtype == 'rel':
				relX, relY = xw_stats["rel"]
				return WindowFrame(relX, relY, relX + w, relY + h)
			if subtype == 'geometry':
				return xw_stats["geo_to_xy"]
			if subtype == 'corners':
				return xw_stats["corner_points"]
		raise NotImplemented (f'Lite.get_location({utility=},{subtype=}')

	def get_wmctrl_position(S):
		lines = service_call("wmctrl","-l","-G")
		split_line=''
		for line in lines:
			split_line=line.split()
			if int(split_line[0],16) == S.id:
				break
		#OFF_DEBUG_PRINT(f'get_wmctrl_position {split_line}')
		leftX,  topY, width, height = [ int(_) for _ in split_line[2:6] ]
		rightX, botY  = right_bottom(leftX,  topY, width, height)
		S.set(leftX,  topY,rightX, botY )

	def is_visable(S):
		wm_state        = xprop_query(S.id,"_NET_WM_STATE")
		#OFF_DEBUG_PRINT(f'{wm_state=} so visible = {not "_NET_WM_STATE_HIDDEN" in wm_state}')
		return not '_NET_WM_STATE_HIDDEN' in wm_state
	"""
	Calculate Title Bar Height
	
	To calculate the title bar height, subtract the top border height (from _NET_FRAME_EXTENTS) from the total outer height (from xwininfo).
	
	Example:
	
	    _NET_FRAME_EXTENTS: 5, 5, 30, 5
	    Total height (xwininfo): 800
	    Client height (application window): 768
	
	Title Bar Height:
	
	Title Bar Height = (Total Height - Client Height) - Top Border Width
	                 = (800 - 768) - 5
	                 = 32 pixels
	"""


	def correct_borders(S):
		left_w, right_w, top_title, bot_w = S.borders
		leftX, topY, rightX, botY = S
		leftX  += left_w
		rightX -= (left_w + right_w )
		topY   += top_title
		botY   -= bot_w
		return WindowFrame(leftX, topY, rightX, botY)

	def place_xdo(S):
		# xdotool_place(id,leftX,topY,rightX,botY)
		#OFF_DEBUG_PRINT(f'place xdo: {WindowFrame(*S)}')
		#OFF_DEBUG_PRINT(f'xprop_borders{S.borders}')
		xdotool_place(S.id,*S.compensate_borders())

	def place_wmctrl(S):
		S.SHOW_ROW(f'{S.name} -> ')
		#leftX,topY,rightX,botY=S.compensate_borders()
		#wmctrl_place(S.id,leftX,topY,rightX,botY)
		wmctrl_place(S.id,*S)
		show_all_geometry(S.id)
		#OFF_DEBUG_PRINT()
		# cur_pos=xwininfo_geometry_frame(S.id)
		# cur_pos.SHOW_ROW(f'{S.name} at ')

	def place_wmctrl_double_dip(S):
		#OFF_DEBUG_PRINT()
		S.SHOW_ROW(f'{S.name} -> ')
		noborder=S.compensate_borders()
		noborder.SHOW_ROW('noborder')
		wmctrl_place(S.id,*noborder)
		pos=xdotool_get_lite_position(S.id)
		pos.SHOW_ROW("at")
		div = pos.subtract(noborder)
		if WindowFrame(*div).zeros():
			#OFF_DEBUG_PRINT('No differces =======================')
			return
		WindowFrame(*div,False).SHOW_ROW('difference')
		return
		new_pos = noborder.duplicate()
		new_pos [0] += div[0]
		new_pos [1] -= div[1]
		new_pos [2] -= div[2]
		new_pos [3] -= div[3]
		new_pos.SHOW_ROW('new place')
		wmctrl_place(S.id,*new_pos)
		pos=xdotool_get_lite_position(S.id)
		pos.SHOW_ROW("moved to new")
		return
		position_frame=xdotool_get_lite_position(S.id)
		position_frame.SHOW_ROW("xdo first")
		if S == position_frame:
			#OFF_DEBUG_PRINT(f'"xdotool" got the same position as passed to "wmctrl_place"')
			return

		pos_div=[a-b for a,b in zip(S,position_frame)]
		#OFF_DEBUG_PRINT(f'div {int_list_format(pos_div,2)}')
		corrected_pos=[a+a-b for a,b in zip(coords,position_frame)]
		WindowFrame(*corrected_pos).SHOW_ROW("corrected")
		time.sleep(2)
		wmctrl_place(S.id,*corrected_pos)
		pos=xdotool_get_lite_position(S.id)
		pos.SHOW_ROW("after second")
		pos_div=[a-b for a,b in zip(S,pos)]
		#OFF_DEBUG_PRINT(f'end div {int_list_format(pos_div,2)}')

	def place_xdotool_double_dip(S):
		#OFF_DEBUG_PRINT()
		# S.SHOW_ROW(f'{S.name} -> ')
		xdotool_place(S.id,*S)
		if not S.borders:
			return
		pos=xdotool_get_lite_position(S.id)
		#pos.SHOW_ROW("is at: ")
		div = pos.subtract(S)
		if S.borders:
			#S.borders.SHOW_ROW('Borders')
			#div.SHOW_ROW('Difference')
			if div > S.borders:
				#OFF_DEBUG_PRINT(f"div > borders")
				xdotool_place(S.id,S[0],S[1],S[2],S[3]-S.borders[2])
				return
		border_adjust=S.compensate_borders()
		#border_adjust.SHOW_ROW('border_adjust')
		xdotool_place(S.id,*border_adjust)
		pos=xdotool_get_lite_position(S.id)
		#pos.SHOW_ROW("at")
		div = pos.subtract(border_adjust)
		if div.zeros():
			#OFF_DEBUG_PRINT('No differces =======================')
			return
		#div.SHOW_ROW('difference')
		return

MonitorCount=-1
class Monitor(WindowFrame):
	"""
	Is the WindowFrame area where windows can bee placed.
	The assumption is that nor the desktop nor the number or status of windows change
	during the live time of the script.
	S.name         : what you like
	S.count        : useful ?
	S.lites        : list of windows on this screen
	S.partitions   : partitions of the screen area in WindowFrames equal to the number of lites
	S.permutations : keeps track of the permutations of the lites assignment to partitions on second calls to the script
	"""
	def __init__(S,name,x,y,w,h):
		global MonitorCount
		WindowFrame.__init__(S,x,y,x+w,y+h)
		# S.SHOW_ROW(f'{name}')
		S.name=name
		MonitorCount+=1
		S.count=MonitorCount
		S.lites=[]
		S.partitions=deque()

	def update(S):
		"""
		got or lites from assign_lites_to_monitors(..)
		now subtract panel areas,
		partition the screen in WindowFrames to place the lites
		initiate permutations for a possible folowup call
		:return:
		"""
		# subtract panels to retain the netto erea
		lites_to_keep=deque()
		for lite in S.lites:
			if lite.desk < 0:
				S.subtract_panel(lite)
				continue
			if lite.is_visable():
				lites_to_keep.append(lite)
		S.lites=lites_to_keep
		if not lites_to_keep:
			return
		
		# divide the the area in parts equal to the number of lites
		S.partitions=S.divide_recursive(len(S.lites),True,divide_left=False)

		# assign each lite a partition close to the current position
		make_match_in_manhattan(S.lites,S.partitions)

	def place_lites(S):
		for lite in S.lites:
			#lite.place_xdo()
			#time.sleep(.8)
			#lite.place_wmctrl()
			#lite.place_wmctrl_double_dip()
			lite.place_xdotool_double_dip()

			#time.sleep(.8)

	def __str__(S):
		x0,y0,x1,y1=S
		return f'{S.count:1} [{x0:4},{y0:4}],[{x1:4},{y1:4}] lites({len(S.lites):2}) "{S.name}"'

	def show_lites(S):
		print(f'Monitor: "{S.name}" {int_list_format(S,5)}')
		for lite in S.lites:
			print(f'\t{str(lite)}')

	def rotate_lites(S,active_lite):
		# DEBUGPRINT(f'\nrotate_lites:')
		if len (S.lites ) < 2:
			return
		# is this the monitor holding the active window?
		am_I_the_one=False
		for lite in S.lites:
			# DEBUGPRINT(f'0x{lite.id:06x} == 0x{active_lite:06x}')
			am_I_the_one = ( lite.id == active_lite )
			if am_I_the_one:
				break
		if not am_I_the_one:
			#DEBUGPRINT("I'm not the one.")
			return
		S.partitions.rotate(-1)
		for lite,windowframe in zip(S.lites,S.partitions):
			lite.copy(windowframe)
			lite.place_xdotool_double_dip()

def assign_lites_to_monitors(monitors,lites):
	"""
	Assing lites to monitors with whom the have te most common area
	:param monitors:
	:param lites:
	:return:
	"""
	for lite in lites:
		prevalent_monitor = None
		biggest_common_area = -1
		for monitor in monitors:
			common = monitor.common_area(lite)
			if common and (lite.desk == -1):
				monitor.lites.append(lite)
				continue
			#OFF_DEBUG_PRINT(f'{common:6} {monitor.name} {lite.name}')
			if common > biggest_common_area:
				biggest_common_area = common
				prevalent_monitor   = monitor
		if prevalent_monitor:
			prevalent_monitor.lites.append(lite)

def xrandr_monitors()->list:
	"""
	Make a list of available monitor screens and their usable area
	:return: list of class Monitor
	"""
	monitor_regex = re.compile(r'(\S+) connected.*? (\d+)x(\d+)\+(\d+)\+(\d+)')
	monitors=[]
	for line in service_call("xrandr"):
		match = monitor_regex.search(line)
		if match:
			monitor, width, height, x_offset, y_offset = match.groups()
			#OFF_DEBUG_PRINT(f'{monitor=},{ width=},{ height=},{ x_offset=},{ y_offset=}')
			monitors.append(Monitor(monitor,int(x_offset),int(y_offset),int(width),int(height)))
	return monitors

def run():
	monitors=xrandr_monitors()
	lites=wmctrl_active_desktop_lites_list() # wmctrl_list_lites skips the root desktop
	# for lite in lites:
	# 	DEBUGPRINT(f'{str(lite)}')
	assign_lites_to_monitors(monitors,lites)
	for monitor in monitors:
		monitor.update()
	return monitors

	def place_lites(S,lites):
		for lite in lites:
			lite.place_wmctrl()

	def divide_lites(S):
		"""
		Devide a screen in WindowFrames to accommodate visible windows (lites).
		:return:
		"""
		front_lites=S.surface_lites_iterator()
		#S.lites_at_monitor=group_by_common_area(S.screens,front_lites)

		for screen,lites in zip(S.screens,S.lites_at_monitor):
			#OFF_DEBUG_PRINT(f'{screen.name()}')
			wanted_frames=len(lites)
			if not wanted_frames:
				continue
			#screen_tiles=screen.frame_divide(wanted_frames)
			screen_tiles = screen.ratio_divide(wanted_frames)
			#S.matched=make_match_in_heaven(lites,screen_tiles)
			matched = make_match_in_manhattan(lites, screen_tiles)
			S.place_lites(matched)

#
#  timing to catch a second call (click)
#
############################################

def sts(t:float)->str: # short time string
	"""
	effort to make time easier on the eyes.
	1734578551.362689 becomes a string "551.3626"
	:param t: epoch float
	:return: str( 3 least significant digits '.' 4 most significant digits )
	"""
	int_part = int(t)
	decimals = t - int_part
	int_part %= 1000
	decimals *= 10000
	int_deci = int (decimals)
	return f'{int_part:03}.{int_deci:04}'

def check_time_stamp_file():
	"""
	Look if the HANG_AROUND_FILE exists.
	if not make it and return.
	elif
	the HANG_AROUND_FILE is around longer than the HANG_AROUND_TIME delete it
	(file should not exist at this time)
	and start again.
	elif
	the HANG_AROUND_FILE is around less than the HANG_AROUND_TIME
	I'm a second instance so touch the HANG_AROUND_FILE
	to signal the first instance and leave.
	:return:
	"""
	global FileTime,KEEP_AROUND
	if not os.path.exists(HANG_AROUND_FILE):
		#OFF_DEBUG_PRINT('check_time_stamp_file NO HANG_AROUND_FILE')
		target_dir=os.path.dirname(HANG_AROUND_FILE)
		os.makedirs(target_dir, mode=0o777, exist_ok=True)
		with open(HANG_AROUND_FILE,'w') as f:
			f.write(str(os.getpid()))
			f.write("This file shoudn't bee around any more.")
			FileTime=time.time()
		atexit.register(remove_hang_around)
		#OFF_DEBUG_PRINT(f'Keep around file created by pid({os.getpid()}) at FileTime: {sts(FileTime)}')
		return
	now    = time.time()
	access = os.path.getmtime(HANG_AROUND_FILE)
	# DEBUGPRINT(f'HANG_AROUND_FILE now {sts(now)} - access={sts(access)} = {sts(now-access)}')
	# DEBUGPRINT(f'(now - access) > ({sts(HANG_AROUND_TIME)}) {(now - access) > HANG_AROUND_TIME}')
	if  (now - access) > HANG_AROUND_TIME:
		# stale HANG_AROUND_FILE remove and make a fresh start
		#OFF_DEBUG_PRINT(f'Old "{HANG_AROUND_FILE}" removed start over.')
		os.remove(HANG_AROUND_FILE)
		check_time_stamp_file()
		return
	os.utime(HANG_AROUND_FILE,times=(now,now))
	new_access= os.path.getmtime(HANG_AROUND_FILE)
	print("Signaled the first instance.")
	# DEBUGPRINT(f'access was {sts(access)} now {sts(new_access)}')
	# input('Enter to make me leave.')
	exit(0)

def reset_time_stamp_file():
	#OFF_DEBUG_PRINT('reset_time_stamp_file')
	os.remove(HANG_AROUND_FILE)
	atexit.unregister(remove_hang_around) # necessary to prevent double registering ?
	check_time_stamp_file()

def is_time_up():
	now    = time.time()
	if  (now - FileTime) > HANG_AROUND_TIME:
		print(f'Time is up, Lites go dark blinds close.')
		#os.remove(HANG_AROUND_FILE) # at exit does it
		exit(0)
	return now

def poll_time_stamp_file():
	count_down=20
	count = count_down
	accessed = FileTime
	while abs(accessed - FileTime) < 0.05:
		now = is_time_up()
		# count-=1
		# if count < 1:
		# 	time_delta=abs(accessed - FileTime)
		# 	print(f'Age: {sts(now - FileTime)}sec. ABS({sts(accessed)} - {sts(FileTime)}) = abs({sts(time_delta)})')
		# 	count=count_down
		time.sleep(.2)
		accessed =  os.path.getmtime(HANG_AROUND_FILE)
	# print(f'{accessed =} {FileTime=}')
	# print("poll_time_stamp_file() returns")
	return

#
#  ---> Test ---> Test ---> Test ---> Test ---> Test ---> Test
#
################################################################

def divide_test(x0,y0,x1,y1,parts):
	f=WindowFrame(x0,y0,x1,y1)
	f.frame_divide(5)

def test_lite_create_and_slecet(id):
	ll=wmctrl_active_desktop_lites_list()
	for lite in ll:
		if lite.id == id:
			return lite

def test_locater_and_placers(lite,placer,locator,sublocator=None):
	frame = lite.get_location(locator,sublocator)
	lite.set(*frame)
	message=locator
	if sublocator:
		message=sublocator
	frame.SHOW_ROW(f'{message}')
	input('enter')
	placer(lite)
	time.sleep(2)
	input('to the same place again Press Enter')
	placer(lite)
	time.sleep(2)

def test_place(id):
	print(f'test_place({id})')
	print(xdpyinfo_dimensions())
	#xw_info=xwininfo_stats_coordinate(id)
	#JDUMP(xw_info,"xwininfo_stats_coordinate")
	show_all_geometry(id)
	tester=test_lite_create_and_slecet(id)
	print(f'{tester.name} is visable {tester.is_visable()}')
	print(f'\nStart: {str(tester)}')
	# test_locater_and_placers(tester, Lite.place_wmctrl, "xdotool")
	# test_locater_and_placers(tester, Lite.place_wmctrl, "xwininfo", "corners")
	test_locater_and_placers(tester, Lite.place_wmctrl, "xwininfo", "geometry")
	return # *************************************************************************************
	xa,ya,xb,yb=winframe
	xa+=200
	ya-=50
	xb+=300
	yb+=270
	tester.set(xa,ya,xb,yb)
	#tester.place_wmctrl()
	tester.place_xdotool_double_dip()
	tester.get_wmctrl_position()
	print(f'Moved: {str(tester)}')
	time.sleep(1)
	tester.set(*winframe)
	#tester.place_wmctrl()
	tester.place_xdotool_double_dip()
	tester.get_wmctrl_position()
	print(f' Back: {str(tester)}')
	time.sleep(1)
	print(tester.subtract(winframe))
	show_all_geometry(id)
	#xwininfo_stats_coordinate(id)
	#tester.place_wmctrl()

def main():
	monitors=run()
	for monitor in monitors:
		monitor.place_lites()
	#
	# for monitor in monitors:
	# 	monitor.show_lites()
	check_time_stamp_file()
	print(f'kill with:\nrm -v {HANG_AROUND_FILE}')
	while True:
		#print(f'.',end='',flush=True)
		poll_time_stamp_file()
		active_window=xprop_active_window()
		xdo_active_window=xdotool_getactivewindow()
		#DEBUGPRINT(f'0x{active_window:06x} == 0x{xdo_active_window:06x}')
		for monitor in monitors:
			monitor.rotate_lites(xdo_active_window)
		reset_time_stamp_file()

if __name__ == '__main__':
	#test_place(int("0x4a001f2",16 ))
	main()


