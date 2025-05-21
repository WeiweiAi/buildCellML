from libcellml import cellmlElementTypeAsString,Annotator

def annotateModel(model):

    annotator = Annotator()
    annotator.setModel(model)
    duplicatedIds = annotator.duplicateIds()
    for duplicatedId in duplicatedIds:
        allItems = annotator.items(duplicatedId)
        for item in allItems:
            annotator.assignId(item)
    annotator.assignAllIds()

    return annotator

def getAnnotator(model):
    annotator = Annotator()
    annotator.setModel(model)
    return annotator

def getElementByID(annotator, elementID):
    """ Get a CellML element by ID in a annotator
    
    Parameters
    ----------
    model: libcellml Annotator instance
        The annotator to search in
    elementID: string
        The ID of the element to search for
    
    Raises
    ------
    ValueError
        If the element is not found in the model
        or if the element type is not supported
        
    Returns
    -------
    tuple
        (string, CellML element)
        The type of the element and the element found
    """
    cellElement=annotator.item(elementID)
    if cellElement:
        if cellmlElementTypeAsString(cellElement.type())== 'MODEL':
            return 'MODEL', cellElement.model()
        elif cellmlElementTypeAsString(cellElement.type())== 'COMPONENT':
            return 'COMPONENT', cellElement.component()
        elif cellmlElementTypeAsString(cellElement.type())== 'VARIABLE':
            return 'VARIABLE', cellElement.variable()
        elif cellmlElementTypeAsString(cellElement.type())== 'RESET':
            return 'RESET', cellElement.reset()
        elif cellmlElementTypeAsString(cellElement.type())== 'IMPORT':
            return 'IMPORT', cellElement.importSource()
        elif cellmlElementTypeAsString(cellElement.type())== 'UNITS':
            return 'UNITS', cellElement.units()
        elif cellmlElementTypeAsString(cellElement.type())== 'UNIT':
            return 'UNIT', cellElement.unitsItem()
        elif cellmlElementTypeAsString(cellElement.type())== 'CONNECTION' or cellmlElementTypeAsString(cellElement.type())== 'MAP_VARIABLES': # need to check
            return 'CONNECTION', cellElement.variablePair()
        else:
            raise ValueError('Element type not supported: '+cellmlElementTypeAsString(cellElement.type()))
    else:
        raise ValueError('Element not found in annotator or multiple elements found: '+elementID)


def getVariableInfo(annotator, variableID):
    """ Get information about a variable in a annotator
    
    Parameters
    ----------
    model: libcellml Annotator instance
        The annotator to search in
    variableIDs: string
        The ID of the variable to search for
    
    Raises
    ------
    ValueError
        If the variable is not found in the model
        
    Returns
    -------
    variable
        The variable found
    """    
    variable=annotator.variable(variableID)
    if variable:
        pass         
    else:
        raise ValueError('Variable not found in annotator: '+variableID)
    return variable
