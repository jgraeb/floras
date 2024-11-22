'''
Grid class saving the layout of the grid world including labels and colors.
'''
from ipdb import set_trace as st

class Grid():
    def __init__(self,file, labels_dict = {}, color_dict={}):
        self.labels = labels_dict
        self.colors = color_dict
        self.map, self.len_y, self.len_x = self.get_map(file)
        self.cuts = []

    def get_map(self, file):
        map = {}
        f = open(file, 'r')
        lines = f.readlines()
        len_y = len(lines)
        for i,line in enumerate(lines):
            for j,item in enumerate(line):
                if item != '\n' and item != '|':
                    map.update({(i,j): item})
                    len_x = j
        len_x += 1
        return map, len_y, len_x
    
    def add_cuts(self,cuts):
        self.cuts = cuts

    def transition_specs(self, ystr, xstr):
        ''' 
        LTL spec encoding n-e-s-w movement on the grid (excluding obstacles).
        Only encoding movement on the grid, no fuel level or other auxiliary variables.
        '''
        dynamics_spec = set()
        rmoves = [(-1,0),(1,0), (0,-1), (0,1)]

        for ii in range(0,self.len_y):
            for jj in range(0,self.len_x):
                if not self.map[(ii,jj)] == '*':
                    next_steps_string = '('+ystr+' = '+str(ii)+' && '+xstr+' = '+str(jj)+')'
                    for rmove in rmoves:
                        newr = (ii+rmove[0],jj+rmove[1])
                        if newr in self.map and not self.map[newr] == '*':
                            next_steps_string = next_steps_string + ' || ('+ystr+' = '+str(item[0])+' && '+xstr+' = '+str(item[1])+')'
                    dynamics_spec |= {'('+ystr+' = '+str(ii)+' && '+xstr+' = '+str(jj)+') -> X(('+ next_steps_string +'))'}
        return dynamics_spec