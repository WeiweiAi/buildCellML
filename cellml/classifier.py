from __future__ import annotations
import json
from libcellml import Units,Variable, AnalyserModel
from enum import Enum, auto
from dataclasses import dataclass
from .analyser import parse_model
import rdflib
from .viewer import view_equivalent_variables
from .utilities import validate_file_path

class Domain(Enum):
    CHEMICAL = auto()
    MECHANICAL_TRANSLATIONAL = auto()
    MECHANICAL_ROTATIONAL = auto()
    ELECTRICAL = auto()
    HYDRAULIC = auto()
    UNKNOWN = auto()

class PhysicalRole(Enum):
    EFFORT = auto()
    FLOW = auto()
    QUANTITY = auto()
    MOMENTUM = auto()
    POWER = auto() 
    ENERGY = auto() 
    SIGNAL = auto()
    UNCLASSIFIED = auto()

# Lookup dictionary mapping OPB IDs to Bond Graph energy identities
OPB_ROLE_MAP: dict[str, tuple[Domain, PhysicalRole]] = {   
    
    # Chemical Domain
    "OPB_00378": (Domain.CHEMICAL, PhysicalRole.EFFORT),      # Chemical potential (J/mol)
    "OPB_00592": (Domain.CHEMICAL, PhysicalRole.FLOW),        # Chemical amount flow rate (fmol/s)
    "OPB_00593": (Domain.CHEMICAL, PhysicalRole.FLOW),        # Chemical amount density flow rate (mM/s, mol/m2/s,mol/m/s)
    "OPB_00425": (Domain.CHEMICAL, PhysicalRole.QUANTITY),    # Molar amount of chemical (fmol)
    "OPB_01528": (Domain.CHEMICAL, PhysicalRole.QUANTITY),    # Lineal concentration of chemical (mol/m)
    "OPB_01529": (Domain.CHEMICAL, PhysicalRole.QUANTITY),    # Areal concentration of chemical (mol/m2)
    "OPB_00340": (Domain.CHEMICAL, PhysicalRole.QUANTITY),    # Concentration of chemical (mM, mol/m3)

    # Mechanical Translational Domain
    "OPB_01482": (Domain.MECHANICAL_TRANSLATIONAL, PhysicalRole.EFFORT),   # Lineal mechanical force (N, J/m)
    "OPB_01053": (Domain.MECHANICAL_TRANSLATIONAL, PhysicalRole.EFFORT),     # Mechanical stress (J/m2)
    "OPB_00251": (Domain.MECHANICAL_TRANSLATIONAL, PhysicalRole.FLOW),     # Lineal translational velocity (m/s)
    "OPB_01220": (Domain.MECHANICAL_TRANSLATIONAL, PhysicalRole.FLOW),     # Material flow rate (kg/s)
    "OPB_00033": (Domain.MECHANICAL_TRANSLATIONAL, PhysicalRole.MOMENTUM), # Translational momentum (kg*m/s, N*s)
    "OPB_00269": (Domain.MECHANICAL_TRANSLATIONAL, PhysicalRole.QUANTITY), # Translational displacement (m)
    "OPB_01226": (Domain.MECHANICAL_TRANSLATIONAL, PhysicalRole.QUANTITY), # Mass of solid entity (kg)
    "OPB_01597": (Domain.MECHANICAL_TRANSLATIONAL, PhysicalRole.QUANTITY), # Lineal density of mass (kg/m)
    "OPB_01593": (Domain.MECHANICAL_TRANSLATIONAL, PhysicalRole.QUANTITY), # Areal density of mass (kg/m2)
    "OPB_01619": (Domain.MECHANICAL_TRANSLATIONAL, PhysicalRole.QUANTITY), # Volumnal density of matter (kg/m3)

    # Mechanical Rotational Domain
    "OPB_01656": (Domain.MECHANICAL_ROTATIONAL, PhysicalRole.FLOW),        # Joint rotational velocity(rad/s)
    #"OPB_01483": (Domain.MECHANICAL_ROTATIONAL, PhysicalRole.EFFORT),      # Rotational mechanical force  Torque, N*m
    "OPB_00163": (Domain.MECHANICAL_ROTATIONAL, PhysicalRole.MOMENTUM),    # Rotational momentum (N*m*s)
    "OPB_01434": (Domain.MECHANICAL_ROTATIONAL, PhysicalRole.QUANTITY),    # Joint rotational displacement (rad)

    # Electrical Domain
    "OPB_00506": (Domain.ELECTRICAL, PhysicalRole.EFFORT),   # Electrical potential (mV)
    "OPB_00318": (Domain.ELECTRICAL, PhysicalRole.FLOW),     # Charge flow rate (fA:C/s,C_per_m_s, C_per_m2_s, C_per_m3_s)
    "OPB_01521": (Domain.ELECTRICAL, PhysicalRole.MOMENTUM), # A momentum property that is proportional to the temporal differential of an electrical current, A/s
    "OPB_00411": (Domain.ELECTRICAL, PhysicalRole.QUANTITY), # Charge amount (fC)
    "OPB_01239": (Domain.ELECTRICAL, PhysicalRole.QUANTITY), # Charge lineal density (C/m)
    "OPB_01238": (Domain.ELECTRICAL, PhysicalRole.QUANTITY), # Charge areal density (C/m2)
    "OPB_01237": (Domain.ELECTRICAL, PhysicalRole.QUANTITY), # Charge volumetric density (C/m3)

    # Hydraulic Domain
    "OPB_00509": (Domain.HYDRAULIC, PhysicalRole.EFFORT),   # Fluid pressure (Pa, J/m3, N/m2)
    "OPB_00299": (Domain.HYDRAULIC, PhysicalRole.FLOW),     # Fluid flow rate (m3/s)
    "OPB_00073": (Domain.HYDRAULIC, PhysicalRole.MOMENTUM), # A momentum property that is proportional to the temporal differential of an fluid flow rate, L/s2
    "OPB_00154": (Domain.HYDRAULIC, PhysicalRole.QUANTITY), # Spatial amount, Fluid volume, L

    # General Domain
    "OPB_00402": (Domain.UNKNOWN, PhysicalRole.QUANTITY),      # Time
    "OPB_00293": (Domain.UNKNOWN, PhysicalRole.EFFORT),        # Temperature (K)
    "OPB_00562": (Domain.UNKNOWN, PhysicalRole.ENERGY),        # Energy (J)
    "OPB_00563": (Domain.UNKNOWN, PhysicalRole.POWER),         # Power (mW)
    "OPB_00100": (Domain.UNKNOWN, PhysicalRole.QUANTITY),      # Thermodynamic entropy amount, J/K
    "OPB_00564": (Domain.UNKNOWN, PhysicalRole.FLOW),          # Thermodynamic entropy flow, J/K/s
    "OPB_00410": (Domain.UNKNOWN, PhysicalRole.QUANTITY),      # Ideal gas constant
    "OPB_00089": (Domain.UNKNOWN, PhysicalRole.QUANTITY),      # Faraday constant
}

@dataclass
class UnitSignature:
    unit_name: str
    domain: Domain
    role: PhysicalRole
    cellml_units: Units
    opb_id: str

@dataclass
class VariableSignature:
    variable_name: str
    component_name: str
    variable_type: str
    units: str
    domain: str
    role: str
    opb_id: str
    equivalentVariables: list

class SemanticUnitClassifier:
    def __init__(self, ttl_path: str, baseline_cellml_path: str):
        self.signatures: list[UnitSignature] = []
        
        # Step 1: Parse RDF Graph
        unit_to_opb = self._parse_ttl_annotations(ttl_path)
        
        # Step 2: Load Baseline CellML Units & Map to OPB
        self._build_unit_signatures(baseline_cellml_path, unit_to_opb)

    def _parse_ttl_annotations(self, ttl_path: str) -> dict[str, str]:
        """Extracts unit_name -> OPB_ID from the RDF TTL file."""
        g = rdflib.Graph()
        g.parse(ttl_path, format="turtle")
        
        sio_is_unit_of = rdflib.URIRef("http://semanticscience.org/resource/SIO_000222")
        unit_to_opb = {}

        for subject, predicate, obj in g.triples((None, sio_is_unit_of, None)):
            # Extract unit name from URI fragment (e.g. ./baseline_units.cellml#J_per_mol -> J_per_mol)
            unit_name = str(subject).split("#")[-1]
            # Extract OPB identifier (e.g. http://identifiers.org/opb/OPB_00378 -> OPB_00378)
            opb_id = str(obj).split("/")[-1]
            unit_to_opb[unit_name] = opb_id

        return unit_to_opb

    def _build_unit_signatures(self, baseline_cellml_path: str, unit_to_opb: dict[str, str]):
        """Parses baseline_units.cellml and constructs unit signatures."""
        baseline_model, issues = parse_model(baseline_cellml_path)
        if baseline_model is None:
            raise ValueError(f"Failed to parse baseline CellML model: {issues}")
        for i in range(baseline_model.unitsCount()):
            u = baseline_model.units(i)
            u_name = u.name()
            if u_name in unit_to_opb:
                opb_id = unit_to_opb[u_name]                
                if opb_id in OPB_ROLE_MAP:
                    domain, role = OPB_ROLE_MAP[opb_id]
                    self.signatures.append(
                        UnitSignature(
                            unit_name=u_name,
                            domain=domain,
                            role=role,
                            cellml_units=u,
                            opb_id=opb_id
                        )
                    )

    def classify_variable(self, target_var: Variable) -> tuple[Domain, PhysicalRole, str]:
        """
        Takes a variable from any target CellML model and queries libcellml's API
        to find compatible units in baseline_units.cellml.
        """
        var_units = target_var.units()
        if var_units is None:
            return Domain.UNKNOWN, PhysicalRole.UNCLASSIFIED, ""

        # Use native libcellml unit compatibility API
        for sig in self.signatures:
            if Units.compatible(var_units, sig.cellml_units):
                return sig.domain, sig.role, sig.opb_id

        return Domain.UNKNOWN, PhysicalRole.UNCLASSIFIED, ""

class SemanticVariableClassifier:
    def __init__(self, semantic_classifier: SemanticUnitClassifier, analyserModel: AnalyserModel):
        self.semantic_classifier = semantic_classifier
        self.analyserModel = analyserModel

    def classify_variables(self) -> list[VariableSignature]:
        """
        Classifies all variables in the target CellML model based on their units and OPB annotations.
        """
        if not self.analyserModel.isValid():
            raise ValueError(f"The model is {self.analyserModel.typeAsString(self.analyserModel.type())}.")
        variable_signatures: list[VariableSignature] = []
        for analyserVar in self.analyserModel.states() + self.analyserModel.constants() + self.analyserModel.computedConstants()+self.analyserModel.algebraicVariables():
            variable=analyserVar.variable()           
            domain, role, opb_id = self.semantic_classifier.classify_variable(variable)
            variable_signatures.append(
                VariableSignature(
                    variable_name=variable.name(),
                    component_name=variable.parent().name() if variable.parent() else "",
                    variable_type=analyserVar.typeAsString(analyserVar.type()),
                    domain=domain.name,
                    role=role.name,
                    opb_id=opb_id,
                    units=variable.units().name() if variable.units() else "",
                    equivalentVariables=view_equivalent_variables(variable)
                )
            )
        return variable_signatures

    def save_variable_signatures_to_json(self, variable_signatures: list[VariableSignature], output_path: str):
        """
        Saves the variable signatures to a JSON file.
        """
        output_file = validate_file_path(output_path)
        if output_file is None:
            raise ValueError(f"Invalid output file path: {output_path}")
        else:      
        # Convert dataclass instances to dictionaries for JSON serialization
           signatures_dict = [sig.__dict__ for sig in variable_signatures]
           with open(output_file, 'w', encoding='utf-8') as f:
              json.dump(signatures_dict, f, ensure_ascii=False, indent=4)

    

   
