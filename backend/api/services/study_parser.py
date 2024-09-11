import pandas as pd
import numpy as np
from typing import List, Dict
from api.models.catalog import Study, Building, Space, Certification, Person


class StudyParser:
    """Parse a study from an Excel file.
    """

    def parse(self, io) -> Study:
        df = pd.read_excel(io, sheet_name="Study")
        df = self.clean_header(df)
        df.rename(
            columns={
                'Name': 'name',
                'Description': 'description',
                'Website': 'website',
                'Start year': 'start_year',
                'End year': 'end_year',
                'Duration': 'duration',
                'Occupant impact': 'occupant_impact',
                'Other indoor parameter': 'other_indoor_param',
                'Citation': 'citation',
                'DOI': 'doi',
                'Funding information': 'funding',
                'Ethics approval(s)': 'ethics',
                'License': 'license'
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
                df[col] = df[col].str.lower().str.replace(' ', '_')
        # To explicitly convert NaN to None
        df = df.replace({np.nan: None})
        # print(df)

        std_dict = df.iloc[0].to_dict()
        study = Study(**std_dict)

        contributors = self.read_contributors(io)
        study.contributors = contributors

        spaces = self.read_spaces(io)

        buildings = self.read_buildings(io, spaces)
        study.buildings = buildings
        study.building_count = len(buildings)

        if study.identifier is None:
            study.identifier = '_draft'

        return study

    def read_contributors(self, io) -> List[Person]:
        df = pd.read_excel(io, sheet_name="Contributor")
        df = self.clean_header(df)
        df.rename(
            columns={
                'Full name': 'name',
                'Email': 'email',
                'Email public': 'email_public',
                'Institution': 'institution',
            },
            inplace=True)

        # To explicitly convert NaN to None
        # Convert 'yes' to True, 'no' to False, and handle unexpected strings by converting them to None
        if 'email_public' in df.columns:
            df['email_public'] = df['email_public'].str.lower().map(
                {'yes': True, 'true': True, '1': True}).fillna(False)
        df = df.replace({np.nan: None})

        persons = []
        for index, row in df.iterrows():
            prsn = row.to_dict()
            person = Person(**prsn)
            persons.append(person)
        return persons

    def read_buildings(self, io, spaces: List[Space]) -> List[Building]:
        df = pd.read_excel(io, sheet_name="Building")
        df = self.clean_header(df)
        df.rename(
            columns={
                'Building identifier': 'identifier',
                'Country': 'country',
                'City': 'city',
                'Postcode': 'postcode',
                'Building type': 'type',
                'If other, specify building type': 'other_type',
                'Outdoor environment': 'outdoor_env',
                'If other, specify outdoor environment': 'other_outdoor_env',
                'Green certified': 'green_certified',
                'Green certification program name': 'green_certification_name',
                'Green certification level': 'green_certification_level',
                'Year of construction': 'construction_year',
                'Renovation': 'renovation',
                'Year of renovation': 'renovation_year',
                'Mechanical ventilation': 'mechanical_ventilation',
                'Operable windows': 'operable_windows',
                'Special population designation': 'special_population',
                'If other, specify special population': 'other_special_population',
                'Smoking permitted': 'smoking',
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
                df[col] = df[col].str.lower().str.replace(' ', '_')
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
            # look up spaces
            building.spaces = spaces[building.identifier]
            # building.id = index
            buildings.append(building)
        return buildings

    def read_spaces(self, io) -> Dict[str, List[Space]]:
        df = pd.read_excel(io, sheet_name="Space")
        df = self.clean_header(df)
        df.rename(
            columns={
                'Building identifier': 'building_identifier',
                'Space identifier': 'identifier',
                'Space types': 'type',
                'Occupancy status': 'occupancy',
                'Mechanical ventilation system type': 'mechanical_ventilation_type',
                'Mechanical ventilation system status': 'mechanical_ventilation_status',
                'Windows status': 'windows_status',
                'Ventilation rate': 'ventilation_rate',
                'Air change rate': 'air_change_rate',
                'Particle filtration rating': 'particle_filtration_rating',
                'Cooling system type': 'cooling_type',
                'If other, specify cooling system type': 'other_cooling_type',
                'Cooling system status': 'cooling_status',
                'Heating system type': 'heating_type',
                'If other, specify heating system type': 'other_heating_type',
                'Heating system status': 'heating_status',
                'Presence of standalone air filtration/purification': 'air_filtration',
                'Presence of printers or photocopiers': 'printers',
                'Presence of carpets': 'carpets',
                'Presence of any combustion sources': 'combustion_sources',
                'Marjor combustion sources': 'major_combustion_sources',
                'Minor combustion sources': 'minor_combustion_sources',
                'Presence of pets': 'pets',
                'Presence of visible dampness': 'dampness',
                'Presence of visible mold': 'mold',
                'Cleaning with detergents': 'detergents',
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
            df[col] = df[col].str.lower().str.replace(' ', '_')
        # To explicitly convert NaN to None
        df = df.replace({np.nan: None})
        # print(df)

        spaces = {}
        for index, row in df.iterrows():
            spc = row.to_dict()
            space = Space(**spc)
            # ensure it is a string
            space.identifier = f"{space.identifier}"
            if spc['building_identifier'] is not None:
                # ensure building identifier is a string
                bldg_id = f"{spc['building_identifier']}"
                if bldg_id not in spaces:
                    spaces[bldg_id] = []
                spaces[bldg_id].append(space)
        return spaces

    def clean_header(self, df):
        # Remove 2 first rows
        df = df.iloc[2:]
        # Remove non-printable/invisible characters from column names
        df.columns = df.columns.str.replace(
            r'[^\x20-\x7E]', ' ', regex=True)
        df.columns = df.columns.str.strip()
        return df
