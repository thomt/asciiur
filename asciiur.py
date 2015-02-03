
from PIL import Image, ImageFont, ImageDraw, ImageSequence
import glob, re, time, random, sys, os, fractions
from bisect import bisect
from images2gif import writeGif


WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

def analyseImage(path):
    im = Image.open(path)
    results = {
        'size': im.size,
        'mode': 'full',
    }
    try:
        while True:
            if im.tile:
                tile = im.tile[0]
                update_region = tile[1]
                update_region_dimensions = update_region[2:]
                if update_region_dimensions != im.size:
                    results['mode'] = 'partial'
                    break
            im.seek(im.tell() + 1)
    except EOFError:
        pass
    return results

def processImage(path):
    mode = analyseImage(path)['mode']
    im = Image.open(path)
    frames = []
    p = im.getpalette()
    last_frame = im.convert('RGBA')
    
    try:
        while True:
            
        	if not im.getpalette():
        		im.putpalette(p)
            
        	new_frame = Image.new('RGBA', im.size)
            
         	if mode == 'partial':
        	    new_frame.paste(last_frame)
            
        	new_frame.paste(im, (0,0), im.convert('RGBA'))
        	
        	ascii_frame = asciify(new_frame)
        	frames.append(ascii_frame)
        	last_frame = new_frame
        	im.seek(im.tell() + 1)
    except EOFError:
        pass

    return frames

'''
resizes the largest dimension of the frame to the specified max_dimen and scales
the remaining dimension to a percentage relative to max_dimen

'''
def scale(frame, max_dimen=150):
	(width, height) = frame.size
	if width > height:
		scale_percent = float(height) / float(width)
		height = int(max_dimen * float(scale_percent))
		width = max_dimen
	else:
		scale_percent = float(width) / float(height)
		width = int(max_dimen * float(scale_percent))
		height = max_dimen

	return (width, height)

def asciify(frame):
	# 7 tonal ranges, from lighter to darker.

	tones = [
				" ",
				".,",
				";`",
				"_-",
				"=+",
				"+~",
				"Xx",
				"#"
			]

	zonebounds=[36,72,108,144,180,216,252]

	# frame=frame.resize((96, 45), Image.BILINEAR)
	frame = frame.resize(scale(frame, 150), Image.ANTIALIAS)
	frame = frame.convert("L") # convert to mono - black & white

	string = ""
	tmp = ""
	strlist = []

	for y in range(0,frame.size[1]):
		for x in range(0,frame.size[0]):
			lum = 255 - frame.getpixel((x,y))
			row = bisect(zonebounds,lum)
			tonal_range = tones[row]
			tonal_result = tonal_range[random.randint(0, len(tonal_range)-1)]
			string = string + tonal_result
			tmp = tmp + tonal_result
		strlist.append(tmp)
		tmp = ""
		string = string + "\n"

	im = txttoimage(strlist).convert("L")

	return im

def font_spacing(fonttype=None, fontsize=None):
	if fonttype == 'fonts/LiberationMono-Regular.ttf':
		return int((float(3) / float(5)) * fontsize+0.4)
	else:
		return 4

def txttoimage(strlist, fonttype='fonts/LiberationMono-Regular.ttf', fontsize=8, fontcolor=BLACK, bgcolor=WHITE):
	font = ImageFont.truetype(fonttype, fontsize)
	spacing = font_spacing(fonttype, fontsize)
	imgsize = font.getsize(strlist[0])
	img = Image.new("RGBA", (imgsize[0], (spacing * len(strlist))), bgcolor)
	draw = ImageDraw.Draw(img)
	yloc = 0

	for string in strlist:
		draw.text((0,yloc), string, fontcolor, font = font)
		yloc += spacing
		draw = ImageDraw.Draw(img)

	return img

def main(argv=None):

	start_time = time.time()
	filename = ''
	durations = []

	if argv is None:
		argv = sys.argv
		if len(argv) > 1:
			filename = str(sys.argv[1])
			parse_index = filename.rfind('/')
			output_name = filename[:parse_index+1] + 'ascii_' + filename[parse_index+1:]

		else:
			print "Error. No argument provided."
			sys.exit(0)

	print 'file: ' + filename 

	print 'asciifying gif frames...'
	frames = processImage(filename)

	orig_gif = Image.open(filename)

	for image in ImageSequence.Iterator(orig_gif):
		try:
			durations.append(image.info['duration'] / 1000.0)
		except KeyError:
			pass

	print 'assembling gif...'
	try:
		writeGif(output_name, frames, duration = durations)
	except IOError as errno:
		extra_files = glob.glob('._/*.gif')
		if extra_files:
			print str(errno) + ': cleaning up extraneous files'
			if file_ in extra_files:
				os.remove(file_)

	print "completed in %.2f seconds." % (time.time() - start_time)

if __name__ == "__main__":
    main()
