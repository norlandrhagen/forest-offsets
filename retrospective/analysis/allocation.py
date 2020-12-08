import numpy as np


def calculate_allocation(data, rp=0):
    baseline_carbon = (
        data['baseline']['components']['ifm_1'] + data['baseline']['components']['ifm_3']
    )

    onsite_carbon = (
        data[f'rp[{rp}]']['components']['ifm_1'] + data[f'rp[{rp}]']['components']['ifm_3']
    )
    adjusted_onsite = onsite_carbon * (1 - data[f'rp[{rp}]']['confidence_deduction']).astype(
        float
    ).round(5)

    delta_onsite = adjusted_onsite - baseline_carbon

    baseline_wood_products = (
        data['baseline']['components']['ifm_7'] + data['baseline']['components']['ifm_8']
    )

    actual_wood_products = (
        data[f'rp[{rp}]']['components']['ifm_7'] + data[f'rp[{rp}]']['components']['ifm_8']
    )

    leakage_adjusted_delta_wood_products = (actual_wood_products - baseline_wood_products) * 0.8

    secondary_effects = data[f'rp[{rp}]']['secondary_effects']
    secondary_effects[leakage_adjusted_delta_wood_products > 0] = 0

    calculated_allocation = delta_onsite + leakage_adjusted_delta_wood_products + secondary_effects
    calculated_allocation.name = 'calc_alloc'
    return calculated_allocation