class Waveplate():
    def __init__(self, id,  oa=0):
        self.ID = id
        self.OA = oa
        
    def setOA(self, oa):
        #update the optical axis 
        self.OA = oa