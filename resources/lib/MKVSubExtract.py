import os
import re
import threading
import subprocess

def log(*args):
    for arg in args:
        print arg

class MKVExtractor:
    def __init__(self, toolsDir=''):
        self.toolsDir = toolsDir
        self.progress = 0

    def getSubTrack(self, filePath):
        '''Uses mkvinfo to find the track that contains the subtitles'''
        infoPath = os.path.join(self.toolsDir, "mkvinfo")
        log('path to executable mkvinfo: %s' % infoPath)
        proc = subprocess.Popen([infoPath, filePath], stdout=subprocess.PIPE, shell=True)
        output = proc.communicate()[0]
        
        tracks = {}
        trackNumber = None
        for line in output.splitlines():
            r = re.search('[+] Track number: (\d+)', line)
            if r:
                trackNumber = int(r.group(1))
                trackID = trackNumber
                r = re.search('track ID .*: (\d+)', line)
                if r:
                    trackID = int(r.group(1))
                tracks[trackNumber] = { 'TID': trackID }
                continue
    
            r = re.search('[+] Track type: (.+)', line)
            if r:
                trackType = r.group(1)
                tracks[trackNumber]['type'] = trackType
                continue
    
            r = re.search('[+] Language: (.+)', line)
            if r:
                language = r.group(1)
                tracks[trackNumber]['language'] = language
                continue
            
            r = re.search('[+] Codec ID: (.+)', line)
            if r:
                codec = r.group(1)
                tracks[trackNumber]['codec'] = codec
                continue
        
        subTrackID = None
        for track in tracks.values():
            if track['type'] != 'subtitles':
                continue
            if 'language' in track and track['language'] != 'eng':
                continue
            if 'codec' in track and track['codec'] != 'S_TEXT/UTF8':
                continue
            subTrackID = track['TID']
            break
        
        return subTrackID
    
    def startExtract(self, filePath, trackID):
        self.progress = 0
        extractPath = os.path.join(self.toolsDir, "mkvextract")
        self.srtPath = os.path.splitext(filePath)[0] + ".srt"
        args = [extractPath, "tracks", filePath, str(trackID) + ':' + self.srtPath]
        log('executing args: %s' % args)
        
        self.proc = subprocess.Popen(args, stdout=subprocess.PIPE,shell=True, universal_newlines=True)
        
        self.mThread = threading.Thread(target=self.monitorThread)
        self.mThread.setDaemon(True)
        self.mThread.start()
        
    def monitorThread(self):
        '''Monitor Thread is running as long as the process is running'''
        outfile=self.proc.stdout

        log("Starting to read stdout from mkvextract")
        while not self.proc.poll(): 
            line = outfile.readline()
            #log('line received: %s' % line)
            if not len(line):
                break

            # extract percentages from string "Progress: n%"
            r = re.search('Progress:\s+(\d+)', line)
            if r:
                self.progress = int(r.group(1))
            
        log("Ending execution")
        try:
            self.proc.terminate()
        except:
            pass
    
    def cancelExtract(self):
        returnCode = self.proc.poll()
        if returnCode is not None:
            return
        self.proc.kill()
        
    def isRunning(self):
        return self.mThread.isAlive()
    
    def getSubFile(self):
        if self.progress != 100:
            if self.proc.poll() == 0:
                self.srtPath
        return self.srtPath
