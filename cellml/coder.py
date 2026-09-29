from libcellml import AnalyserModel, Generator, GeneratorProfile, Model, Printer
from .analyser import parse_model,analyse_model_full,flatten_model
from .utilities import validate_file_path
from pathlib import Path
"""
=================
Code generation
=================
This module contains functions for generating code from a CellML model.

The following functions are defined:
    * writeCellML: write a CellML model to a CellML file.
    * writePythonCode: generate python file from a CellML model.
"""

def writeCellML(model: Model, full_path: str) -> None:  
    """ 
    Write a CellML model to a CellML file.

    Parameters
    ----------
    model: Model
        The CellML model to be written.
    full_path: str
        The full path of the CellML file (including the file name and extension).

    Side effect
    -----------
    The CellML model is written to the specified file.
    """
    
    printer = Printer()
    serialised_model = printer.printModel(model)
    full_path_ = validate_file_path(full_path) 
    if full_path_:
        with open(full_path_, "w") as f:
            f.write(serialised_model)
        print('CellML model saved to:',full_path)   

def writeCellML_flat(model: Model, full_path: str, base_dir: str|Path,strict_mode=True)-> None:  
    """ 
    Write a CellML model to a CellML file after flattening it.

    Parameters
    ----------
    model: Model
        The CellML model to be written.
    full_path: str
        The full path of the CellML file (including the file name and extension).
    base_dir: str|Path
        The base directory of the CellML model.
    strict_mode: bool
        If True, the model is checked against the CellML 2.0 specification.

    Side effect
    -----------
    The CellML model is written to the specified file.
    """
    flat_model, issues = flatten_model(model, base_dir, strict_mode)
    if flat_model is not None:
        writeCellML(flat_model, full_path)
    else:
        print('Error: Unable to flatten the model. Issues:', issues)   

def writePythonCode(analyser_model:AnalyserModel, full_path):
    """ 
    Generate Python code from a CellML model
    and write the code to the specified file.

    Parameters
    ----------
    analyser_model: AnalyserModel
        The AnalyserModel instance of the CellML model.
    full_path: str
        The full path of the python file (including the file name and extension).

    Side effect
    -----------
    The python code is written to the specified file.
    """

    generator = Generator()
    profile = GeneratorProfile(GeneratorProfile.Profile_PYTHON)
    implementation_code_python = generator.implementationCode(analyser_model, profile)                   
    full_path_ = validate_file_path(full_path) 
    if full_path_:
        with open(full_path_, "w") as f:
            f.write(implementation_code_python)

def toCellML2(oldPath, newPath, external_variables_info={},strict_mode=True, py_full_path=None):
    """ 
    Convert a CellML 1.X model to CellML 2.0.

    Parameters
    ----------
    oldPath: str
        The full path of the CellML 1.X file (including the file name and extension).
    newPath: str
        The full path of the CellML 2.0 file (including the file name and extension).
    external_variables_info: dict
        A dictionary of external variables information, in the format of {id:{'component': , 'name': }}.
        Empty by default.
    strict_mode: bool
        If True, the model is checked against the CellML 2.0 specification.
    py_full_path: str
        The full path of the python file (including the file name and extension).    

    Side effect
    -----------
    The new CellML 2.0 model is written to the specified file.
    If the model is valid, the python code is written to the specified file.
    """
    try:
        model_parse, issues=parse_model(oldPath, False)
    except Exception as e:
        print(f"Error parsing the model from {oldPath}: {e}")
        return
    if model_parse is None:
        print(f"Error: Unable to parse the model from {oldPath}. Issues: {issues}")
        return     
    writeCellML(model_parse,newPath)
    base_dir=Path(newPath).parent
    analyser_model,issues=analyse_model_full(model_parse,base_dir,external_variables_info,strict_mode)
    print(issues)
    if py_full_path is not None and analyser_model is not None:
        writePythonCode(analyser_model, py_full_path)
    