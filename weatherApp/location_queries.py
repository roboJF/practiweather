"""Normalize user-entered locations for OpenWeather geocoding."""

US_STATE_CODES = {
    'alabama': 'AL',
    'alaska': 'AK',
    'arizona': 'AZ',
    'arkansas': 'AR',
    'california': 'CA',
    'colorado': 'CO',
    'connecticut': 'CT',
    'delaware': 'DE',
    'district of columbia': 'DC',
    'florida': 'FL',
    'georgia': 'GA',
    'hawaii': 'HI',
    'idaho': 'ID',
    'illinois': 'IL',
    'indiana': 'IN',
    'iowa': 'IA',
    'kansas': 'KS',
    'kentucky': 'KY',
    'louisiana': 'LA',
    'maine': 'ME',
    'maryland': 'MD',
    'massachusetts': 'MA',
    'michigan': 'MI',
    'minnesota': 'MN',
    'mississippi': 'MS',
    'missouri': 'MO',
    'montana': 'MT',
    'nebraska': 'NE',
    'nevada': 'NV',
    'new hampshire': 'NH',
    'new jersey': 'NJ',
    'new mexico': 'NM',
    'new york': 'NY',
    'north carolina': 'NC',
    'north dakota': 'ND',
    'ohio': 'OH',
    'oklahoma': 'OK',
    'oregon': 'OR',
    'pennsylvania': 'PA',
    'rhode island': 'RI',
    'south carolina': 'SC',
    'south dakota': 'SD',
    'tennessee': 'TN',
    'texas': 'TX',
    'utah': 'UT',
    'vermont': 'VT',
    'virginia': 'VA',
    'washington': 'WA',
    'west virginia': 'WV',
    'wisconsin': 'WI',
    'wyoming': 'WY',
}

US_COUNTRY_NAMES = {
    'us',
    'usa',
    'united states',
    'united states of america',
}

STATE_ALIASES = {
    **US_STATE_CODES,
    **{code.casefold(): code for code in US_STATE_CODES.values()},
    'd.c.': 'DC',
}


def normalize_location_query(query):
    """Convert common U.S. location formats to city,state-code,US."""
    query = query.strip()

    if ',' in query:
        return _normalize_comma_separated_query(query)

    folded_query = query.casefold()
    for state_name in sorted(STATE_ALIASES, key=len, reverse=True):
        suffix = f' {state_name}'
        if folded_query.endswith(suffix):
            city = query[:-len(suffix)].strip()
            if city:
                return f'{city},{STATE_ALIASES[state_name]},US'

    return query


def _normalize_comma_separated_query(query):
    parts = [part.strip() for part in query.split(',')]

    if parts[-1].casefold() in US_COUNTRY_NAMES:
        parts[-1] = 'US'

    state_index = -2 if parts[-1] == 'US' and len(parts) >= 2 else -1
    state_code = STATE_ALIASES.get(parts[state_index].casefold())
    if state_code:
        parts[state_index] = state_code
        if state_index == -1:
            parts.append('US')

    return ','.join(parts)
