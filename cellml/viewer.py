from __future__ import annotations
from libcellml import  Model, Component, Variable

def view_components(model: Model,print_details: bool = True) -> list:
    """Prints the components of a CellML model."""
    spacer = "  - "
    print("Model '{m}' has {c} components".format(m=model.name(), c=model.componentCount()))
    components = []
    for i in range(model.componentCount()):
        child_component = model.component(i)
        if print_details:
            print_component_only_to_terminal(child_component, spacer)
        components.append(child_component)
    print()
    return components

def print_component_only_to_terminal(component: Component, spacer: str):
    print("{s}Component '{c}' has {n} child components".format(
        s=spacer,
        c=component.name(),
        n=component.componentCount()))

    for c in range(0, component.componentCount()):
        another_spacer = "    " + spacer
        child_component = component.component(c)
        print_component_only_to_terminal(child_component, another_spacer)
    print()

def view_equivalent_variables(variable: Variable) -> list:
    """Prints the equivalent variables of a CellML variable."""
    if variable is None:
        print("Variable is None")
        return
    variable_list = []
    variable_list.append([variable.name(),
                         variable.parent().name(),
                         variable.units().name(),
                         variable.initialValue()])
    _list_equivalent_variables(variable, variable_list)

    return variable_list

def _list_equivalent_variables(variable: Variable, variable_list: list):
    if variable is None:
        return
    for i in range(0, variable.equivalentVariableCount()):
        equivalent_variable = variable.equivalentVariable(i)
        # Form a list of strings that describe the equivalent variable.
        test = [equivalent_variable.name(),
                equivalent_variable.parent().name(),
                equivalent_variable.units().name(),
                equivalent_variable.initialValue()]
        # If the equivalent variable has not already been checked, then start another recursion.
        if test not in variable_list:
            variable_list.append(test)
            _list_equivalent_variables(equivalent_variable, variable_list)

def group_variables(model: Model) -> list:
    """Groups the variables of a CellML model by their equivalence."""
    variable_groups = []
    for i in range(model.componentCount()):
        component = model.component(i)
        for j in range(component.variableCount()):
            variable = component.variable(j)
            # Check if the variable is already in a group
            found = False
            for group in variable_groups:
                if variable in group:
                    found = True
                    break
            if not found:
                # Create a new group for this variable and its equivalents
                new_group = []
                _list_equivalent_variables(variable, new_group)
                variable_groups.append(new_group)
    return variable_groups