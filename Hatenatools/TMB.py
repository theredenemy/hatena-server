from PPM import AscDec, DecAsc, ThumbPalette


import numpy as np


class TMB:
	def __init__(self):
		self.Loaded = False
		self.Thumbnail = None
		self.RawThumbnail = None
	def ReadFile(self, path, DecodeThumbnail=False):
		f = open(path, "rb")
		ret = self.Read(f.read(), DecodeThumbnail)
		f.close()
		return ret
	def Read(self, data, DecodeThumbnail=False):
		if data[:4] != "PARA" or len(data) < 0x6a0:
			return False

		#Read the header:
		self.AudioOffset = AscDec(data[4:8], True) + 0x6a0#only stored for self.Pack()
		self.AudioLenght = AscDec(data[8:12], True)#only stored for self.Pack()

		self.FrameCount = AscDec(data[12:14], True) + 1
		self.Locked = ord(data[0x10]) & 0x01 == 1
		self.ThumbnailFrameIndex = AscDec(data[0x12:0x14], True)#which frame is in the thumbnnail

		#self.OriginalAuthorName = u"".join(unichr(AscDec(data[0x14+i*2:0x14+i*2+2], True)) for i in xrange(11)).split(u"\0")[0]
		#self.EditorAuthorName = u"".join(unichr(AscDec(data[0x2A+i*2:0x2A+i*2+2], True)) for i in xrange(11)).split(u"\0")[0]
		#self.Username = u"".join(unichr(AscDec(data[0x40+i*2:0x40+i*2+2], True)) for i in xrange(11)).split(u"\0")[0]
		self.OriginalAuthorName = data[0x14:0x2A].decode("UTF-16LE").split(u"\0")[0]
		self.EditorAuthorName = data[0x2A:0x40].decode("UTF-16LE").split(u"\0")[0]
		self.Username = data[0x40:0x56].decode("UTF-16LE").split(u"\0")[0]

		self.OriginalAuthorID = data[0x56:0x5e][::-1].encode("HEX").upper()
		self.EditorAuthorID = data[0x5E:0x66][::-1].encode("HEX").upper()#the last user to save the file

		self.OriginalFilenameC = data[0x66:0x78]#compressed
		self.CurrentFilenameC = data[0x78:0x8a]#compressed
		self.OriginalFilename = "%s_%s_%s.tmb" % (self.OriginalFilenameC[:3].encode("HEX").upper(), self.OriginalFilenameC[3:-2], str(AscDec(self.OriginalFilenameC[-2:], True)).zfill(3))
		self.CurrentFilename = "%s_%s_%s.tmb" % (self.CurrentFilenameC[:3].encode("HEX").upper(), self.CurrentFilenameC[3:-2], str(AscDec(self.CurrentFilenameC[-2:], True)).zfill(3))

		self.PreviousEditAuthorID = data[0x8a:0x92][::-1].encode("HEX").upper()#don't know what this really is

		self.PartialFilenameC = data[0x92:0x9a]#compressed

		self.Date = AscDec(data[0x9a:0x9e], True)#in seconds since midnight 1'st january 2000

		self.RawThumbnail = data[0xa0:0x6a0]
		if DecodeThumbnail:
			self.GetThumbnail()#self.Thumbnail[x, y] = uint32 RGBA

		self.Loaded = True
		#return the results
		return self
	def WriteFile(self, path):#not implented
		out = self.Pack()
		if out:
			f = open(path, "wb")
			f.write(out)
			f.close()
			return True
		else:
			return False
	def Pack(self, ppm=None):#not implented
		if not self.Loaded: return False

		#realself = self
		#if ppm: self = ppm

		out = ["PARA",#magic
			   DecAsc(self.AudioOffset-0x6a0, 4, True),#animation data size
			   DecAsc(self.AudioLenght, 4, True),#audio data size
			   DecAsc(self.FrameCount-1, 2, True),#frame count
			   "\x24\x00",#unknown
			   chr(self.Locked), "\0",#locked
			   DecAsc(self.ThumbnailFrameIndex, 2, True),#which frame is in the thumbnnail
			   self.OriginalAuthorName.encode("UTF-16LE") + "\0\0"*(11-len(self.OriginalAuthorName)),#Original Author Name
			   self.EditorAuthorName.encode("UTF-16LE") + "\0\0"*(11-len(self.EditorAuthorName)),#Editor Author Name
			   self.Username.encode("UTF-16LE") + "\0\0"*(11-len(self.Username)),#Username
			   self.OriginalAuthorID.decode("HEX")[::-1],#OriginalAuthorID
			   self.EditorAuthorID.decode("HEX")[::-1],#EditorAuthorID
			   self.OriginalFilenameC,#OriginalFilename
			   self.CurrentFilenameC,#CurrentFilename
			   self.PreviousEditAuthorID.decode("HEX")[::-1],#EditorAuthorID
			   self.PartialFilenameC,#PartialFilename
			   DecAsc(self.Date, 4, True),#Date in seconds
			   "\0\0",#padding
			   self.PackThumbnail()]#thumbnail

		return "".join(out)
	def GetThumbnail(self, force=False):
		if (self.Thumbnail is None or force):# and self.RawThumbnail:
			global ThumbPalette
			if not self.RawThumbnail:
				return False

			out = np.zeros((64, 48), dtype=">u4")

			#speedup:
			palette = ThumbPalette

			#8x8 tiling:
			for ty in range(6):
				for tx in range(8):
					for y in range(8):
						for x in range(0,8,2):
							#two colors stored in each byte:
							byte = ord(self.RawThumbnail[(ty*512+tx*64+y*8+x)/2])
							out[x+tx*8  , y+ty*8] = palette[byte & 0xF]
							out[x+tx*8+1, y+ty*8] = palette[byte >> 4]

			self.Thumbnail = out
		return self.Thumbnail
	def PackThumbnail(self, Exact=True, force=False):#more or less a private function for now
		palette =  (0xFEFEFEFF,#0
					0x4F4F4FFF,#1
					0xFFFFFFFF,#2
					0x9F9F9FFF,#3
					0xFF0000FF,#4
					0x770000FF,#5
					0xFF7777FF,#6
					0x00FF00FF,#7-
					0x0000FFFF,#8
					0x000077FF,#9
					0x7777FFFF,#A
					0x00FF00FF,#B-
					0xFF00FFFF,#C
					0x00FF00FF,#D-
					0x00FF00FF,#E-
					0x00FF00FF)#F-


		if not self.Thumbnail:
			return self.RawThumbnail
		else:
			if Exact:
				out = []

				#8x8 tiling:
				for ty in range(6):
					for tx in range(8):
						for y in range(8):
							for x in range(0,8,2):
								#two colors stored in each byte:
								#pos = 0xa0+(ty*512+tx*64+y*8+x)/2
								p1 = palette.index(int(self.Thumbnail[x+tx*8  , y+ty*8]))
								p2 = palette.index(int(self.Thumbnail[x+tx*8+1, y+ty*8]))
								out.append(chr(p2<<4 | p1))

				self.RawThumbnail = "".join(out)
				return self.RawThumbnail
			else:
				#not yet implented
				return False