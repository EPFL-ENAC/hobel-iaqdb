export const climateOptions = [
  { value: 'Af', label: '[Af]  Tropical, rainforest' },
  { value: 'Am', label: '[Am]  Tropical, monsoon' },
  { value: 'Aw', label: '[Aw]  Tropical, savannah' },
  { value: 'BWh', label: '[BWh] Arid, desert, hot' },
  { value: 'BWk', label: '[BWk] Arid, desert, cold' },
  { value: 'BSh', label: '[BSh] Arid, steppe, hot' },
  { value: 'BSk', label: '[BSk] Arid, steppe, cold' },
  { value: 'Csa', label: '[Csa] Temperate, dry summer, hot summer' },
  { value: 'Csb', label: '[Csb] Temperate, dry summer, warm summer' },
  { value: 'Csc', label: '[Csc] Temperate, dry summer, cold summer' },
  { value: 'Cwa', label: '[Cwa] Temperate, dry winter, hot summer' },
  { value: 'Cwb', label: '[Cwb] Temperate, dry winter, warm summer' },
  { value: 'Cwc', label: '[Cwc] Temperate, dry winter, cold summer' },
  { value: 'Cfa', label: '[Cfa] Temperate, no dry season, hot summer' },
  { value: 'Cfb', label: '[Cfb] Temperate, no dry season, warm summer' },
  { value: 'Cfc', label: '[Cfc] Temperate, no dry season, cold summer' },
  { value: 'Dsa', label: '[Dsa] Cold, dry summer, hot summer' },
  { value: 'Dsb', label: '[Dsb] Cold, dry summer, warm summer' },
  { value: 'Dsc', label: '[Dsc] Cold, dry summer, cold summer' },
  { value: 'Dsd', label: '[Dsd] Cold, dry summer, very cold winter' },
  { value: 'Dwa', label: '[Dwa] Cold, dry winter, hot summer' },
  { value: 'Dwb', label: '[Dwb] Cold, dry winter, warm summer' },
  { value: 'Dwc', label: '[Dwc] Cold, dry winter, cold summer' },
  { value: 'Dwd', label: '[Dwd] Cold, dry winter, very cold winter' },
  { value: 'Dfa', label: '[Dfa] Cold, no dry season, hot summer' },
  { value: 'Dfb', label: '[Dfb] Cold, no dry season, warm summer' },
  { value: 'Dfc', label: '[Dfc] Cold, no dry season, cold summer' },
  { value: 'Dfd', label: '[Dfd] Cold, no dry season, very cold winter' },
  { value: 'ET', label: '[ET]  Polar, tundra' },
  { value: 'EF', label: '[EF]  Polar, frost' },
];

export const occupantImpactOptions = [
  { value: 'health', label: 'Health' },
  { value: 'comfort', label: 'Comfort' },
  { value: 'satisfaction', label: 'Satisfaction' },
  { value: 'performance', label: 'Performance' },
  { value: 'well-being', label: 'Well-being' },
  { value: 'na', label: 'Not applicable' },
];

export const otherIndoorParamOptions = [
  { value: 'thermal', label: 'Thermal' },
  { value: 'acoustic', label: 'Acoustic' },
  { value: 'visual', label: 'Visual' },
  { value: 'na', label: 'Not applicable' },
];

export const ventilationStatusOptions = [
  { value: 'on', label: 'On' },
  { value: 'off', label: 'Off' },
  { value: 'mixed', label: 'Mixed' },
  { value: 'unknown', label: 'Unknown' },
  { value: 'na', label: 'Not applicable' },
];

export const ventilationTypeOptions = [
  { value: 'mixing', label: 'Mixing' },
  { value: 'displacement', label: 'Displacement' },
  { value: 'exhaust only', label: 'Exhaust only' },
  { value: 'other', label: 'Other' },
  { value: 'unknown', label: 'Unknown' },
  { value: 'na', label: 'Not applicable' },
];

export const windowsStatusOptions = [
  { value: 'open', label: 'Open' },
  { value: 'closed', label: 'Closed' },
  { value: 'unknown', label: 'Unknown' },
  { value: 'na', label: 'Not applicable' },
];

export const coolingStatusOptions = [
  { value: 'on', label: 'On' },
  { value: 'off', label: 'Off' },
  { value: 'mixed', label: 'Mixed' },
  { value: 'unknown', label: 'Unknown' },
  { value: 'na', label: 'Not applicable' },
];

export const coolingTypeOptions = [
  { value: 'forced air', label: 'Forced air' },
  { value: 'fan coil units', label: 'Fan coil units' },
  { value: 'ceiling radiant', label: 'Ceiling radiant' },
  { value: 'floor radiant', label: 'Floor radiant' },
  { value: 'other', label: 'Other' },
  { value: 'unknown', label: 'Unknown' },
  { value: 'na', label: 'Not applicable' },
];

export const heatingStatusOptions = [
  { value: 'on', label: 'On' },
  { value: 'off', label: 'Off' },
  { value: 'mixed', label: 'Mixed' },
  { value: 'unknown', label: 'Unknown' },
  { value: 'na', label: 'Not applicable' },
];

export const heatingTypeOptions = [
  { value: 'forced air', label: 'Forced air' },
  { value: 'fan coil units', label: 'Fan coil units' },
  { value: 'ceiling radiant', label: 'Ceiling radiant' },
  { value: 'floor radiant', label: 'Floor radiant' },
  { value: 'radiator', label: 'Radiator' },
  { value: 'other', label: 'Other' },
  { value: 'unknown', label: 'Unknown' },
  { value: 'na', label: 'Not applicable' },
];

export const majorCombustionSourcesOptions = [
  {
    value: 'unvented kerosene and gas space heaters',
    label: 'Unvented kerosene and gas space heaters',
  },
  { value: 'wood stoves', label: 'Wood stoves' },
  { value: 'fireplaces', label: 'Fireplaces' },
  { value: 'gas stoves', label: 'Gas stoves' },
  { value: 'other', label: 'Other' },
];

export const minorCombustionSourcesOptions = [
  { value: 'candles', label: 'Candles' },
  { value: 'incense', label: 'Incense' },
  { value: 'other', label: 'Other' },
];

export const buildingTypeOptions = [
  { value: 'multifamily residential', label: 'Multifamily residential' },
  { value: 'dwelling', label: 'Dwelling' },
  { value: 'office', label: 'Office' },
  { value: 'school', label: 'School' },
  { value: 'senior center', label: 'Senior Center' },
  { value: 'hospital', label: 'Hospital' },
  { value: 'retail', label: 'Retail' },
  { value: 'sport center,', label: 'Sport center' },
  { value: 'other', label: 'Other' },
];

export const outdoorEnvOptions = [
  { value: 'rural', label: 'Rural' },
  { value: 'urban', label: 'Urban' },
  { value: 'suburban', label: 'Suburban' },
  { value: 'industrialized', label: 'Industrialized' },
  { value: 'unknown', label: 'Unknown' },
];

export const populationOptions = [
  { value: 'low-income', label: 'Low-income' },
  { value: 'middle-income', label: 'Middle-income' },
  { value: 'high-income', label: 'High-income' },
  { value: 'Elderly', label: 'Elderly' },
  { value: 'children', label: 'Children' },
  { value: 'other', label: 'Other' },
  { value: 'na', label: 'Not applicable' },
];

export const yesNoOptions = [
  { value: 'yes', label: 'Yes' },
  { value: 'no', label: 'No' },
  { value: 'unknown', label: 'Unknown' },
];

export const spaceTypeOptions = [
  { value: 'living room', label: 'Living room' },
  { value: 'kitchen', label: 'Kitchen' },
  { value: 'bedroom', label: 'Bedroom' },
  { value: 'basement', label: 'Basement' },
  { value: 'garage', label: 'Garage' },
  { value: 'enclosed shared office', label: 'Enclosed shared office' },
  { value: 'enclosed private office', label: 'Enclosed private office' },
  { value: 'open office', label: 'Open office' },
  { value: 'focus room', label: 'Focus room' },
  { value: 'hallway', label: 'Hallway' },
  { value: 'restaurant', label: 'Restaurant' },
  { value: 'supermarket', label: 'Supermarket' },
  { value: 'waiting room', label: 'Waiting room' },
  { value: 'patient room', label: 'Patient room' },
  { value: 'classroom', label: 'Classroom' },
  { value: 'outdoor', label: 'Outdoor' },
  { value: 'other', label: 'Other' },
];

export const occupancyOptions = [
  { value: 'occupied', label: 'Occupied' },
  { value: 'unoccupied', label: 'Unoccupied' },
  { value: 'combined', label: 'Combined' },
  { value: 'unknown', label: 'Unknown' },
];

export const equipmentGradeOptions = [
  { value: 'research-grade', label: 'Research-grade' },
  { value: 'mid-level', label: 'Mid-level' },
  { value: 'low-cost', label: 'Low-cost' },
  { value: 'unknown', label: 'Unknown' },
];

export const placementOptions = [
  { value: 'ceiling', label: 'Ceiling' },
  { value: 'lateral wall', label: 'Lateral wall' },
  { value: 'air return', label: 'Air return' },
  { value: 'desk', label: 'Desk' },
  { value: 'other', label: 'Other' },
  { value: 'mixed', label: 'Mixed' },
  { value: 'unknown', label: 'Unknown' },
];

export const physicalParameterOptions = [
  { value: 'individual voc', label: 'Individual VOC' },
  { value: 'tvoc', label: 'TVOC' },
  { value: 'pm10', label: 'PM10' },
  { value: 'pm2.5', label: 'PM2.5' },
  { value: 'pm1', label: 'PM1' },
  { value: 'particle number ≤10μm', label: 'Particle number ≤10μm' },
  { value: 'particle number ≤2.5μm', label: 'Particle number ≤2.5μm' },
  { value: 'particle number ≤1μm', label: 'Particle number ≤1μm' },
  { value: 'nanoparticles', label: 'Nanoparticles' },
  { value: 'carbon dioxide', label: 'Carbon dioxide' },
  { value: 'carbon monoxide', label: 'Carbon monoxide' },
  { value: 'ozone', label: 'Ozone' },
  { value: 'radon', label: 'Radon' },
  { value: 'sulphur dioxide', label: 'Sulphur dioxide' },
  { value: 'nitrogen dioxide', label: 'Nitrogen dioxide' },
  { value: 'lead', label: 'Lead' },
  { value: 'air temperature', label: 'Air temperature' },
  { value: 'relative humidity', label: 'Relative humidity' },
  { value: 'occupancy', label: 'Occupancy' },
  {
    value: 'mechanical ventilation rate',
    label: 'Mechanical ventilation rate',
  },
  { value: 'biocontaminants', label: 'Biocontaminants' },
];

export const referenceOptions = [
  { value: 'building', label: 'Building ID' },
  { value: 'space', label: 'Space ID' },
  { value: 'instrument', label: 'Instrument ID' },
  { value: 'timestamp', label: 'Timestamp' },
  ...physicalParameterOptions,
  { value: 'other', label: 'Other' },
];

export const countryOptions = [
  { value: 'AF', label: 'Afghanistan' },
  { value: 'AX', label: 'Åland Islands' },
  { value: 'AL', label: 'Albania' },
  { value: 'DZ', label: 'Algeria' },
  { value: 'AS', label: 'American Samoa' },
  { value: 'AD', label: 'Andorra' },
  { value: 'AO', label: 'Angola' },
  { value: 'AI', label: 'Anguilla' },
  { value: 'AQ', label: 'Antarctica' },
  { value: 'AG', label: 'Antigua and Barbuda' },
  { value: 'AR', label: 'Argentina' },
  { value: 'AM', label: 'Armenia' },
  { value: 'AW', label: 'Aruba' },
  { value: 'AU', label: 'Australia' },
  { value: 'AT', label: 'Austria' },
  { value: 'AZ', label: 'Azerbaijan' },
  { value: 'BS', label: 'Bahamas' },
  { value: 'BH', label: 'Bahrain' },
  { value: 'BD', label: 'Bangladesh' },
  { value: 'BB', label: 'Barbados' },
  { value: 'BY', label: 'Belarus' },
  { value: 'BE', label: 'Belgium' },
  { value: 'BZ', label: 'Belize' },
  { value: 'BJ', label: 'Benin' },
  { value: 'BM', label: 'Bermuda' },
  { value: 'BT', label: 'Bhutan' },
  { value: 'BO', label: 'Bolivia (Plurinational State of)' },
  { value: 'BQ', label: 'Bonaire, Sint Eustatius and Saba' },
  { value: 'BA', label: 'Bosnia and Herzegovina' },
  { value: 'BW', label: 'Botswana' },
  { value: 'BV', label: 'Bouvet Island' },
  { value: 'BR', label: 'Brazil' },
  { value: 'IO', label: 'British Indian Ocean Territory' },
  { value: 'BN', label: 'Brunei Darussalam' },
  { value: 'BG', label: 'Bulgaria' },
  { value: 'BF', label: 'Burkina Faso' },
  { value: 'BI', label: 'Burundi' },
  { value: 'CV', label: 'Cabo Verde' },
  { value: 'KH', label: 'Cambodia' },
  { value: 'CM', label: 'Cameroon' },
  { value: 'CA', label: 'Canada' },
  { value: 'KY', label: 'Cayman Islands' },
  { value: 'CF', label: 'Central African Republic' },
  { value: 'TD', label: 'Chad' },
  { value: 'CL', label: 'Chile' },
  { value: 'CN', label: 'China' },
  { value: 'CX', label: 'Christmas Island' },
  { value: 'CC', label: 'Cocos (Keeling) Islands' },
  { value: 'CO', label: 'Colombia' },
  { value: 'KM', label: 'Comoros' },
  { value: 'CG', label: 'Congo' },
  { value: 'CD', label: 'Congo (Democratic Republic of the)' },
  { value: 'CK', label: 'Cook Islands' },
  { value: 'CR', label: 'Costa Rica' },
  { value: 'CI', label: "Côte d'Ivoire" },
  { value: 'HR', label: 'Croatia' },
  { value: 'CU', label: 'Cuba' },
  { value: 'CW', label: 'Curaçao' },
  { value: 'CY', label: 'Cyprus' },
  { value: 'CZ', label: 'Czechia' },
  { value: 'DK', label: 'Denmark' },
  { value: 'DJ', label: 'Djibouti' },
  { value: 'DM', label: 'Dominica' },
  { value: 'DO', label: 'Dominican Republic' },
  { value: 'EC', label: 'Ecuador' },
  { value: 'EG', label: 'Egypt' },
  { value: 'SV', label: 'El Salvador' },
  { value: 'GQ', label: 'Equatorial Guinea' },
  { value: 'ER', label: 'Eritrea' },
  { value: 'EE', label: 'Estonia' },
  { value: 'SZ', label: 'Eswatini' },
  { value: 'ET', label: 'Ethiopia' },
  { value: 'FK', label: 'Falkland Islands (Malvinas)' },
  { value: 'FO', label: 'Faroe Islands' },
  { value: 'FJ', label: 'Fiji' },
  { value: 'FI', label: 'Finland' },
  { value: 'FR', label: 'France' },
  { value: 'GF', label: 'French Guiana' },
  { value: 'PF', label: 'French Polynesia' },
  { value: 'TF', label: 'French Southern Territories' },
  { value: 'GA', label: 'Gabon' },
  { value: 'GM', label: 'Gambia' },
  { value: 'GE', label: 'Georgia' },
  { value: 'DE', label: 'Germany' },
  { value: 'GH', label: 'Ghana' },
  { value: 'GI', label: 'Gibraltar' },
  { value: 'GR', label: 'Greece' },
  { value: 'GL', label: 'Greenland' },
  { value: 'GD', label: 'Grenada' },
  { value: 'GP', label: 'Guadeloupe' },
  { value: 'GU', label: 'Guam' },
  { value: 'GT', label: 'Guatemala' },
  { value: 'GG', label: 'Guernsey' },
  { value: 'GN', label: 'Guinea' },
  { value: 'GW', label: 'Guinea-Bissau' },
  { value: 'GY', label: 'Guyana' },
  { value: 'HT', label: 'Haiti' },
  { value: 'HM', label: 'Heard Island and McDonald Islands' },
  { value: 'VA', label: 'Holy See' },
  { value: 'HN', label: 'Honduras' },
  { value: 'HK', label: 'Hong Kong' },
  { value: 'HU', label: 'Hungary' },
  { value: 'IS', label: 'Iceland' },
  { value: 'IN', label: 'India' },
  { value: 'ID', label: 'Indonesia' },
  { value: 'IR', label: 'Iran (Islamic Republic of)' },
  { value: 'IQ', label: 'Iraq' },
  { value: 'IE', label: 'Ireland' },
  { value: 'IM', label: 'Isle of Man' },
  { value: 'IL', label: 'Israel' },
  { value: 'IT', label: 'Italy' },
  { value: 'JM', label: 'Jamaica' },
  { value: 'JP', label: 'Japan' },
  { value: 'JE', label: 'Jersey' },
  { value: 'JO', label: 'Jordan' },
  { value: 'KZ', label: 'Kazakhstan' },
  { value: 'KE', label: 'Kenya' },
  { value: 'KI', label: 'Kiribati' },
  { value: 'KP', label: "Korea (Democratic People's Republic of)" },
  { value: 'KR', label: 'Korea (Republic of)' },
  { value: 'KW', label: 'Kuwait' },
  { value: 'KG', label: 'Kyrgyzstan' },
  { value: 'LA', label: "Lao People's Democratic Republic" },
  { value: 'LV', label: 'Latvia' },
  { value: 'LB', label: 'Lebanon' },
  { value: 'LS', label: 'Lesotho' },
  { value: 'LR', label: 'Liberia' },
  { value: 'LY', label: 'Libya' },
  { value: 'LI', label: 'Liechtenstein' },
  { value: 'LT', label: 'Lithuania' },
  { value: 'LU', label: 'Luxembourg' },
  { value: 'MO', label: 'Macao' },
  { value: 'MG', label: 'Madagascar' },
  { value: 'MW', label: 'Malawi' },
  { value: 'MY', label: 'Malaysia' },
  { value: 'MV', label: 'Maldives' },
  { value: 'ML', label: 'Mali' },
  { value: 'MT', label: 'Malta' },
  { value: 'MH', label: 'Marshall Islands' },
  { value: 'MQ', label: 'Martinique' },
  { value: 'MR', label: 'Mauritania' },
  { value: 'MU', label: 'Mauritius' },
  { value: 'YT', label: 'Mayotte' },
  { value: 'MX', label: 'Mexico' },
  { value: 'FM', label: 'Micronesia (Federated States of)' },
  { value: 'MD', label: 'Moldova (Republic of)' },
  { value: 'MC', label: 'Monaco' },
  { value: 'MN', label: 'Mongolia' },
  { value: 'ME', label: 'Montenegro' },
  { value: 'MS', label: 'Montserrat' },
  { value: 'MA', label: 'Morocco' },
  { value: 'MZ', label: 'Mozambique' },
  { value: 'MM', label: 'Myanmar' },
  { value: 'NA', label: 'Namibia' },
  { value: 'NR', label: 'Nauru' },
  { value: 'NP', label: 'Nepal' },
  { value: 'NL', label: 'Netherlands' },
  { value: 'NC', label: 'New Caledonia' },
  { value: 'NZ', label: 'New Zealand' },
  { value: 'NI', label: 'Nicaragua' },
  { value: 'NE', label: 'Niger' },
  { value: 'NG', label: 'Nigeria' },
  { value: 'NU', label: 'Niue' },
  { value: 'NF', label: 'Norfolk Island' },
  { value: 'MK', label: 'North Macedonia' },
  { value: 'MP', label: 'Northern Mariana Islands' },
  { value: 'NO', label: 'Norway' },
  { value: 'OM', label: 'Oman' },
  { value: 'PK', label: 'Pakistan' },
  { value: 'PW', label: 'Palau' },
  { value: 'PS', label: 'Palestine, State of' },
  { value: 'PA', label: 'Panama' },
  { value: 'PG', label: 'Papua New Guinea' },
  { value: 'PY', label: 'Paraguay' },
  { value: 'PE', label: 'Peru' },
  { value: 'PH', label: 'Philippines' },
  { value: 'PN', label: 'Pitcairn' },
  { value: 'PL', label: 'Poland' },
  { value: 'PT', label: 'Portugal' },
  { value: 'PR', label: 'Puerto Rico' },
  { value: 'QA', label: 'Qatar' },
  { value: 'RE', label: 'Réunion' },
  { value: 'RO', label: 'Romania' },
  { value: 'RU', label: 'Russian Federation' },
  { value: 'RW', label: 'Rwanda' },
  { value: 'BL', label: 'Saint Barthélemy' },
  { value: 'SH', label: 'Saint Helena, Ascension and Tristan da Cunha' },
  { value: 'KN', label: 'Saint Kitts and Nevis' },
  { value: 'LC', label: 'Saint Lucia' },
  { value: 'MF', label: 'Saint Martin (French part)' },
  { value: 'PM', label: 'Saint Pierre and Miquelon' },
  { value: 'VC', label: 'Saint Vincent and the Grenadines' },
  { value: 'WS', label: 'Samoa' },
  { value: 'SM', label: 'San Marino' },
  { value: 'ST', label: 'Sao Tome and Principe' },
  { value: 'SA', label: 'Saudi Arabia' },
  { value: 'SN', label: 'Senegal' },
  { value: 'RS', label: 'Serbia' },
  { value: 'SC', label: 'Seychelles' },
  { value: 'SL', label: 'Sierra Leone' },
  { value: 'SG', label: 'Singapore' },
  { value: 'SX', label: 'Sint Maarten (Dutch part)' },
  { value: 'SK', label: 'Slovakia' },
  { value: 'SI', label: 'Slovenia' },
  { value: 'SB', label: 'Solomon Islands' },
  { value: 'SO', label: 'Somalia' },
  { value: 'ZA', label: 'South Africa' },
  { value: 'GS', label: 'South Georgia and the South Sandwich Islands' },
  { value: 'SS', label: 'South Sudan' },
  { value: 'ES', label: 'Spain' },
  { value: 'LK', label: 'Sri Lanka' },
  { value: 'SD', label: 'Sudan' },
  { value: 'SR', label: 'Suriname' },
  { value: 'SJ', label: 'Svalbard and Jan Mayen' },
  { value: 'SE', label: 'Sweden' },
  { value: 'CH', label: 'Switzerland' },
  { value: 'SY', label: 'Syrian Arab Republic' },
  { value: 'TW', label: 'Taiwan, Province of China' },
  { value: 'TJ', label: 'Tajikistan' },
  { value: 'TZ', label: 'Tanzania, United Republic of' },
  { value: 'TH', label: 'Thailand' },
  { value: 'TL', label: 'Timor-Leste' },
  { value: 'TG', label: 'Togo' },
  { value: 'TK', label: 'Tokelau' },
  { value: 'TO', label: 'Tonga' },
  { value: 'TT', label: 'Trinidad and Tobago' },
  { value: 'TN', label: 'Tunisia' },
  { value: 'TR', label: 'Turkey' },
  { value: 'TM', label: 'Turkmenistan' },
  { value: 'TC', label: 'Turks and Caicos Islands' },
  { value: 'TV', label: 'Tuvalu' },
  { value: 'UG', label: 'Uganda' },
  { value: 'UA', label: 'Ukraine' },
  { value: 'AE', label: 'United Arab Emirates' },
  {
    value: 'GB',
    label: 'United Kingdom of Great Britain and Northern Ireland',
  },
  { value: 'UM', label: 'United States Minor Outlying Islands' },
  { value: 'US', label: 'United States of America' },
  { value: 'UY', label: 'Uruguay' },
  { value: 'UZ', label: 'Uzbekistan' },
  { value: 'VU', label: 'Vanuatu' },
  { value: 'VE', label: 'Venezuela (Bolivarian Republic of)' },
  { value: 'VN', label: 'Viet Nam' },
  { value: 'VG', label: 'Virgin Islands (British)' },
  { value: 'VI', label: 'Virgin Islands (U.S.)' },
  { value: 'WF', label: 'Wallis and Futuna' },
  { value: 'EH', label: 'Western Sahara' },
  { value: 'YE', label: 'Yemen' },
  { value: 'ZM', label: 'Zambia' },
  { value: 'ZW', label: 'Zimbabwe' },
];

export const licenseOptions = [
  {
    value: 'CC0',
    label: 'CC0 (Public Domain Dedication)',
    description:
      'No rights reserved. Data can be used by anyone for any purpose without permission.',
  },
  {
    value: 'CC BY',
    label: 'CC BY (Attribution)',
    description:
      'Users can distribute, remix, adapt, and build upon the data, even commercially, as long as they credit the original creation.',
  },
  {
    value: 'CC BY-SA',
    label: 'CC BY-SA (Attribution-ShareAlike)',
    description:
      'Users can distribute, remix, adapt, and build upon the data, even commercially, as long as they credit the original creation and license their new creations under the identical terms.',
  },
  {
    value: 'CC BY-NC',
    label: 'CC BY-NC (Attribution-NonCommercial)',
    description:
      'Users can distribute, remix, adapt, and build upon the data non-commercially, and although their new works must also acknowledge the original and be non-commercial, they don’t have to license their derivative works on the same terms.',
  },
  {
    value: 'CC BY-NC-SA',
    label: 'CC BY-NC-SA (Attribution-NonCommercial-ShareAlike)',
    description:
      'Users can distribute, remix, adapt, and build upon the data non-commercially, as long as they credit the original creation and license their new creations under the identical terms.',
  },
  {
    value: 'PDDL',
    label: 'Public Domain Dedication and License (PDDL)',
    description:
      'Similar to CC0, it allows data to be freely used by anyone for any purpose.',
  },
  {
    value: 'ODC-By',
    label: 'Attribution License (ODC-By)',
    description:
      'Allows for the sharing, modification, and use of data as long as attribution is given.',
  },
  {
    value: 'ODbL',
    label: 'Open Database License (ODbL)',
    description:
      'Allows for the sharing, modification, and use of data as long as attribution is given, and any new datasets created from the original are shared under the same terms.',
  },
  {
    value: 'GPL',
    label: 'GNU General Public License (GPL)',
    description:
      'Allows for the sharing, modification, and use of data, but requires that any derivative works or data be distributed under the same license.',
  },
  {
    value: 'MIT',
    label: 'MIT License',
    description:
      'A permissive license that allows for reuse, including closed-source use, as long as the original license is included with any substantial portions of the dataset.',
  },
  {
    value: 'Apache2',
    label: 'Apache License 2.0',
    description:
      'Allows for the reuse of data, including for commercial purposes, as long as the original license is included, and any modifications are clearly noted.',
  },
  {
    value: 'BSD',
    label: 'BSD License',
    description:
      'A permissive license that allows for the reuse of data, including closed-source use, as long as the original license is included. There are different versions (2-clause, 3-clause) with slight variations.',
  },
  {
    value: 'UK OGL',
    label: 'UK Open Government License',
    description:
      'Allows the use, modification, and distribution of data provided attribution is given.',
  },
  {
    value: 'Canada OGL',
    label: 'Canada Open Government License',
    description:
      'Allows the use, modification, and distribution of data provided attribution is given.',
  },
  {
    value: 'Australia OGL',
    label: 'Australia Open Government License',
    description:
      'Allows the use, modification, and distribution of data provided attribution is given.',
  },
  {
    value: 'EUPL',
    label: 'European Union Public License (EUPL)',
    description:
      'A license that allows for the use, modification, and distribution of data, with the requirement that derivative works be shared under the same license.',
  },
];

export const vocOptions = [
  { value: '100-41-4', label: 'Ethyl Benzene' },
  { value: '100-42-5', label: 'Styrene' },
  { value: '100-44-7', label: 'Benzyl Chloride' },
  { value: '100-51-6', label: 'Benzyl Alcohol' },
  { value: '103-65-1', label: 'Propyl Benzene' },
  { value: '104-46-1', label: 'Anethole' },
  { value: '104-76-7', label: '2-Ethyl-1-Hexanol' },
  { value: '105-37-3', label: 'Ethyl Propionate' },
  { value: '105-54-4', label: 'Ethyl butyrate' },
  { value: '106-22-9', label: 'Beta-Citronellol' },
  { value: '106-46-7', label: '1,4-Dichlorobenzene' },
  { value: '106-97-8', label: 'Butane' },
  { value: '106-99-0', label: '1,3-Butadiene' },
  { value: '107-05-1', label: 'Allyl Chloride' },
  { value: '107-06-2', label: '1,2-Dichloroethane' },
  { value: '107-07-3', label: '2-Chloroethanol' },
  { value: '107-13-1', label: 'Acrylonitrile' },
  { value: '107-31-3', label: 'Methyl Formate' },
  { value: '107-46-0', label: 'Hexamethyldisiloxane' },
  { value: '107-83-5', label: '2-Methylpentane' },
  { value: '107-87-9', label: '2-Pentanone' },
  { value: '107-98-2', label: '1-Methoxy-2-Propanol (PGME)' },
  { value: '108-05-4', label: 'Vinyl Acetate' },
  { value: '108-08-7', label: '2,4-Dimethylpentane' },
  { value: '108-10-1', label: 'Hexone (MIBK)' },
  { value: '108-20-3', label: 'Diisopropyl Ether' },
  { value: '108-21-4', label: 'Isopropyl Acetate' },
  { value: '108-38-3', label: 'M-Xylene' },
  { value: '108-65-6', label: 'Propylene Glycol Methyl Ether Acetate' },
  { value: '108-67-8', label: '1,3,5-Trimethylbenzène' },
  { value: '108-87-2', label: 'Methylcyclohexane' },
  { value: '108-88-3', label: 'Toluene' },
  { value: '108-90-7', label: 'Chlorobenzene' },
  { value: '108-93-0', label: 'Cyclohexanol' },
  { value: '108-94-1', label: 'Cyclohexanone' },
  { value: '108-98-5', label: 'Thiophenol' },
  { value: '109.86-4', label: '2-Methoxyethanol' },
  { value: '109-60-4', label: 'n-Propyl Acetate' },
  { value: '109-66-0', label: 'n-Pentane' },
  { value: '109-79-5', label: '1-Butanethiol' },
  { value: '109-87-5', label: 'Dimethoxymethane' },
  { value: '109-94-4', label: 'Ethyl Formate' },
  { value: '109-99-9', label: 'Tetrahydrofuran' },
  { value: '110-05-4', label: 'Di-t-Butyl Peroxyde' },
  { value: '110-19-0', label: 'Isobutyl Acetate' },
  { value: '110-54-3', label: 'n-Hexane' },
  { value: '110-80-5', label: '2-Ethoxyethanol' },
  { value: '110-82-7', label: 'Cyclohexane' },
  { value: '110-86-1', label: 'Pyridine' },
  { value: '111-15-9', label: '2-Ethoxyethylacetate' },
  { value: '111-65-9', label: 'Octane (all isomers)' },
  { value: '111-66-0', label: '1-Octene' },
  { value: '111-76-2', label: 'Butylcellosolve (2-Butoxyethanol)' },
  { value: '111-84-2', label: 'Nonane' },
  { value: '111-90-0', label: 'Diethylene Glycol Ethyl Ether' },
  { value: '111-96-0', label: 'DEGDME' },
  { value: '1120-21-4', label: 'Undecane' },
  { value: '112-07-2', label: '2-Butoxyethylacetate' },
  { value: '112-25-4', label: 'EGHE' },
  { value: '112-31-2', label: 'Decanal' },
  { value: '112-34-5', label: 'Diethylene Glycol Monobutyl Ether' },
  { value: '112-40-3', label: 'Dodecane' },
  { value: '115-10-6', label: 'Dimethyl ether' },
  { value: '115-11-7', label: '2-methyl-1-propene' },
  { value: '1192-18-3', label: '1,2-Dimethylcyclopentane' },
  { value: '120-82-1', label: '1,2,4-Trichlorobenzene' },
  { value: '121-43-7', label: 'Trimethyl Borate' },
  { value: '123-51-3', label: '3-Methyl-1-Butanol' },
  { value: '123-86-4', label: 'Butyl Acetate' },
  { value: '123-92-2', label: 'Isoamyl Acetate' },
  { value: '124-17-4', label: 'Diethylene Glycol Monobutyl Ether Acetate' },
  { value: '124-18-5', label: 'Decane' },
  { value: '124-19-6', label: 'Nonanal' },
  { value: '127-18-4', label: 'Perchloroethylene' },
  { value: '127-91-3', label: 'beta-Pinene' },
  { value: '1330-20-7', label: 'Xylenes' },
  { value: '13466-78-9', label: '3-Carene' },
  { value: '140-11-4', label: 'Benzyl Acetate' },
  { value: '140-67-0', label: 'Estragole (1,8-Cineole)' },
  { value: '140-88-5', label: 'Ethyl Acrylate' },
  { value: '141-32-2', label: 'Butyl Acrylate' },
  { value: '141-63-9', label: 'Decamethylcyclopentasiloxane' },
  { value: '141-78-6', label: 'Ethyl Acetate' },
  { value: '142-82-5', label: 'n-Heptane' },
  { value: '142-92-7', label: 'n-Hexyl Acetate' },
  { value: '142-96-1', label: 'Butyl Ether' },
  { value: '1634-04-4', label: 'Methyl-t-Butyl Ether' },
  { value: '1640-89-7', label: 'Ethylcyclopentane' },
  { value: '2213-23-2', label: '2,4-Dimethylheptane' },
  { value: '2216-33-3', label: '3-Methyloctane' },
  { value: '2452-99-5', label: '1,2-Dimethylcyclopentane' },
  { value: '2453-00-1', label: '1,3-Dimethylcyclopentane' },
  { value: '25551-13-7', label: 'Triméthylbenzene' },
  { value: '287-92-3', label: 'Cyclopentane' },
  { value: '31017-40-0', label: '4-Phenylcyclohexane' },
  { value: '31807-55-3', label: '2,2,4,6-Pentamethylheptane' },
  { value: '34590-94-8', label: 'Dipropylene Glycol Methyl Ether' },
  { value: '431-03-8', label: 'Diacetyl' },
  { value: '470-67-7', label: 'Isocineole' },
  { value: '470-82-6', label: 'Eucalyptol' },
  { value: '5131-66-8', label: '1-Butoxy-2-Propanol' },
  { value: '513-53-1', label: '2-Butanethiol' },
  { value: '513-86-0', label: 'Acetoin' },
  { value: '51-79-6', label: 'Urethane' },
  { value: '526-73-8', label: '1,2,3-Trimethylbenzene' },
  { value: '534-15-6', label: '1,1-Dimethoxyethane' },
  { value: '5392-40-5', label: 'Citral' },
  { value: '540-51-2', label: '2-Bromoethanol' },
  { value: '540-84-1', label: 'Isooctane' },
  { value: '541-05-9', label: 'Hexamethylcyclotrisiloxane' },
  { value: '541-73-1', label: '1,3 Dichlorobenzene' },
  { value: '543-59-9', label: '1-chloropentane' },
  { value: '56-23-5', label: 'Carbon Tetrachloride' },
  { value: '562-49-2', label: '3,3-Dimethylpentane' },
  { value: '565-59-3', label: '2,3-Dimethylpentane' },
  { value: '583-57-3', label: '1,2-Dimethylcyclohexane' },
  { value: '589-34-4', label: '3-Methylhexane' },
  { value: '590-35-2', label: '2,2-Dimethylpentane' },
  { value: '591-68-4', label: 'Butyl valerate' },
  { value: '591-76-4', label: '2-Methylhexane' },
  { value: '592-13-2', label: '2,5-Dimethylhexane' },
  { value: '592-27-8', label: '2-Methylheptane' },
  { value: '5989-27-5', label: 'D-Limonene' },
  { value: '600-14-6', label: '2,3-Pentadione' },
  { value: '60-29-7', label: 'Ethyl Ether' },
  { value: '6032-29-7', label: '2-Pentanol' },
  { value: '611-14-3', label: '2-Ethyltoluene' },
  { value: '620-02-0', label: '5-Methyl Furfural' },
  { value: '620-14-4', label: 'm-Ethyltoluene' },
  { value: '622-96-8', label: '4-Ethyl Toluene' },
  { value: '623-42-7', label: 'Methyl Butyrate' },
  { value: '624-41-9', label: '2-Methyl-1-Butyl Acetate' },
  { value: '637-92-3', label: 'ETBE (ethyl-tert-butyl-ether)' },
  { value: '64-17-5', label: 'Ethanol' },
  { value: '67-63-0', label: 'Isopropyl Alcohol' },
  { value: '67-64-1', label: 'Acetone' },
  { value: '67-66-3', label: 'Chloroform' },
  { value: '71-23-8', label: '1-Propanol' },
  { value: '71-36-3', label: '1-Butyl Alcohol' },
  { value: '71-41-0', label: '1-Pentanol' },
  { value: '71-43-2', label: 'Benzene' },
  { value: '71-55-6', label: 'Methyl Chloroform' },
  { value: '7452-79-1', label: 'Ethyl 2-Methylbutanoate' },
  { value: '74-83-9', label: 'Methyl Bromide' },
  { value: '74-87-3', label: 'Chloromethane' },
  { value: '75-05-8', label: 'Acetonitrile' },
  { value: '75-09-2', label: 'Methylene Chloride' },
  { value: '75-18-3', label: 'Dimethylsulfide' },
  { value: '75-28-5', label: 'Isobutane' },
  { value: '75-29-6', label: 'Isopropyl chloride' },
  { value: '75-34-3', label: '1,1-Dichloroethane' },
  { value: '75-65-0', label: '2-Methyl-2-Propanol' },
  { value: '75-85-4', label: '2-Methyl-2-Butanol' },
  { value: '76-22-2', label: 'Camphor' },
  { value: '7785-70-8', label: 'Alpha-Pinene (1R)' },
  { value: '78-70-6', label: 'Linalol' },
  { value: '78-78-4', label: '2-Methylbutane' },
  { value: '78-83-1', label: '2-Methyl-1-Propanol' },
  { value: '78-92-2', label: '2-Butyl Alcohol' },
  { value: '78-93-3', label: '2-Butanone (MEK)' },
  { value: '79-01-6', label: 'Trichloroethylene' },
  { value: '79-20-9', label: 'Methyl Acetate' },
  { value: '79-92-5', label: 'Camphene' },
  { value: '80-62-6', label: 'Methyl Methacrylate' },
  { value: '868-57-5', label: 'Methyl-2-méthylbutyrate' },
  { value: '872-50-4', label: '1-Methyl-2-Pyrrolidinone' },
  { value: '91-20-3', label: 'Naphtalène' },
  { value: '95-47-6', label: 'O-Xylene' },
  { value: '95-50-1', label: '1,2-Dichlorobenzene' },
  { value: '95-63-6', label: '1,2,4-Trimethylbenzene' },
  { value: '96-14-0', label: '3-Methylpentane' },
  { value: '96-33-3', label: 'Methyl Acrylate' },
  { value: '96-37-7', label: 'Methylcyclopentane' },
  { value: '96-47-9', label: '2-Methyltetrahydrofuran' },
  { value: '97-62-1', label: 'Ethyl Isobutyrate' },
  { value: '97-63-2', label: 'Ethyl Methacrylate' },
  { value: '97-85-8', label: 'Isobutyl Isobutyrate' },
  { value: '98-00-0', label: 'Furfuryl Alcohol' },
  { value: '98-01-1', label: 'Furfuraldehyde' },
  { value: '98-82-8', label: 'Cumene' },
  { value: '98-83-9', label: 'Methyl Styrene' },
  { value: '98-86-2', label: 'Acetophenone' },
  { value: '99-49-0', label: 'Carvone' },
  { value: '99-87-6', label: 'Cymene' },
  { value: '100-52-7', label: 'Benzaldehyde' },
  { value: '111-30-8', label: 'Glutaradehyde' },
  { value: '123-38-6', label: 'Propionaldehyde' },
  { value: '123-72-8', label: 'Butyraldehyde' },
  { value: '4170-30-3', label: 'Crotonaldehyde' },
  { value: '50-00-0', label: 'Formaldehyde' },
  { value: '643-79-8', label: 'O-Phtalaldehyde' },
  { value: '66-25-1', label: 'Hexaldehyde' },
  { value: '17302-37-3', label: '2,2-dimethyldecane' },
  { value: '1678-91-7', label: 'Ethylcyclohexane' },
  { value: '110-88-3', label: '1,3,5-Trioxane' },
  { value: '556-67-2', label: 'Octamethylcyclotetrasiloxane' },
  { value: '3522-94-9', label: '2,2,5-Trymethylhexane' },
  { value: '75-07-0', label: 'Acetaldehyde' },
  { value: '109-92-2', label: 'Ethylvinylether' },
  { value: '99-85-4', label: 'γ-Terpinene' },
  { value: '565-75-3', label: '2,3,4-Trimethylpentane' },
  { value: '107-01-7', label: '2-butene' },
  { value: '560-21-4', label: '2,3,3-Trimethylpentane' },
  { value: '584-94-1', label: '2,3-Dimethylhexane' },
];
