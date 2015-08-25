dhG=None
timeout=85

def enum(): #lists the devices found by libUSB-win32
	import usb
	bs=usb.busses()
	print len(bs), " busses found"
	
	for b in bs:
		print "bus: ",b
		ds=b.devices
		print len(ds), " devices found"
		print
		for i in range(0,len(ds)):
			d=ds[i]
			print "DEVICE %d: PID: %04X, VID: %04X, devnum: %X" % (i, d.idVendor,d.idProduct, d.devnum), 
			dh=d.open()
			print "manuf:",dh.getString(d.iManufacturer,1000),", SN:",dh.getString(d.iSerialNumber,1000),", Product description:",dh.getString(d.iProduct,1000),", dev version:", d.deviceVersion
			c=d.configurations[0]
			print "config:",c.value,",",dh.getString(c.iConfiguration,1000)
			ifs=c.interfaces
			i=ifs[0][0]
			es=i.endpoints



def init(n=0): #opens the device, returns its deviceHandle
	import usb
	#global dh
	b=usb.busses()
	d=b[0].devices[n]
	print "DEVICE ",n,": PID:", d.idProduct ," VID: ",d.idVendor,", devnum: ",d.devnum
	dh=d.open()
	print "manuf:",dh.getString(d.iManufacturer,1000),", SN:",dh.getString(d.iSerialNumber,1000)
	c=d.configurations[0]
	try:
		print "config:",c.value,",",dh.getString(c.iConfiguration,1000)
	except:
		pass
	ifs=c.interfaces
	i=ifs[0][0]
	es=i.endpoints
	for e in es:
		if e.address>=128:
			ei=e.address
		else:
			eo=e.address
	dh.setConfiguration(c)
	global dhG
	try:
		dh.claimInterface(i)
		dhG=dh
	except usb.USBError:
		print "					INTERFACE WAS BUSY; RELEASING..."
		dhG.releaseInterface()
		#dh.releaseInterface()
		dh.claimInterface(i)
		dhG=dh
	return {"hnd":dh,"in":ei,"out":eo}


def connect(device_info): # sends command used by MMeter software when pressing the "Connect" button
	device_info["hnd"].controlMsg(0x21,0x9,(0x80,0x25,0,0,3),0x300)

def disconnect(device_info): # sends command used by MMeter software when pressing the "Disconnect" button
	device_info["hnd"].controlMsg(0x22,0x9,(0x80,0x25,0,0,3),0x300)
	
def ask(device_info): # causes the multimeter to dump a packet of data (401 bytes)
	device_info["hnd"].bulkWrite(device_info["out"],(2,0x5a,0,0,0,0,0,0))

	
def connect2(di):
	connect(di)
	dump(di)

def disconnect2(di):
	disconnect(di)
	dump(di)
	
def ask2(di):
	ask(di)
	dump(di)
	
	
def dumpRaw(di, maxt=0, maxtrains=0): #prints all bytes read
	import time
	t0=time.clock()
	bytesRead=0
	emptyTrains=0
	try:
		while True:
			output=di["hnd"].bulkRead(di["in"],8)
			actualBytesInOutput=output[0] & 15
			bytesRead+=actualBytesInOutput
			t=time.clock()-t0
			printout= "%06d" % (t*1000)
			if actualBytesInOutput>0:
				if emptyTrains>0:
					printout= "(%d ms, %d trains empty...)\n%s"%((t-te)*1000,emptyTrains,printout)
					emptyTrains=0
				for n in output:
					printout+= " %02X" % (n)
				printout+="\t%d\n" % bytesRead
			else:
				if emptyTrains==0:
					te=t
				emptyTrains+=1
				printout+="\r"
			print printout,
			if maxt!=0 and t>maxt:
				break
			if maxtrains!=0 and bytesRead>0 and emptyTrains>maxtrains:
				break
	except KeyboardInterrupt:
		print


def dumpRawSM(di, maxt=0): #prints all bytes read, distinguishing probable stale data and valid data
	import time
	t0=time.clock()
	t=0
	bytesRead=0
	emptyTrains=0
	state=0
	try:
		while (not (maxt!=0 and t>maxt)) and (not(bytesRead>0 and emptyTrains>5)):
			output=di["hnd"].bulkRead(di["in"],8)
			actualBytesInOutput=output[0] & 15
			t=time.clock()-t0
			printout= "%06d" % (t*1000)
			if actualBytesInOutput>0:
				if emptyTrains>3 or bytesRead>0:
					bytesRead+=actualBytesInOutput
				if emptyTrains>0:
					printout= "(%d ms, %d trains empty...)\n%s"%((t-te)*1000,emptyTrains,printout)
					emptyTrains=0

				for n in output:
					printout+= " %02X" % (n)
				printout+="\t%s\n" % (bytesRead if bytesRead>0 else "STALE")
			else:
				if emptyTrains==0:
					te=t
				emptyTrains+=1
				printout+="\r"
			print printout,
			# if maxt!=0 and t>maxt:
				# break
			# if state==1 and emptyTrains>5:
				# break
	except KeyboardInterrupt:
		print


		
def dump(di):  #prints data bytes (cleans headers and padding zeros used by serial comm)
	import time
	t0=time.clock()
	bytesRead=0
	try:
		while True:
			output=di["hnd"].bulkRead(di["in"],8)
			actualBytesInOutput=output[0] & 15
			bytesRead+=actualBytesInOutput
			t=time.clock()-t0
			print "%06d" % (t*1000),
			for n in output[1:actualBytesInOutput]:
				print "%02X" % (n),
			print		
	except KeyboardInterrupt:
		pass
	
		
def close(di):
	#print "				CLOSING INTERFACE"
	di["hnd"].releaseInterface()

	
def printGraphValues(di,maxval=100): #prints the values that make up the graph, with value conversion and spacing the divisions
	data=getAnswer2(di,300)
	#print len(data),"bytes:"
	overloads=0;
	vertical_offset=data[12]
	
	for i in range(41,min(len(data),maxval)):
		if (i-41)%40==0:
			print
		o=data[i]
		print o if o<127 else -(255-o),
		if o==90:
			overloads+=1;
	print "length=",len(data)," overloads=",overloads," len-ol/2=",len(data)-overloads/2
	return
		

def printValues(di): #print 50 header bytes
	import time
	t0=time.clock()
	bytesRead=0
	t=0
	emptyTrains=0
	while  not( t>timeout or (emptyTrains>5 and bytesRead>0)):
		#print bytesRead," ",emptyTrains," ",t
		output=di["hnd"].bulkRead(di["in"],8)
		t=time.clock()-t0
		#print "%06d" % (t*1000),
		actualBytesInOutput=output[0] & 15
		if actualBytesInOutput==0:
			emptyTrains+=1
		else:
			emptyTrains=0
		bytesRead+=actualBytesInOutput
		if bytesRead in range(0,50):
			for n in range(1,actualBytesInOutput+1):
				o=output[n]
				print "%02X " % (o),
	print
	print "\nRead %d bytes in %f secs; emptyTrains == %d" % (bytesRead, t, emptyTrains)
	return bytesRead

def getAnswer(di): #return list of read bytes; stop reading when timeout or when 10 empty trains appear after some bytes were already read
	import time
	result=()
	t0=time.clock()
	bytesRead=0
	t=0
	emptyTrains=0
	while  not( t>timeout or (emptyTrains>200 and bytesRead>0)):  #stop conditions: timeout OR (some bytes read AND 200 consecutive empty trains)
	#while  not(emptyTrains>5 and bytesRead>0):
		#print " ",bytesRead," ",emptyTrains," ",t,"\r",
		output=di["hnd"].bulkRead(di["in"],8)
		t=time.clock()-t0
		actualBytesInOutput=output[0] & 15
		emptyTrains= 0 if actualBytesInOutput!=0 else emptyTrains+1
		bytesRead+=actualBytesInOutput
		result+=output[1:actualBytesInOutput+1]
	print bytesRead," ",emptyTrains," ",t
	return result	
		
		
def getAnswer2(di,maxEmptyTrains=150): #return list of read bytes; stop reading when good answer, or timeout or when 150 empty trains appear after some bytes were already read
	import time
	result=()
	t0=time.clock()
	bytesRead=0
	t=0
	emptyTrains=0
	gotGoodAnswer=False
	while  not( t>timeout or (emptyTrains>maxEmptyTrains and bytesRead>0) or gotGoodAnswer):  #stop conditions: timeout OR (some bytes read AND x consecutive empty trains)
	#while  not(emptyTrains>5 and bytesRead>0):
		#print " ",bytesRead," ",emptyTrains," ",t,"\r",
		output=di["hnd"].bulkRead(di["in"],8)
		t=time.clock()-t0
		actualBytesInOutput=output[0] & 15
		emptyTrains= 0 if actualBytesInOutput!=0 else emptyTrains+1
		bytesRead+=actualBytesInOutput
		result+=output[1:actualBytesInOutput+1]
		# if len(result) in (41,361) and result[0:2]==(0x5a,0) :
			# gotGoodAnswer=True
	#print bytesRead," ",emptyTrains," ",t
	return result	
				
		
		
def go(n=0): #ask, clear presumed stale buffer, print first 50 data bytes
	global dhG
	di=init(n)
	dhG=di
	try:
		connect(di)
		ask(di)
		#clearBuffer(di)
		numbytes=printValues(di)
		disconnect(di)
	finally:
		close(di)
	return numbytes>0

def go2(nd=0,nr=1): #ask nr times, print raw response until ^C
	global dhG
	di=init(nd)
	dhG=di
	try:
		connect(di)
		# dumpRaw(di)
		for i in range(0,nr):
			ask(di)
			dumpRaw(di,0,300)
		disconnect(di)
	finally:
		close(di)
		
def go3(n): #like go() but repeatedly
	global dhG
	di=init(n)
	dhG=di
	try:
		connect(di)
		while True:
			clearBuffer(di)
			ask(di)
			printGraphValues(di,1000)
			print
		disconnect(di)
	finally:
		close(di)
	return numbytes>0
		
		
def clearBuffer(di):
	#we want 10 consecutive reads bearing 0 data bytes to be sure that there is no stale data waiting.
	emptyTrains=0
	while emptyTrains<10:
		output=di["hnd"].bulkRead(di["in"],8)
		actualBytesInOutput=output[0] & 15
		if actualBytesInOutput==0:
			emptyTrains+=1
		else:
			emptyTrains=0
			print "B"
		
def go4(n): # to see the first 20 header bytes, their changes and the ASCII reading.
	import time
	global dhG
	di=init(n)
	dhG=di
	oldData=data=()
	tOldData=0
	spinner="/\\"
	s=0
	t0=time.clock()
	try:
		connect(di)
		while True:
			while True:
				ask(di)
				#clearBuffer(dh)
				print "\x08\x08%s" % (spinner[s]),
				s+=1
				if s==len(spinner):
					s=0
				t=time.clock()-t0
				data=getAnswer(di)
				if data[0:2]==(0x5A, 0):
					break
				if data==():
					print "timeout"
				else:
					print "bad answer,",len(data),"bytes:"
					break
			printout=""
			somethingChanged=False
			for i in range(0,21):
				try:
					if data[i]==oldData[i]:
						printout+= ".. "
					else: 
						printout+= "%02X " % (data[i])
						#somethingChanged=True
				except IndexError:
					printout+= "   " if len(data)<=i else "%02X " % (data[i])
					#somethingChanged=True
			for i in range(21,41):	#ASCII decoding
				try:
					c=chr(data[i]) if data[i]!=0 else '_'
					#if data[i]==oldData[i]:
					#	printout+= " "
					#else: 
					printout+=c
				except IndexError:  #part of the expected ASCII is missing! mark with *
					printout+= '*'					
			#print "=",
			#if somethingChanged:
			if oldData!=data:
				print "\r", printout, t-tOldData
				if not len(data) in (361,41):
					print "LENGTH WAS",len(data)
			else:
				print ".\x08\x08",
			oldData=data
			tOldData=t
		disconnect(di)
	finally:
		close(di)	

def go5(nd=0,nr=1): #repeat nr times (ask + dumpraw), print raw response until ^C
	global dhG
	import time
	di=init(nd)
	dhG=di
	try:
		connect(di)
		for i in range(0,nr):
			ask(di)
			dumpRaw(di)
		disconnect(di)
	finally:
		close(di)
		
def go6(nd=0,nr=1, maxt=0): #repeat nr times (ask + dumpraw + wait n secs), print raw response until ^C
	global dhG
	import time
	di=init(nd)
	dhG=di
	try:
		connect(di)
		print "Initial read to clear pending data..."
		dumpRawSM(di, maxt) 
		for i in range(0,nr):
			print "Asking..."
			ask(di)
			dumpRawSM(di, maxt)
			if maxt!=0:
				print "Waiting",maxt+1
				time.sleep(maxt+1)
		disconnect(di)
	finally:
		close(di)
		
def go7(nd=0,nr=1, maxt=0): #just dump whatever is read, without requesting anything. Useful to make sure there are no requests queued.
	global dhG
	import time
	di=init(nd)
	dhG=di
	try:
		connect(di)
		dumpRawSM(di, maxt)
		disconnect(di)
	finally:
		close(di)
		
def identify_multimeters():
	import usb
	timescale = {
		6 : "100ns",
		7 : "200ns",
		8 : "500ns",
		9 : "1us",
		0xA : "2us",
		0xB : "5us",
		0xC : "10us",
		0xD : "20us",
		0xE : "50us",
		0xF : "100us",
		0x10: "200us",
		0x11: "500us",
		0x12: "1ms",
		0x13: "2ms",
		0x14: "5ms",
		0x15: "10ms",
		0x16: "20ms",
		0x17: "50ms",
		0x18: "100ms",
		0x19: "200ms",
		0x1A: "500ms",
		0x1B: "1s",
		0x1C: "2s",
		0x1D: "5s"
		}
	modes_voltage = {
		0 : "20mV",
		1 : "50mV",
		2 : "100mV",
		3 : "200mV",
		4 : "500mV",
		5 : "1V",
		6 : "2V",
		7 : "5V",
		8 : "10V",
		9 : "20V",
		0xA: "50V",
		0xB: "100V",
		0xC: "200V",
		0xD: "%00V"
		}
	modes_amperage = {
		3 : "200uA",
		4 : "500uA",
		5 : "1mA",
		9 : "20mA",
		0xA: "50mA",
		0xB: "100mA",
		0xF: "2A",
		0x10: "5A"
		}
	bs=usb.busses()
	print len(bs), " busses found"
	
	for b in bs:
		#print "bus: ",b
		ds=b.devices
		print len(ds), " devices found"		
		for i in range(0,len(ds)):
			print
			state=0
			d=ds[i]
			print "DEVICE IDENTIFICATION: PID: %04X, VID: %04X, devnum: %X" % (d.idVendor, d.idProduct, d.devnum)
			dh=d.open()
			state=1
			print "DEVICE DETAILS: manuf:",dh.getString(d.iManufacturer,1000),", SN:",dh.getString(d.iSerialNumber,1000),", Product description:",dh.getString(d.iProduct,1000),", dev version:", d.deviceVersion
			c=d.configurations[0]
			ifs=c.interfaces
			i=ifs[0][0]
			es=i.endpoints
			for e in es:
				if e.address>=128:
					ei=e.address
				else:
					eo=e.address
			dh.setConfiguration(c)
			di={"hnd":dh,"in":ei,"out":eo}
			global dhG
			try:
				dh.claimInterface(i)
				state=2
				connect(di)
				state=3
				tries=0
				while tries<4:
					print "Asking for multimeter data:",
					ask(di)
					state=4
					#clearBuffer(di)
					data=getAnswer(di)
					if data[0:4]==(0x5A, 0, 3, 5):
						break
					tries+=1
					if data==():
						print "timeout..."
					else:
						print "unexpected answer..."
				if tries==4:
					#we arrived here because there was no good answer
					print "This device does not answer as expected from a Multimeter. If it is, please turn it off and disconnect the cable; then, reconnect, and turn on the multimeter."
					continue
				#if we are here, we had no USB error, no timeout and no bad data, so must be a good answer
				print "Got data!"
				print "STATUS:"
				print "Vertical scale:",
				mode=data[6]
				if mode==0x80:
					print modes_voltage[data[11]],
				elif mode==0x81:
					print modes_amperage[data[11]],
				else:
					print "Mode is not Voltage nor Amperage measurement",
					
				if data[9]==1:
					print "[AUTO]"
				

				print "Time scale:",timescale[data[13]],
				if data[8]==1:
					print "[AUTO]"
				
				print "Graph:","running" if data[7]==1 else "held"
				print "Readout:",
				printout=""
				for i in range(20,40): 	#ASCII decoding
					try:
						c=chr(data[i]) if data[i]!=0 else ' '
						printout+=c
					except IndexError:  #part of the expected ASCII is missing! 
						printout+= ' '				
				print printout
				
				disconnect(di)
				state=5
			finally:
				if state==1:
					print "USB communication error"
				elif state in range(2,5):
					print "Something happened! state=",state
					close(di)	
					
					
					
if __name__ == "__main__":
	identify_multimeters()