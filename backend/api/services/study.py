import os
import json
import tempfile
from api.db import AsyncSession
from sqlalchemy.sql import text
from sqlalchemy.orm import selectinload
from sqlalchemy import func
from sqlmodel import select
from fastapi import HTTPException
from api.services.s3 import s3_client
from api.models.catalog import Study, StudiesResult, Building, Space, StudyDraft, Instrument, InstrumentParameter, Dataset, Variable, Person, Certification, GroupByResult, GroupByCount
from enacit4r_sql.utils.query import QueryBuilder


class StudyQueryBuilder(QueryBuilder):

    def build_count_query_with_joins(self, filter):
        query = self.build_count_query()
        query = self._apply_joins(query, filter)
        return query

    def build_group_query_with_joins(self, filter, group_by_column):
        query = self._apply_filter(
            select(group_by_column, func.count(func.distinct(self.model.id))))
        query = self._apply_joins(query, filter)
        return query.group_by(group_by_column)

    def build_query_with_joins(self, total_count, filter):
        start, end, query = self.build_query(total_count)
        query = self._apply_joins(query, filter)
        query = query.options(selectinload(Study.contributors),
                              selectinload(Study.buildings),
                              selectinload(Study.instruments),
                              selectinload(Study.datasets))
        return start, end, query

    def _apply_joins(self, query, filter):
        if "$building" in filter:
            query = query.join(Building, Study.id == Building.study_id)
        if "$space" in filter:
            query = query.join(Space, Study.id == Space.study_id)
        query = query.distinct()
        return query


class StudyService:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def count(self) -> int:
        """Count all studies"""
        count = (await self.session.exec(text("select count(id) from study"))).scalar()
        return count

    async def get(self, study_id: int) -> Study:
        """Get a study by id"""
        res = await self.session.exec(
            select(Study).where(
                Study.id == study_id).options(selectinload(Study.contributors), selectinload(Study.buildings), selectinload(Study.instruments), selectinload(Study.datasets))
        )
        study = res.one_or_none()
        if not study:
            raise HTTPException(
                status_code=404, detail="Study not found")

        return study

    async def get_by_identifier(self, study_identifier: str) -> Study:
        """Get a study by id"""
        res = await self.session.exec(
            select(Study).where(
                Study.identifier == study_identifier).options(selectinload(Study.contributors), selectinload(Study.buildings), selectinload(Study.instruments), selectinload(Study.datasets))
        )
        study = res.one_or_none()
        if not study:
            raise HTTPException(
                status_code=404, detail="Study not found")

        return study

    async def delete(self, study_id: int) -> Study:
        """Delete a study by id"""
        res = await self.session.exec(
            select(Study).where(Study.id == study_id)
        )
        study = res.one_or_none()
        return await self.delete_study(study)

    async def delete_by_identifier(self, study_identifier: str) -> Study:
        """Delete a study by identifier"""
        res = await self.session.exec(
            select(Study).where(Study.identifier == study_identifier)
        )
        study = res.one_or_none()
        return await self.delete_study(study)

    async def delete_study(self, study: Study) -> Study:
        """Delete a study and all its related data"""
        if not study:
            raise HTTPException(
                status_code=404, detail="Study not found")

        # Delete the study
        await self.session.delete(study)
        await self.session.commit()

        # Delete the public folder in S3
        pub_folder = f"pub/{study.identifier}"
        await s3_client.delete_files(pub_folder)

        return study

    async def find(self, filter: dict, sort: list, range: list) -> StudiesResult:
        """Get all studies matching filter and range"""
        builder = StudyQueryBuilder(Study, filter, sort, range, {
            "$building": Building, "$space": Space})

        # Do a query to satisfy total count
        count_query = builder.build_count_query_with_joins(filter)
        total_count_query = await self.session.exec(count_query)
        total_count = total_count_query.one()

        # Main query
        start, end, query = builder.build_query_with_joins(total_count, filter)
        if total_count == 0:
            return StudiesResult(
                total=total_count,
                skip=start,
                limit=end - start + 1,
                data=[]
            )

        # Execute query
        results = await self.session.exec(query)
        studies = results.all()

        return StudiesResult(
            total=total_count,
            skip=start,
            limit=end - start + 1,
            data=studies
        )

    async def save(self, study_draft: StudyDraft) -> Study:
        """Save the study draft in the database, replacing the existing study if one with same identifier exists."""

        draft_folder = f"draft/{study_draft.identifier}"
        pub_folder = f"pub/{study_draft.identifier}"

        contributor_drafts = study_draft.contributors
        study_draft.contributors = []
        building_drafts = study_draft.buildings
        study_draft.buildings = []
        instrument_drafts = study_draft.instruments
        study_draft.instruments = []
        datasets_drafts = study_draft.datasets
        study_draft.datasets = []

        res = await self.session.exec(
            select(Study).where(Study.identifier == study_draft.identifier)
        )
        existing_study = res.one_or_none()
        if existing_study:
            # delete existing study
            await self.session.delete(existing_study)
            await self.session.commit()
            await s3_client.delete_files(pub_folder)

        study = Study(**study_draft.model_dump())
        study.id = None
        self.session.add(study)
        await self.session.commit()
        await self.session.refresh(study)
        study_dict = study.model_dump()

        # Copy all study draft files to pub folder
        study_files = [file for file in await s3_client.list_files(draft_folder) if file.endswith("/study.json") == False]
        if study_files:
            # Copy the study files to the pub folder
            for file in study_files:
                new_file = file.replace("/draft/", "/pub/")
                await s3_client.copy_file(file, new_file)

        # Contributors
        study_dict['contributors'] = []
        for contributor_draft in contributor_drafts:
            person = Person(**contributor_draft.model_dump())
            person.id = None
            person.study_id = study.id
            self.session.add(person)
            await self.session.commit()
            await self.session.refresh(person)
            study_dict['contributors'].append(person.model_dump())

        # Buildings
        study_dict['buildings'] = []
        for building_draft in building_drafts:
            space_drafts = building_draft.spaces
            building_draft.spaces = []
            certification_drafts = building_draft.certifications
            building_draft.certifications = []
            building = Building(**building_draft.model_dump())
            building.study_id = study.id
            building.id = None

            self.session.add(building)
            await self.session.commit()
            await self.session.refresh(building)
            building_dict = building.model_dump()

            # Spaces
            building_dict['spaces'] = []
            for space_draft in space_drafts:
                space = Space(**space_draft.model_dump())
                space.id = None
                space.study_id = study.id
                space.building_id = building.id
                self.session.add(space)
                await self.session.commit()
                await self.session.refresh(space)
                building_dict['spaces'].append(space.model_dump())

            # Certifications
            building_dict['certifications'] = []
            for certification_draft in certification_drafts:
                certification = Certification(
                    **certification_draft.model_dump())
                certification.id = None
                certification.building_id = building.id
                self.session.add(certification)
                await self.session.commit()
                await self.session.refresh(certification)
                building_dict['certifications'].append(
                    certification.model_dump())

            study_dict['buildings'].append(building_dict)

        # Instruments
        study_dict['instruments'] = []
        for instrument_draft in instrument_drafts:
            parameters_drafts = instrument_draft.parameters
            instrument_draft.parameters = []
            instrument = Instrument(**instrument_draft.model_dump())
            instrument.id = None
            instrument.study_id = study.id
            self.session.add(instrument)
            await self.session.commit()
            await self.session.refresh(instrument)
            instrument_dict = instrument.model_dump()

            # Parameters
            instrument_dict['parameters'] = []
            for param_draft in parameters_drafts:
                param = InstrumentParameter(**param_draft.model_dump())
                param.id = None
                param.instrument_id = instrument.id
                self.session.add(param)
                await self.session.commit()
                await self.session.refresh(param)
                instrument_dict['parameters'].append(param.model_dump())

            study_dict['instruments'].append(instrument_dict)

        # Datasets
        study_dict['datasets'] = []
        for dataset_draft in datasets_drafts:
            variable_drafts = dataset_draft.variables
            dataset_draft.variables = []
            dataset = Dataset(**dataset_draft.model_dump())
            dataset.id = None
            dataset.study_id = study.id

            # Files
            if dataset_draft.folder:
                new_folder = dataset_draft.folder['path'].replace(
                    "/draft/", "/pub/")
                dataset.folder['path'] = new_folder
                children = []
                for child in dataset_draft.folder['children']:
                    new_child = child.copy()
                    new_child['path'] = new_child['path'].replace(
                        "/draft/", "/pub/")
                    children.append(new_child)
                dataset.folder['children'] = children

            self.session.add(dataset)
            await self.session.commit()
            await self.session.refresh(dataset)
            dataset_dict = dataset.model_dump()

            # Variables
            dataset_dict['variables'] = []
            for variable_draft in variable_drafts:
                variable_draft.dataset_id = dataset.id
                variable = Variable(**variable_draft.model_dump())
                variable.id = None
                self.session.add(variable)
                await self.session.commit()
                await self.session.refresh(variable)
                dataset_dict['variables'].append(variable.model_dump())
            study_dict['datasets'].append(dataset_dict)

        # Dump full study in JSON format
        with tempfile.TemporaryDirectory() as temp_dir:
            print(f"Temporary directory created at: {temp_dir}")
            temp_file_path = os.path.join(temp_dir, "study.json")
            with open(temp_file_path, "w") as temp_file:
                json.dump(study_dict, temp_file, indent=2)
            await s3_client.upload_local_file(temp_dir, "study.json", s3_folder=pub_folder)

        return await self.get(study.id)

    async def count_group_by(self, filter: dict, group_by: str) -> dict:
        """Count all studies matching filter"""
        builder = StudyQueryBuilder(Study, filter, [], [], {
            "$building": Building, "$space": Space})

        # Do a query to satisfy total count
        count_query = builder.build_group_query_with_joins(
            filter, getattr(Study, group_by))
        group_by_count_res = await self.session.exec(count_query)
        group_by_counts = group_by_count_res.all()

        # Convert to dict
        return GroupByResult(
            field=group_by,
            counts=[GroupByCount(value=str(item[0]) if item[0] else None, count=item[1])
                    for item in group_by_counts])
