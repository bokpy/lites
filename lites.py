#!/usr/bin/python3
import subprocess
import json
import re

DEBUGEXIT=exit
DEBUGPRINT=print

B=120   # border width

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

#Id_re     =r'Window id: *(0x\d+)'
AulX_re     =r'Absolute upper-left X: *(\d+)'
AulY_re     =r'Absolute upper-left Y: *(\d+)'
Width_re    =r'Width: *(\d+)'
Height_re   =r'Height:*(\d+)'
Xwin_re     ='|'.join([AulX_re,AulY_re,Width_re,Height_re])
Re_Xwin=re.compile(Xwin_re,re.MULTILINE)

def xwininfo(id)->"WindowFrame":
	#DEBUGPRINT(f'<--- xwininfo({id}) --->')
	try:
		info = subprocess.check_output(["xwininfo","-frame","-id",str(id)])
	except subprocess.SubprocessError as e:
		print(f'xwininfo -id {id} failed')
		print(f'subprocess.SubprocessError {e}')
		return None
	str_info=info.decode('utf-8')
	grps=Re_Xwin.findall(str_info)
	DEBUGPRINT(grps)
	return grps

# def xwininfo_frame(id):
# 	try:
# 		info = subprocess.check_output(["xwininfo", "-frame", "-id",str(id)])
# 	except subprocess.SubprocessError as e:
# 		print(f'xwininfo -id {id} failed')
# 		print(f'subprocess.SubprocessError {e}')
# 		return {}
# 	str_info=info.decode('utf-8')
#
# 	return str_info

# def get_window_size_with_decorations(window_id):
# 	# Run xwininfo for the given window ID
# 	result = subprocess.run(['xwininfo', '-id',
# 	                         str(window_id)], stdout=subprocess.PIPE)
# 	output = result.stdout.decode('utf-8')
#
# 	# Parse the output for width and height
# 	width, height = None, None
# 	for line in output.splitlines():
# 		if 'Width:' in line:
# 			width = int(line.split(':')[1].strip())
# 		elif 'Height:' in line:
# 			height = int(line.split(':')[1].strip())
#
# 	return width, height

	# # Example usage:
	# # Replace '0x123456' with the actual window ID of the target window.
	# window_id = '0x123456'
	# width, height = get_window_size_with_decorations(window_id)
	# print(f'Width: {width}, Height: {height}')

def wmctrl(*args) -> str:
	call = ["wmctrl"] + list(args)
	try:
		res = subprocess.check_output(call)
	except subprocess.SubprocessError as e:
		print(f'wmctrl {args} failed')
		print(f'subprocess.SubprocessError {e}')
		return ''
	return res.decode('utf-8')

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

	def grow(S,pixels):
		SminX,SminY,SmaxX,SmaxY=S
		S.set(SminX+pixels,SminY+pixels,SmaxX-pixels,SmaxY-pixels)
		pass

	def shrink(S,pixels):
		S.grow(-pixels)

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
				if haeven[eve][adam]<0:
					continue
				if not best_adam_for_eve:
					best_adam_for_eve=[eve,adam,haeven[eve][adam]]
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
			lux=int(l[n:n+4])
			n+=5
			luy=int(l[n:n+4])
			n+=5
			w=int(l[n:n+4])
			n+=5
			h=int(l[n:n+4])
			WindowFrame.__init__(S,lux,luy,w,h,xywh=True)
			return
		if isinstance(args[0],int):
			S.id  = args[0]
			S.desk= args[1]
			if isinstance(args[2],WindowFrame):
				minx,miny,maxx,maxy=args[2]
				WindowFrame.__init__(S,minx,miny,maxx,maxy)
				return
		WindowFrame.__init__(S,args[3],args[4],args[5],args[6])

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

	def place(S):
		# wmctrl -i -r 0x0340003e -e '0,3500,100,500,700'
		DEBUGPRINT(f'place {str(S)}')
		x, y, w, h = S.x_y_width_heigth()
		DEBUGPRINT(f'at [{x:4},{y:4}] {w:4}x{h:4}')
		wmctrl('-i', '-r',str(S.id), '-e', f"0,{x},{y},{w},{h}" )

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

def xrandr()->list:
	monitor_regex = re.compile(r'(\S+) connected.*? (\d+)x(\d+)\+(\d+)\+(\d+)')
	try:
		bytes = subprocess.check_output(["xrandr"])
	except subprocess.SubprocessError as e:
		print(f'xrandr failed')
		print(f'subprocess.SubprocessError {e}')
		return {}
	lines=bytes.decode('utf-8').splitlines()
	DEBUGPRINT(f'{lines}')
	screens=[]
	for line in lines:
		match = monitor_regex.search(line)
		if match:
			monitor, width, height, x_offset, y_offset = match.groups()
			DEBUGPRINT(f'{monitor=},{ width=},{ height=},{ x_offset=},{ y_offset=}')
			screens.append(Monitor(monitor,int(x_offset),int(y_offset),int(width),int(height)))
	return screens

class Lunettes:
	def __init__(S):
		S.screens=xrandr()
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
		#DEBUGPRINT('list_windows')
		# 0x01a0009c -1 0    0    6880 1440 Morfine Desktop
		l = wmctrl('-l', '-G')
		return [Lite(lt) for lt in l.splitlines() if not ((' -1 ' in lt ) and ('Desktop' in lt))]

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
		l = wmctrl('-d')
		# print(l)
		a = S._array(l)
		# print(f'{a=}')
		for line in a:
			# print(f'{line=}')
			if line[1] == '*':
				# eg ['1', '*', 'DG:', '6880x1440', 'VP:', '0,0', 'WA:', '0,0', '6880x1440', 'inet']
				return int(line[0])
		raise RuntimeError (f"Lunettes did not find an active window")
		return -1
	
	def get_surface_lites(S):
		# ['1', '*', 'DG:', '6880x1440', 'VP:', '0,0', 'WA:', '0,0', '6880x1440', 'inet']
		# first field is the window number
		active = S.active_desktop()
		for fl in S.lites:
			if fl.get_desktop() == active:
				yield fl
		#return [fl for fl in S.lites if fl.desktop() == active]

	def _make_json_friendly_match_frames_dict(S):
		i=0
		S.match_frames={}
		for frame in S.frames:
			S.match_frames[i]={'frame':frame,'lites':[]}
			i+=1

	# def _lites2match_frames(S):
	# 	S._make_json_friendly_match_frames_dict()
	# 	#JDUMP(S.match_frames)
	# 	for L in S.on_show: # lite eg 0x03600007 1 3464 116 1612 1304 0.0 0
	# 		best_match=None
	# 		frame_count=-1
	# 		for F in S.frames:
	# 			frame_count+=1
	# 			cf=S.common_surface(F[0],F[1],F[2],F[3] , L[2],L[3],L[4],L[5])
	# 			if not best_match:
	# 				best_match=(cf,frame_count)
	# 				continue
	# 			if cf > best_match[0]:
	# 				best_match=(cf,frame_count)
	# 		#DEBUGPRINT(f'{best_match[0]=},{best_match[1]=}')
	# 		S.match_frames[best_match[1]]['lites'].append(L)

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


		# 	#matched=make_match_in_heaven(monitor_lites[i],monitor_frames[i])
		# 	matched=make_match_in_hell(monitor_lites[i],monitor_frames[i])
		# 	for lite in matched:
		# 		lite.place()
		# 		pass
		# 	onscreen_lites_count=len( monitor_lites[i])
		# 	monitor_frames[i]=S.monitor(i).frame_divide(onscreen_lites_count)
		#
		# for i in monitors_range:
		# 	DEBUGPRINT(f'{i=:<3}{monitor_frames[i]=}')
		# 	for lite in monitor_lites[i]:
		# 		DEBUGPRINT(f'{lite=}')
		#
		# DEBUG_SHOW_INT_ARRAY(monitor_frames,'monitor frames')
		#
		# for i in monitors_range:
		# 	#matched=make_match_in_heaven(monitor_lites[i],monitor_frames[i])
		# 	matched=make_match_in_hell(monitor_lites[i],monitor_frames[i])
		# 	for lite in matched:
		# 		lite.place()
		# 		pass

		# for i in monitors_range:
		# 	DEBUGPRINT(f'{i} {monitor_frames[i]}')
		#
		#
		#
		# 	best_match(lites_of_monitor[i],monitor_frames[i])
		# 	lite_count=len(frame['lites'] )
		# 	frame['divide']=S.divide_and_conquer(frame['frame'],lite_count)
		# 	#DEBUGPRINT(f"{frame['divide']=}")
		#
		# for frame in S.match_frames.values():
		# 	for i in range(0,len(frame['lites'])):
		# 		#DEBUGPRINT (f"{frame['lites'][i]} ")
		# 		#DEBUGPRINT (f"{frame['divide'][i]}")
		# 		lite_id    = frame['lites'][i][0]
		# 		lite_frame = frame['divide'][i]
		# 		S.position_and_size(lite_id,lite_frame)
		# 		corrected_farme=S.correction(lite_id,lite_frame)
		# 		if corrected_farme:
		# 			S.position_and_size(lite_id,corrected_farme)

# winid=active[]

# Function to list all windows
# def list_windows():
#     result = subprocess.run(['wmctrl', '-l'], stdout=subprocess.PIPE)
#     windows = result.stdout.decode('utf-8').strip().split("\n")
#     for window in windows:
#         print(window)
#
# # Function to move and resize a window using its window ID (handle)
# def move_and_resize_window(window_id, x, y, width, height):
#     # Use wmctrl to move and resize window
#     cmd = ['wmctrl', '-i', '-r', window_id, '-e', f"0,{x},{y},{width},{height}"]
#     subprocess.run(cmd)
def divide_test(x0,y0,x1,y1,parts):
	f=WindowFrame(x0,y0,x1,y1)
	f.frame_divide(5)


def main() -> None:
	#divide_test(0,0,1024,2048,5)
	lunnets=Lunettes()
	lunnets.divide_lites()
	#lunnets.show_lites()

if __name__ == '__main__':
	main()

