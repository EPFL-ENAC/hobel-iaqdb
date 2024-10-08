import pandas as pd
import numpy as np
from typing import List, Dict
from api.models.catalog import Study, Building, Space, Certification, Person, Instrument, InstrumentParameter


class StudyParser:
    """Parse a study from an Excel file.
    """

    def parse(self, io) -> Study:
        df = pd.read_excel(io, sheet_name="Study")
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
        # To explicitly convert NaN to None
        df = df.replace({np.nan: None})
        # print(df)

        std_dict = df.iloc[0].to_dict()
        study = Study(**std_dict)

        contributors = self.read_contributors(io)
        study.contributors = contributors

        instruments = self.read_instruments(io)
        study.instruments = instruments

        spaces = self.read_spaces(io)
        study.space_count = sum(len(sp) for sp in spaces.values())

        buildings = self.read_buildings(io, spaces)
        study.buildings = buildings
        study.building_count = len(buildings)

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
            person = Person(**prsn)
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
            },
            inplace=True)

        # Lower case of categorical columns
        for col in ['equipment_grade_rating', 'placement']:
            if col in df.columns:
                df[col] = self.mormalize_column(df, col)
        for i in range(1, 50):
            ppCol = f"physical parameter {i}"
            if ppCol in df.columns:
                df[ppCol] = self.mormalize_column(df, ppCol)
        # To explicitly convert NaN to None
        df = df.replace({np.nan: None})

        instruments = []
        for index, row in df.iterrows():
            inst = row.to_dict()
            instrument = Instrument(**inst)
            instrument.id = index
            instrument.study_id = 0
            # ensure it is a string
            instrument.identifier = f"{instrument.identifier}"
            for i in range(1, 50):
                ppCol = f"physical parameter {i}"
                if ppCol in inst and inst[ppCol] is not None:
                    amCol = f"analysis method {i}"
                    muCol = f"measurement uncertainty {i}"
                    param = {
                        "id": i,
                        "physical_parameter": inst[ppCol],
                        "analysis_method": inst[amCol] if amCol in inst else None,
                        "measurement_uncertainty": inst[muCol] if muCol in inst else None,
                        "study_id": 0,
                        "instrument_id": index,
                    }
                    instrument.parameters.append(InstrumentParameter(**param))

            instruments.append(instrument)
        return instruments

    def read_buildings(self, io, spaces: List[Space]) -> List[Building]:
        df = pd.read_excel(io, sheet_name="Building")
        df = self.clean_header(df)
        df.rename(
            columns={
                'building identifier': 'identifier',
                'country': 'country',
                'city': 'city',
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
                'operable windows': 'operable_windows',
                'special population designation': 'special_population',
                'if other, specify special population': 'other_special_population',
                'smoking permitted': 'smoking',
            },
            inplace=True)

        # Convert columns to numeric, invalid parsing will be set as NaN (None in case of conversion to object type)
        for col in ['construction_year', 'renovation_year']:
            if col in df.columns:
                df[col] = pd.to_numeric(
                    df[col], downcast='integer', errors='coerce')
        # Lower case of categorical columns
        for col in ['type', 'outdoor_env', 'green_certified', 'renovation', 'mechanical_ventilation', 'operable_windows', 'special_population', 'smoking']:
            if col in df.columns:
                df[col] = self.mormalize_column(df, col)
        # To explicitly convert NaN to None
        df = df.replace({np.nan: None})
        # print(df)

        buildings = []
        for index, row in df.iterrows():
            bldg = row.to_dict()
            building = Building(**bldg)
            if bldg['green_certified'] is not None and bldg['green_certified'].lower() == 'yes' and bldg['green_certification_name'] is not None:
                crtf = Certification(
                    program=bldg['green_certification_name'], level=bldg['green_certification_level'])
                building.certifications = [crtf]
            # ensure it is a string
            building.identifier = f"{building.identifier}"
            building.id = index
            building.study_id = 0
            # look up spaces
            building.spaces = spaces[building.identifier]
            for space in building.spaces:
                space.building_id = index
                space.study_id = 0
            # building.id = index
            buildings.append(building)
        return buildings

    def read_spaces(self, io) -> Dict[str, List[Space]]:
        df = pd.read_excel(io, sheet_name="Space")
        df = self.clean_header(df)
        df.rename(
            columns={
                'building identifier': 'building_identifier',
                'space identifier': 'identifier',
                'space types': 'type',
                'occupancy status': 'occupancy',
                'mechanical ventilation system type': 'mechanical_ventilation_type',
                'mechanical ventilation system status': 'mechanical_ventilation_status',
                'windows status': 'windows_status',
                'ventilation rate': 'ventilation_rate',
                'air change rate': 'air_change_rate',
                'particle filtration rating': 'particle_filtration_rating',
                'cooling system type': 'cooling_type',
                'if other, specify cooling system type': 'other_cooling_type',
                'cooling system status': 'cooling_status',
                'heating system type': 'heating_type',
                'if other, specify heating system type': 'other_heating_type',
                'heating system status': 'heating_status',
                'presence of standalone air filtration/purification': 'air_filtration',
                'presence of printers or photocopiers': 'printers',
                'presence of carpets': 'carpets',
                'presence of any combustion sources': 'combustion_sources',
                'marjor combustion sources': 'major_combustion_sources',
                'minor combustion sources': 'minor_combustion_sources',
                'presence of pets': 'pets',
                'presence of visible dampness': 'dampness',
                'presence of visible mold': 'mold',
                'cleaning with detergents': 'detergents',
            },
            inplace=True)

        # Convert columns to numeric, invalid parsing will be set as NaN (None in case of conversion to object type)
        if 'particle_filtration_rating' in df.columns:
            df['particle_filtration_rating'] = pd.to_numeric(
                df['particle_filtration_rating'], downcast='integer', errors='coerce')
        for col in ['ventilation_rate', 'air_change_rate']:
            if col in df.columns:
                df[col] = pd.to_numeric(
                    df[col], downcast='float', errors='coerce')
        # Lower case of categorical columns
        for col in ['type', 'occupancy', 'mechanical_ventilation_type', 'mechanical_ventilation_status', 'windows_status',
                    'cooling_type', 'cooling_status', 'heating_type', 'heating_status', 'air_filtration',
                    'printers', 'carpets', 'combustion_sources', 'major_combustion_sources', 'minor_combustion_sources',
                    'pets', 'dampness', 'mold', 'detergents']:
            df[col] = self.mormalize_column(df, col)
        # To explicitly convert NaN to None
        df = df.replace({np.nan: None})
        # print(df)

        spaces = {}
        for index, row in df.iterrows():
            spc = row.to_dict()
            space = Space(**spc)
            # ensure it is a string
            space.identifier = f"{space.identifier}"
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
        return df[column].str.lower().str.replace(
            r'[^\x20-\x7E]', ' ', regex=True).str.strip()
