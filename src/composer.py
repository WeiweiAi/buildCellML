from .analyser import parse_model
from .coder import writeCellML, analyse_model_full
from .annotator import getAnnotator, getVariableInfo
from .builder import create_model,create_component, import_setup,importComponents,create_variable,add_variable,varmap,infix_to_mathml,add_equations, check_equivalence_list

def collect_variable_info(map_dict):
    """ 
    Collect information about the variables in a CellML model.
    
    Parameters
    ----------
    model: Model
        The CellML model to collect variable information from.
    
    Returns
    -------
    dict
        A dictionary of variable information.
        The keys are the component names and the values are dictionaries of variable information.
    """
    for model_fullpath, var_map in map_dict.items():
        model = parse_model(model_fullpath)
        annotator = getAnnotator(model)
        for bg_variable in var_map:
            cellml_variables = []
            for cellml_variableID in var_map[bg_variable]:
                try:
                    cellml_variable = getVariableInfo(annotator, cellml_variableID)
                    cellml_variables.append(cellml_variable)          
                except ValueError as e:
                    print(e)
            if check_equivalence_list(cellml_variables):
                map_dict[model_fullpath][bg_variable] = cellml_variables[0]
            else:
                raise('more than one variable found for:',bg_variable)
    return map_dict

def compose_model(map_dict, model_path):

    # create a new model
    model = create_model('composed_model')
    # add a component to the model
    new_component = create_component('composed_component')
    model.addComponent(new_component)

    for full_path_imported_model, variable_info in map_dict.items():
        importSource, import_model =import_setup(model_path,full_path_imported_model)         
        for bg_variable, variable in variable_info.items():
            # import component
            component_name=variable.parent().name()
            if importComponents(model,importSource,{component_name:import_model.component(component_name)}):
                # add variables to the new component
                variable_units = variable.units()
                new_variable_name = bg_variable
                new_variable=create_variable(new_variable_name, variable_units, None, interface_type='public')
                add_variable(new_component,new_variable)
                if varmap(new_variable,variable):
                    pass
                else: 
                    raise('Failed to map variable:',new_variable_name)
            else:
                raise('Failed to import component:',component_name)
    equations=[]                
    for equation in map_dict['conservation_laws']: 
        yvar=equation['yvar']
        infix=equation['infix']
        mathstr=infix_to_mathml(infix, yvar)
        equations.append(mathstr)
    add_equations(new_component, equations)

    return model
