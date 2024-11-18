'''System under test, load a controller for a static environment.'''

class Agent:
    def __init__(self, name, pos, goals, grid):
        self.name = name
        self.s = pos
        self.y = pos[0]
        self.x = pos[1]
        self.goals = goals
        self.grid = grid
        self.controller = None
        self.isterminal = False

    def save_controller(self, controller):
        self.controller = controller

    def move(self):
        output = self.controller.move()
        self.x = output['x']
        self.y = output['y']
        self.s = (self.y,self.x)
        if self.controller.isterminal or self.s in self.goals:
            self.isterminal = True
