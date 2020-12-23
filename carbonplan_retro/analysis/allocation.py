import pandas as pd


def calculate_allocation(
    data: pd.DataFrame, rp: int = 1, round_intermediates: bool = False
) -> pd.Series:
    """Calculate the allocation of ARBOCs based on project report IFM components

    Parameters
    ----------
    data : pd.DataFrame
        Project database
    rp : int
        Reporting period
    round_intermediates : bool
        If true, round intermeiate calculations before calculating the final allocation

    Returns
    -------
    allocation : pd.Series
    """

    baseline_carbon = (
        data['baseline']['components']['ifm_1'] + data['baseline']['components']['ifm_3']
    )

    onsite_carbon = (
        data[f'rp_{rp}']['components']['ifm_1'] + data[f'rp_{rp}']['components']['ifm_3']
    )
    adjusted_onsite = onsite_carbon * (1 - data[f'rp_{rp}']['confidence_deduction']).astype(
        float
    ).round(5)
    if round_intermediates:
        adjusted_onsite = adjusted_onsite.round()

    delta_onsite = adjusted_onsite - baseline_carbon

    baseline_wood_products = (
        data['baseline']['components']['ifm_7'] + data['baseline']['components']['ifm_8']
    )

    actual_wood_products = (
        data[f'rp_{rp}']['components']['ifm_7'] + data[f'rp_{rp}']['components']['ifm_8']
    )

    leakage_adjusted_delta_wood_products = (actual_wood_products - baseline_wood_products) * 0.8

    secondary_effects = data[f'rp_{rp}']['secondary_effects']
    secondary_effects[secondary_effects > 0] = 0  # Never allowed to have positive SE.

    if round_intermediates:
        leakage_adjusted_delta_wood_products = leakage_adjusted_delta_wood_products.round()

    calculated_allocation = delta_onsite + leakage_adjusted_delta_wood_products + secondary_effects
    calculated_allocation.name = 'opdr_calculated'
    return calculated_allocation
