#!/usr/bin/python3
import subprocess
import json
import re

DEBUGEXIT=exit
DEBUGPRINT=print

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


# #_SHORT={"Absolute upper-left X":"X",
#         "Absolute upper-left Y":'Y',
#         "Relative upper-left X":"RX",
#         "Relative upper-left Y":'RY'
#         }

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

B=2   # half border width

def square_distance(ax,ay,bx,by):
	dx=ax-bx
	dy=ay-by
	return dx*dx+dy*dy

def between(lo,mid,hi):
	return (lo<=mid) and (hi>=mid)

class WindowFrame(list):
	def __init__(S,x0,y0=None,x1=None,y1=None,xywh=False):
		list.__init__(S)
		if xywh:
			if isinstance(y1,int):
				S+=[x0,y0,x0+x1,y0+y1]
			else:
				x0,y0,w,h=x0
				S+=[x0,y0,x0+w,y0+h]
			return
		if isinstance(y1,int):
			S+=[x0,y0,x1,y1]
			return
		S+=list(x0)

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

	def subtract_panel(S,panel):
		#DEBUGPRINT(f'S     {str(WindowFrame(S))}')
		w,h=panel.width_heigth()
		#DEBUGPRINT(f'panel {str(panel)} {w:4} {h:4}')

		SminX,SminY,SmaxX,SmaxY=S
		PminX,PminY,PmaxX,PmaxY=panel
		if w > h: # horizonal panel
			if between(PminY,SminY,PmaxY):
				S[miniY]=PmaxY
				return
			if between(PminY,SmaxY,PmaxY):
				S[maxiY]=PminY
				return
		if between(PminX,SminX,PmaxX):
			S[miniX]=PmaxX
			return
		if between(PminX,SmaxX,PmaxX):
			S[maxiX]=PminX
			return

	def holds(S,x,y):
		Sx0,Sy0,Sx1,Sy1=S
		if x < Sx0 or x > Sx1: return False
		if y < Sy0 or y > Sy1: return False
		return True

	def divide_width(S):
		xmid = (S[miniX]+S[maxiX])//2
		S[maxiX]=xmid-B
		return WindowFrame(xmid+B,S[miniY],S[maxiX],S[maxiY])

	def divide_heigth(S):
		ymid = (S[miniY]+S[maxiY])//2
		S[maxiY]=ymid-B
		return WindowFrame(S[miniX],ymid+B,S[maxiX],S[maxiY])

	def sub_divide(S,parts):
		pieces=[]
		def divide(frame,P):
			P1=P//2
			P2=P-P1
			#DEBUGPRINT(f'{P=:<2}{P1=:<2}{P2=:<2}')
			if P<1 :
				return
			if P==1:
				pieces.append(frame)
				return
			w,h=frame.width_heigth()
			if (w*4//5) > h:
				half=frame.divide_heigth()
			else:
				half=frame.divide_width()
			divide(frame,P1)
			divide(half ,P2)
		frame=S.duplicate()
		divide(frame,parts)
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

def best_match(old_frames,new_frames):
	lo=len(old_frames) ; ln=len(new_frames)
	if lo!=ln:
		raise ValueError ('best_match old_frames and new_frames should be of equal length.')
	pairs=[]
	for of in old_frames:
		best=None
		for nf in new_frames:
			if not best:
				best = [of,nf,of.commen(nf)]
				continue
			comm=of.commen(nf)
			if comm > best[2]:
				best = [of,nf,comm]
		pairs.append(best)

class Lite(WindowFrame):

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
		# S.id='0x01800003'
		# S.desk=int()
		# frame=xwininfo(id)
		# WindowFrame.__init__(S,frame)

	def __repr__(S):
		# 0x03e0003e  1 3440 0    3440 1440
		a,b,c,d=S
		w=c-a ; h = d-b
		return f'Lite("{S.id:#08x} {S.desk:2} {a:4} {b:4} {w:4} {h:4}")'

	def id(S):
		return S.id

	def desktop(S):
		return S.desk

	def frame(S):
		return WindowFrame.S

	def place(S):
		x, y, w, h = S.x_y_width_heigth()
		wmctrl('-i', '-r',str(S.id), '-e', f"0,{x},{y},{w},{h}" )

class Monitor(WindowFrame):
	def __init__(S,name,x,y,w,h):
		WindowFrame.__init__(S,x,y,w,h,xywh=True)
		S.myname=name

	def __str__(S):
		x0,y0,x1,y1=S
		return f'{S.myname:10} [{x0:4},{y0:4}],[{x1:4},{y1:4}]'

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
		#S.frames=[ X['Frame'] for X in screens.values()]
		#DEBUGPRINT(S.screens)
		S.lites=S.list_lites()
		# S.show_lites()
		S.show_screens()
		panels=[panel for panel in S.lites if panel.desk < 0]
		for screen in S.screens:
			for panel in panels:
				screen.subtract_panel(panel)
		S.show_screens()

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
			if fl.desktop() == active:
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

		# each lite to the monitor the with which it has the biggest common area
		monitor_lites = [[] for _ in S.screens ]
		for l in S.get_surface_lites():
			best=None
			count = -1
			for s in S.screens:
				count += 1
				if not best:
					best=[count, l, s.common(l)]
					continue
				com=s.common(l)
				if com > best[2]:
					best=[count, l, com]
			monitor_lites[best[0]].append(best[1])

		for lites_of_monitor in monitor_lites:
			DEBUGPRINT(lites_of_monitor)

		# Devide each monitor in the number of WindowFrame's needed for its Lite's
		i=-1
		for screen in S.screens:
			i+=1
			onscreen_lites=len( monitor_lites[i])
			frames=screen.sub_divide(onscreen_lites)
			DEBUGPRINT(f'{frames=}')
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

def main() -> None:
	lunnets=Lunettes()
	lunnets.divide_lites()
	#lunnets.show_lites()

if __name__ == '__main__':
	main()

