// This is just an example,
// so you can safely delete all default props below

export default {
  app_title: 'iAQ DB',
  app_subtitle: 'The indoor air quality database',
  error_not_found: 'Oops. Nothing here...',
  filters: 'Filters',
  it4r_contrib: 'UI/UX design, application development and deployment',
  layer: {
    buildings: 'Buildings',
    'climate-zones': 'Climate zones',
  },
  timeframe: 'Time frame',
  timeframe_help: 'Start/end dates of the studies are in the time frame.',
  altitudes: 'Altitude',
  altitudes_help: 'Altitude of the building',
  layers: 'Layers',
  legends: 'Legends',
  home: 'Home',
  introduction: 'Introduction',
  climate_zones: 'Climate zones',
  climate_zones_hint: 'The Köppen-Geiger climate classes (1991-2020).',
  number_of_buildings: 'Number of buildings',
  reset_filters: 'Reset filters',
  resources: 'Resources',
  source_code: 'Source Code',
  with_tsunami: 'With tsunami',
  search: 'Search',
  studies: 'Studies',
  buildings: 'Buildings',
  spaces: 'Spaces',
  mechanical: 'Mechanical',
  natural: 'Natural',
  ventilations: 'Ventilations',
  ventilations_hint: 'The space ventilation system.',
  contribute_title: 'Contribute to the Indoor Air Quality Research Database',
  from_to: 'From {from} to {to}',
  voc: 'VOC',
  voc_hint: 'Datasets with volatile organic compound measures.',
  study: {
    name: 'Name',
    name_hint: 'Name of the project',
    description: 'Description',
    description_hint:
      'Detailed description of the project and of its motivations.',
    building_count: 'Building count',
    building_count_hint:
      'Number of buildings in the study (can be higher than the ones described).',
    space_count: 'Space count',
    space_count_hint:
      'Number of spaces in the study (can be higher than the ones described).',
    url: 'Website address',
    url_hint: 'The website of the study, if available.',
    start_year: 'Start year',
    start_year_hint: 'Year at which the study was started.',
    end_year: 'End year',
    end_year_hint: 'Year at which the study ended or will end.',
    funding: 'Funding',
    funding_hint: 'Funding sources for the study.',
    ethics: 'Ethics',
    ethics_hint: 'Ethical considerations of the study.',
    duration: 'Duration (days)',
    duration_hint: 'Number of days of a full field campaign.',
    occupant_impact: 'Occupant impact',
    occupant_impact_hint: 'Studied impact on the occupants.',
    other_indoor_param: 'Other indoor parameter',
    other_indoor_param_hint: 'Other indoor parameter that was studied.',
    person_name: 'Name',
    person_name_hint: "The contact person's name.",
    person_email: 'Email',
    person_email_hint: "The contact person's email.",
    person_email_public: 'Email is publicly visible',
    person_institution: 'Institution',
    person_institution_hint: "The contact person's institution.",
    citation: 'Citation',
    citation_hint: 'How to cite the reference publication.',
    doi: 'DOI',
    doi_hint: '',
    license: 'License',
    license_hint: 'Usage license that applies to the contributed datasets.',
    building: {
      identifier: 'Identifier',
      identifier_hint: 'Building unique identifier in the study.',
      city: 'City',
      city_hint: 'City where the building is located.',
      country: 'Country',
      country_hint: 'Country where the building is located.',
      postcode: 'Postal code',
      postcode_hint: "Postal code of the building's location.",
      longitude: 'Longitude',
      longitude_hint: "Longitude of the building's location.",
      latitude: 'Latitude',
      latitude_hint: "Latitude of the building's location.",
      altitude: 'Altitude',
      altitude_hint: "Altitude of the building's location.",
      climate_zone: 'Climate zone',
      climate_zone_hint: "Climate zone of the building's location.",
      type: 'Type',
      type_hint: 'The type of usage of the building.',
      outdoor_env: 'Outdoor environment',
      outdoor_env_hint: 'Building surroundings.',
      ventilation: 'Ventilation',
      ventilation_hint: '',
      certification_program: 'Green certification program',
      certification_program_hint:
        'Name of the green building certification program.',
      certification_level: 'Green certification level',
      certification_level_hint: 'Level of building certification.',
      construction_year: 'Construction year',
      construction_year_hint: '',
      renovation_year: 'Renovation year',
      renovation_year_hint: '',
      special_population: 'Special population',
      special_population_hint: 'Special population designation.',
      mechanical_ventilation: 'Mechanical ventilation',
      mechanical_ventilation_hint: '',
      operable_windows: 'Operable windows',
      operable_windows_hint: '',
      smoking: 'Smoking permitted',
      smoking_hint: '',
      green_certified: 'Green certified',
      green_certified_hint: 'Whether the building was certified as green.',
    },
    space: {
      identifier: 'Identifier',
      identifier_hint: 'Space unique identifier in the building.',
      type: 'Type',
      type_hint: '',
      occupancy: 'Occupancy',
      occupancy_hint: '',
      ventilation_status: 'Ventilation status',
      ventilation_status_hint: '',
      ventilation_type: 'Ventilation type',
      ventilation_type_hint: '',
      windows_status: 'Windows status',
      windows_status_hint: '',
      ventilation_rate: 'Ventilation rate',
      ventilation_rate_hint: 'Airflow rate in m3/h.',
      air_change_rate: 'Air change rate',
      air_change_rate_hint: 'Air change rates (l/h)',
      particle_filtration_rating: 'Particle filtration rating',
      particle_filtration_rating_hint: 'Rating system and filter class.',
      cooling_status: 'Cooling status',
      cooling_status_hint: '',
      cooling_type: 'Cooling type',
      cooling_type_hint: '',
      heating_status: 'Heating status',
      heating_status_hint: '',
      heating_type: 'Heating type',
      heating_type_hint: '',
      combustion_sources: 'Combustion sources',
      combustion_sources_hint: '',
      major_combustion_sources: 'Major combustion sources',
      major_combustion_sources_hint: '',
      minor_combustion_sources: 'Minor combustion sources',
      minor_combustion_sources_hint: '',
      printers: 'Printers',
      printers_hint: '',
      carpets: 'Carpets',
      carpets_hint: '',
      pets: 'Pets',
      pets_hint: '',
      dampness: 'Dampness',
      dampness_hint: '',
      mold: 'Mold',
      mold_hint: '',
      detergents: 'Detergents',
      detergents_hint: '',
    },
    instrument: {
      identifier: 'Identifier',
      identifier_hint: 'Instrument unique identifier in the study.',
      manufacturer: 'Manufacturer',
      manufacturer_hint: 'Instrument manufacturer.',
      model: 'Model',
      model_hint: 'Instrument model.',
      equipment_grade: 'Equipment grade rating',
      equipment_grade_hint: 'Instrument grade rating.',
      placement: 'Placement',
      placement_hint: 'Instrument placement.',
    },
    parameter: {
      physical_parameter: 'Physical parameter',
      physical_parameter_hint: 'Physical parameter measured by the instrument.',
      analysis_method: 'Analysis method',
      analysis_method_hint: 'Method used to analyze the physical parameter.',
      measurement_uncertainty: 'Measurement uncertainty',
      measurement_uncertainty_hint:
        'Measurement uncertainty of the physical parameter.',
    },
  },
};
