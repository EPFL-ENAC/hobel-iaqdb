import pandas as pd
import numpy as np
import country_converter as coco
from typing import List, Dict
from pydantic import ValidationError
from api.models.catalog import Study, Building, Space, Certification, Person, Instrument, InstrumentParameter, ParseError


class StudyParser:
    """Parse a study from an Excel file.
    """

    def __init__(self):
        self.errors: List[ParseError] = []

    def parse(self, io) -> Study:
        self.errors = []

        try:
            df = pd.read_excel(io, sheet_name="Study")
        except Exception as e:
            raise ValueError(f"Missing or unreadable 'Study' sheet: {e}")

        df = self.clean_header(df)
        df.rename(
            columns={
                'name': 'name',
                'description': 'description',
                'website': 'website',
                'start year': 'start_year',
                'end year': 'end_year',
                'duration': 'duration',
                'occupant impact': 'occupant_impact',
                'other indoor parameter': 'other_indoor_param',
                'citation': 'citation',
                'doi': 'doi',
                'funding information': 'funding',
                'ethics approval(s)': 'ethics',
                'license': 'license'
            },
            inplace=True)

        # Convert columns to numeric, invalid parsing will be set as NaN (None in case of conversion to object type)
        for col in ['start_year', 'end_year', 'duration']:
            if col in df.columns:
                df[col] = pd.to_numeric(
                    df[col], downcast='integer', errors='coerce')
        # Lower case of categorical columns
        for col in ['occupant_impact', 'other_indoor_param']:
            if col in df.columns:
                df[col] = self.mormalize_column(df, col)
        # Convert 'yes' to default license, and handle unexpected strings by converting them to empty string
        if 'license' in df.columns:
            df['license'] = df['license'].str.lower().map(
                {'yes': 'CC BY-NC', 'true': 'CC BY-NC', '1': 'CC BY-NC'}).fillna('')
        # To explicitly convert NaN to None
        df = df.replace({np.nan: None})

        std_dict = df.iloc[0].to_dict()
        try:
            study = Study(**std_dict)
        except ValidationError as e:
            for err in e.errors():
                self.errors.append(ParseError(
                    loc="study." + ".".join(str(l) for l in err["loc"]),
                    msg=err["msg"],
                    severity="error"
                ))
            study = Study(identifier=std_dict.get("identifier") or "_draft")

        # Domain checks
        if study.start_year and study.end_year and study.start_year > study.end_year:
            self.errors.append(ParseError(
                loc="study.start_year",
                msg=f"start_year ({study.start_year}) is after end_year ({study.end_year})",
                severity="error"
            ))

        try:
            contributors = self.read_contributors(io)
        except Exception as e:
            self.errors.append(ParseError(
                loc="contributors", msg=f"Could not read Contributor sheet: {e}", severity="warning"))
            contributors = []
        study.contributors = contributors

        try:
            instruments = self.read_instruments(io)
        except Exception as e:
            self.errors.append(ParseError(
                loc="instruments", msg=f"Could not read Instrument sheet: {e}", severity="warning"))
            instruments = []
        study.instruments = instruments

        try:
            spaces = self.read_spaces(io)
        except Exception as e:
            self.errors.append(ParseError(
                loc="spaces", msg=f"Could not read Space sheet: {e}", severity="warning"))
            spaces = {}

        try:
            buildings = self.read_buildings(io, spaces)
        except Exception as e:
            self.errors.append(ParseError(
                loc="buildings", msg=f"Could not read Building sheet: {e}", severity="warning"))
            buildings = []
        study.buildings = buildings

        # Check for orphan spaces (reference a building not in the Building sheet)
        used_building_ids = {str(b.identifier) for b in buildings}
        for bldg_id in spaces:
            if bldg_id not in used_building_ids:
                self.errors.append(ParseError(
                    loc="space.building_identifier",
                    msg=f"Spaces reference unknown building identifier '{bldg_id}' — they will be ignored",
                    severity="warning"
                ))

        if study.identifier is None:
            study.identifier = '_draft'
        study.id = 0

        return study

    def read_contributors(self, io) -> List[Person]:
        df = pd.read_excel(io, sheet_name="Contributor")
        df = self.clean_header(df)
        df.rename(
            columns={
                'full name': 'name',
                'email': 'email',
                'email public': 'email_public',
                'institution': 'institution',
            },
            inplace=True)

        # Convert 'yes' to True, 'no' to False, and handle unexpected strings by converting them to None
        if 'email_public' in df.columns:
            df['email_public'] = df['email_public'].str.lower().map(
                {'yes': True, 'true': True, '1': True}).fillna(False)
        # To explicitly convert NaN to None
        df = df.replace({np.nan: None})

        persons = []
        for index, row in df.iterrows():
            prsn = row.to_dict()
            try:
                person = Person(**prsn)
            except ValidationError as e:
                for err in e.errors():
                    self.errors.append(ParseError(
                        loc=f"contributor[{index}]." +
                            ".".join(str(l) for l in err["loc"]),
                        msg=err["msg"],
                        severity="error"
                    ))
                continue
            person.id = index
            person.study_id = 0
            persons.append(person)
        return persons

    def read_instruments(self, io) -> List[Instrument]:
        df = pd.read_excel(io, sheet_name="Instrument")
        df = self.clean_header(df)
        df.rename(
            columns={
                'instrument identifier': 'identifier',
                'manufacturer': 'manufacturer',
                'model': 'model',
                'equipment rating': 'equipment_grade_rating',
                'placement': 'placement',
                'parameter': 'physical_parameter',
                'analysis method': 'analysis_method',
                'measurement uncertainty': 'measurement_uncertainty',
            },
            inplace=True)

        # Lower case of categorical columns
        for col in ['equipment_grade_rating', 'placement']:
            if col in df.columns:
                df[col] = self.mormalize_column(df, col)
        # To explicitly convert NaN to None
        df = df.replace({np.nan: None})

        instruments = []
        id = 1
        for index, row in df.iterrows():
            inst = row.to_dict()
            try:
                instrument = Instrument(**inst)
            except ValidationError as e:
                for err in e.errors():
                    self.errors.append(ParseError(
                        loc=f"instrument[{index}]." +
                            ".".join(str(l) for l in err["loc"]),
                        msg=err["msg"],
                        severity="error"
                    ))
                continue
            instrument.study_id = 0
            # ensure it is a string
            instrument.identifier = str(instrument.identifier)

            # find instrument by identifier in the instruments list
            found = [inst for inst in instruments if inst.identifier ==
                     instrument.identifier]
            if len(found) > 0:
                instrument = found[0]
            else:
                instrument.id = id
                id += 1
                instruments.append(instrument)

            physical_parameter = inst.get("physical_parameter")
            if physical_parameter is None:
                self.errors.append(ParseError(
                    loc=f"instrument[{index}].physical_parameter",
                    msg="physical_parameter is missing — parameter row skipped",
                    severity="warning"
                ))
                continue
            param = {
                "id": len(instrument.parameters) + 1,
                "physical_parameter": physical_parameter,
                "analysis_method": inst.get("analysis_method"),
                "measurement_uncertainty": inst.get("measurement_uncertainty"),
                "note": None,
                "study_id": 0,
                "instrument_id": instrument.id,
            }
            try:
                instrument.parameters.append(InstrumentParameter(**param))
            except ValidationError as e:
                for err in e.errors():
                    self.errors.append(ParseError(
                        loc=f"instrument[{index}].parameter." +
                            ".".join(str(l) for l in err["loc"]),
                        msg=err["msg"],
                        severity="error"
                    ))

        return instruments

    def read_buildings(self, io, spaces: List[Space]) -> List[Building]:
        df = pd.read_excel(io, sheet_name="Building")
        df = self.clean_header(df)
        df.rename(
            columns={
                'building identifier': 'identifier',
                'country': 'country',
                'city/geographical area': 'city',
                'postcode': 'postcode',
                'building type': 'type',
                'if other, specify building type': 'other_type',
                'outdoor environment': 'outdoor_env',
                'if other, specify outdoor environment': 'other_outdoor_env',
                'green certified': 'green_certified',
                'green certification program name': 'green_certification_name',
                'green certification level': 'green_certification_level',
                'year of construction': 'construction_year',
                'renovation': 'renovation',
                'year of renovation': 'renovation_year',
                'mechanical ventilation': 'mechanical_ventilation',
                'particle filter rating system': 'particle_filtration_system',
                'particle filter rating level': 'particle_filtration_rating',
                'operable windows': 'operable_windows',
                'airtightness (ach50)': 'airtightness',
                'occupant age group': 'age_group',
                'occupant socioeconomic status': 'socioeconomic_status',
                'smoking permitted': 'smoking',
            },
            inplace=True)

        # Convert columns to numeric, invalid parsing will be set as NaN (None in case of conversion to object type)
        for col in ['construction_year', 'particle_filtration_rating', 'renovation_year']:
            if col in df.columns:
                df[col] = pd.to_numeric(
                    df[col], downcast='integer', errors='coerce')
        for col in ['airtightness']:
            if col in df.columns:
                original = df[col].copy()
                df[col] = pd.to_numeric(df[col], errors='coerce')
                for idx, orig, new in zip(df.index, original, df[col]):
                    if orig is not None and not pd.isna(orig) and pd.isna(new):
                        self.errors.append(ParseError(
                            loc=f"building[{idx}].{col}",
                            msg=f"'{orig}' is not a valid number, set to None",
                            severity="warning"
                        ))
        # Convert columns to string, invalid parsing will be set as NaN (None in case of conversion to object type)
        for col in ['postcode']:
            if col in df.columns:
                df[col] = df[col].astype(str).replace('nan', None)
        # Lower case of categorical columns
        for col in ['type', 'outdoor_env', 'green_certified', 'renovation', 'mechanical_ventilation', 'operable_windows', 'age_group', 'socioeconomic_status', 'smoking']:
            if col in df.columns:
                df[col] = self.mormalize_column(df, col)
        # To explicitly convert NaN to None
        df = df.replace({np.nan: None})
        if 'country' in df.columns:
            def convert_country(x, row_index):
                if x is None:
                    return None
                result = coco.convert(names=x, to='ISO2', not_found=None)
                if result is None:
                    self.errors.append(ParseError(
                        loc=f"building[{row_index}].country",
                        msg=f"Unrecognised country '{x}', set to None",
                        severity="warning"
                    ))
                return result
            df['country'] = [convert_country(v, i)
                             for i, v in zip(df.index, df['country'])]

        buildings = []
        for index, row in df.iterrows():
            bldg = row.to_dict()
            try:
                building = Building(**bldg)
            except ValidationError as e:
                for err in e.errors():
                    self.errors.append(ParseError(
                        loc=f"building[{index}]." +
                            ".".join(str(l) for l in err["loc"]),
                        msg=err["msg"],
                        severity="error"
                    ))
                continue
            if building.identifier is None:
                pass
            if bldg['green_certified'] is not None and bldg['green_certified'].lower() == 'yes' and bldg['green_certification_name'] is not None:
                crtf = Certification(
                    program=bldg['green_certification_name'], level=bldg['green_certification_level'])
                building.certifications = [crtf]
            # ensure it is a string
            building.identifier = str(building.identifier)
            building.id = index
            building.study_id = 0
            # look up spaces
            if building.identifier in spaces:
                building.spaces = spaces[building.identifier]
                for space in building.spaces:
                    space.building_id = index
                    space.study_id = 0
            buildings.append(building)
        return buildings

    def read_spaces(self, io) -> Dict[str, List[Space]]:
        df = pd.read_excel(io, sheet_name="Space")
        df = self.clean_header(df)
        df.rename(
            columns={
                'building identifier': 'building_identifier',
                'space identifier': 'identifier',
                'space type': 'type',
                'floor area': 'floor_area',
                'space volume': 'space_volume',
                'occupancy density': 'occupancy_density',
                'occupancy status': 'occupancy',
                'mechanical ventilation system type': 'mechanical_ventilation_type',
                'if other, specify mechanical ventilation type': 'other_mechanical_ventilation_type',
                'cooling system type': 'cooling_type',
                'if other, specify cooling system type': 'other_cooling_type',
                'heating system type': 'heating_type',
                'if other, specify heating system type': 'other_heating_type',
                'presence of standalone air filtration/purification': 'air_filtration',
                'presence of printers or photocopiers': 'printers',
                'presence of carpets': 'carpets',
                'presence of any combustion sources': 'combustion_sources',
                'major combustion sources': 'major_combustion_sources',
                'minor combustion sources': 'minor_combustion_sources',
                'presence of pets': 'pets',
                'presence of visible dampness': 'dampness',
                'presence of visible mold': 'mold',
                'cleaning with detergents': 'detergents',
            },
            inplace=True)

        # Convert columns to numeric, invalid parsing will be set as NaN (None in case of conversion to object type)
        for col in ['space_volume', 'floor_area', 'occupancy_density']:
            if col in df.columns:
                df[col] = pd.to_numeric(
                    df[col], downcast='float', errors='coerce')
        # Lower case of categorical columns
        for col in ['type', 'occupancy', 'mechanical_ventilation_type',
                    'cooling_type', 'heating_type', 'air_filtration',
                    'printers', 'carpets', 'combustion_sources', 'major_combustion_sources', 'minor_combustion_sources',
                    'pets', 'dampness', 'mold', 'detergents']:
            df[col] = self.mormalize_column(df, col)
        # To explicitly convert NaN to None
        df = df.replace({np.nan: None})

        spaces = {}
        for index, row in df.iterrows():
            spc = row.to_dict()
            try:
                space = Space(**spc)
            except ValidationError as e:
                for err in e.errors():
                    self.errors.append(ParseError(
                        loc=f"space[{index}]." +
                            ".".join(str(l) for l in err["loc"]),
                        msg=err["msg"],
                        severity="error"
                    ))
                continue
            if space.identifier is None:
                pass
            # ensure it is a string
            space.identifier = str(space.identifier)
            space.id = index
            space.study_id = 0
            if spc['building_identifier'] is not None:
                # ensure building identifier is a string
                bldg_id = f"{spc['building_identifier']}"
                if bldg_id not in spaces:
                    spaces[bldg_id] = []
                spaces[bldg_id].append(space)
        return spaces

    def clean_header(self, df: pd.DataFrame) -> pd.DataFrame:
        # Remove 2 first rows
        df = df.iloc[2:]
        # Remove non-printable/invisible characters from column names
        df.columns = df.columns.str.replace(
            r'[^\x20-\x7E]', ' ', regex=True)
        df.columns = df.columns.str.strip().str.lower()
        return df

    def mormalize_column(self, df: pd.DataFrame, column: str) -> pd.DataFrame:
        # Lower case and replace non-printable/invisible characters with space and do stripping
        # column is in df.columns
        if column in df.columns:
            return df[column].str.lower().str.replace(
                '-family', 'family').str.replace(  # legacy
                r'[^\x20-\x7E]', ' ', regex=True).str.strip()
        return None
