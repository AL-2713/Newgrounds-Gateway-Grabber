import zlib
import re

class variableExtractor:
    
    def getVars(self, fileLocation):
        self.zlibConpressedHeader = b"\x43\x57\x53"
        self.variableEnd = b"\x00"
        
        if fileLocation[-3:] != "swf":
            print("! Extractor needs an swf file")
            return []
        
        rawData = open(fileLocation, 'rb').read()
        
        if rawData[:3] == self.zlibConpressedHeader:
            return self.cwsExtract(rawData)
        
        return []
    
    def cwsExtract(self, rawData):
        decompData = zlib.decompress(rawData[8:])
        encKey = self.extractVariable(decompData, "encryptionKey")
        app_id = self.extractVariable(decompData, "apiId", 2)
        
        return [encKey, app_id]
        
    
    def extractVariable(self, binaryData, variable, nest = 1):
        byteCheck = b"\x00\x00" + variable.encode() + b"\x00\x00"
        regexVars = {"encryptionKey": [b"\x20[a-zA-Z0-9]{32}[^\x20-\x7E]", b"\x00[a-zA-Z0-9]{32}\x00"], "apiId": [b"\x0E\d+:\w{8}", b"\x00\d+:\w{8}"]}
        
        if byteCheck in binaryData:
            variableResult = binaryData.split(byteCheck)[nest].split(self.variableEnd)[0]
            return variableResult.decode().strip()
        
        # Regex check if previous logic didnt work
        regexCheck = regexVars[variable]
        for x in regexCheck:
            regFind = re.findall(x, binaryData)
            if len(regFind) > 0:
                textResult = regFind[0].decode()[1:].strip()
                
                if variable == "encryptionKey":
                    textResult = textResult[:32]
                
                return textResult
            

        print("Variable " + variable + " was not found")
        return None