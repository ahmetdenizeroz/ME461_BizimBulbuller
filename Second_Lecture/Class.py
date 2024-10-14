class stupidnamedclass():
    pass
class shape():
    '''
    Always start with explaining the intent of the class!!
    '''
    
    def __init__(me, name = "şog"):
        me.name = name
        me.__area__ = -1
        me.__preimater__ = -2
    
    def ShapeSay(them):
        print(f'This is {them.name} with area {me.area} and perimater {me.perimater} ')


class circle(shape):
    '''
    __init__ and ShapeSay is inherited
    '''
    pass

class square(shape):
    '''
    __init__ is not inherited, ShapeSay is inherited
    '''
    def __init__(you, L = 1, name = "This is a square"):
        you.who = 'john doe'
        super().__init__(name = name)
        you.__L = L
        you.area = L ** 2
        
    @property
    def Side(doesnotmatter):
        return doesnotmatter.__L
    @Side.setter
    def Side(thismatters, newValue):
        if newValue >= 0:
            thismatters.L = newValue
        else:
            print(f'{newValue} is not a good side value')
            print(f'{newValue} is preserved {thismatters.L}')
    
    def Area(self):
        return self.Side * self.__L

    def __str__(kim):
        return f'I am a square dude with side {kim.__L}'

    def __repr__(me2):
        return f'Square: {me2.Side}'

    def __add__(me, newGuy):
        '''let'S assume that adding two squares are simply adding sides'''
        return square(L = me.Side + newGuy.Side, name = "AddedSquare")
    
    def __eq__(ben, veo):
        return ben.Side == veo.Side
