import math

import geopandas
import pandas as pd
from shapely.geometry import Point

from ..data import cat


def to_geodataframe(
    df: pd.DataFrame, lat_key: str = 'LAT', lon_key: str = 'LON'
) -> geopandas.GeoDataFrame:
    ''' helper function to covert DataFrame to GeoDataFrame '''
    geo_df = geopandas.GeoDataFrame(
        df, crs='epsg:4326', geometry=[Point(xy) for xy in zip(df[lon_key], df[lat_key])]
    )
    return geo_df


def load_fia_common_practice(postal_codes, min_year=2002, max_year=2012, private_only=True):
    if isinstance(postal_codes, str):
        postal_codes = [postal_codes]

    try:
        df = pd.concat(
            [
                load_fia_state_long(
                    postal_code, min_year=min_year, max_year=max_year, private_only=private_only
                )
                for postal_code in postal_codes
            ]
        )
        return df

    except:
        raise


def load_pnw_slag_data(postal_code):
    """PNW states use different allometric equations from the national FIA database.
    This function loads a fresh batch of data for those 4 states.
    In practice, it looks like only AK uses these updated biomass values
    """
    pnw_states = ['ak', 'or', 'ca', 'wa']
    if postal_code not in pnw_states:
        raise NotImplementedError(f"Provide postal code for PNW state: {[x for x in pnw_states]}")

    tree = cat.fia(
        postal_code=postal_code,
        table='tree',
        columns=['CN', 'PLT_CN', 'CONDID', 'CARBON_AG', 'TPA_UNADJ', 'STATUSCD'],
    ).read()
    cond = cat.fia(
        postal_code=postal_code,
        table='cond',
        columns=[
            'CN',
            'PLT_CN',
            'INVYR',
            'COND_STATUS_CD',
            'SLOPE',
            'STDAGE',
            'ASPECT',
            'CONDID',
            'CONDPROP_UNADJ',
            'OWNCD',
            'FORTYPCD',
            'FLDTYPCD',
            'SITECLCD',
        ],
    ).read()
    plot = cat.fia(
        postal_code=postal_code,
        table='plot',
        columns=['CN', 'PLOT_STATUS_CD', 'MEASYEAR', 'LAT', 'LON', 'ECOSUBCD', 'ELEV'],
    ).read()

    regional_biomass = pd.read_csv(
        'https://carbonplan.blob.core.windows.net/carbonplan-data/raw/fia/TREE_REGIONAL_BIOMASS.csv',
        usecols=['TRE_CN', 'STATECD', 'REGIONAL_DRYBIOT'],
    )

    regional_tree = tree.join(
        regional_biomass[['TRE_CN', 'REGIONAL_DRYBIOT']].set_index('TRE_CN'), on=['CN']
    )

    # regional starts as biomass, so just TPADJ and convert to ha; this is solely to align with FIA-long from carbonplan_forest/preprocess/fia
    regional_tree['unadj_reg_biomass_ha'] = (
        regional_tree['REGIONAL_DRYBIOT'] * regional_tree['TPA_UNADJ']
    ) / 892.1791216197013
    biomass_vars = ['unadj_reg_biomass_ha']
    biomass_sums = (
        regional_tree.loc[regional_tree['STATUSCD'] == 1]
        .groupby(['PLT_CN', 'CONDID'])[biomass_vars]
        .sum()
    )

    cond_agg = cond.groupby(['PLT_CN', 'CONDID']).max()

    cond_agg = cond_agg.join(plot[plot['PLOT_STATUS_CD'] != 2].set_index('CN'), on='PLT_CN')

    full = cond_agg.join(biomass_sums)
    full['adj_ag_biomass'] = full['unadj_reg_biomass_ha'] / full['CONDPROP_UNADJ']

    full = full.dropna(subset=['LAT', 'LON'])
    return full.reset_index()


def load_fia_state_long(postal_code, min_year=2002, max_year=10_000, private_only=True):
    '''helper function to pre-process the fia-long table'''
    columns = [
        'adj_ag_biomass',
        'OWNCD',
        'CONDID',
        'STDAGE',
        'MEASYEAR',
        'SITECLCD',
        'FORTYPCD',
        'FLDTYPCD',
        'ECOSUBCD',
        'CONDPROP_UNADJ',
        'COND_STATUS_CD',
        'SLOPE',
        'ASPECT',
        'INVYR',
        'LAT',
        'LON',
        'ELEV',
    ]
    if postal_code == 'ak':
        df = load_pnw_slag_data(postal_code)
        df = df[columns]
    else:
        df = cat.fia_long(postal_code=postal_code, columns=columns).read()
    df = df.dropna(subset=['LAT', 'LON', 'adj_ag_biomass'])
    df = df[
        (df['MEASYEAR'] >= min_year) & (df['MEASYEAR'] <= max_year)
    ]  # CP data only uses 2002-2012; this will just mean we store less on disk

    # 44/12 gets us to CO2.
    # 0.5 gets us from biomass to carbon; see carbonplan_forests for more details
    df['slag_co2e_acre'] = df['adj_ag_biomass'] * (44 / 12) * (1 / 2.47) * 0.5
    df['postal_code'] = postal_code

    if private_only:
        df = df[df['OWNCD'] == 46]

    # add in geometry for later spatial aggregations
    df = to_geodataframe(df)

    return df


def load_fia_tree(postal_code):
    '''helper function to pre-process the fia-tree table'''

    cond_df = cat.fia(
        postal_code=postal_code,
        table='cond',
        columns=['CN', 'PLT_CN', 'CONDID', 'OWNCD', 'FORTYPCD', 'FLDTYPCD'],
    ).read()
    cond_agg = cond_df.groupby(['PLT_CN', 'CONDID']).max()

    plot_df = cat.fia(
        postal_code=postal_code, table='plot', columns=['CN', 'LAT', 'LON', 'ELEV', 'INVYR']
    ).read()

    tree_df = cat.fia(
        postal_code=postal_code,
        table='tree',
        columns=[
            'CN',
            'PLT_CN',
            'TPA_UNADJ',
            'SPCD',
            'STATUSCD',
            'DIA',
            'CARBON_AG',
            'CONDID',
        ],
    ).read()

    tree_df = tree_df[tree_df['STATUSCD'] == 1]  # only looking at live trees
    tree_df['unadj_basal_area'] = math.pi * (tree_df['DIA'] / (2 * 12)) ** 2 * tree_df['TPA_UNADJ']
    tree_df = tree_df.join(plot_df.set_index(['CN']), on='PLT_CN', how='inner')
    tree_df = tree_df.join(cond_agg, rsuffix='_cond', on=['PLT_CN', 'CONDID'])
    tree_df = to_geodataframe(tree_df)

    return tree_df
