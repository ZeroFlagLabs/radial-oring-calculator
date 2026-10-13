"""Explicit sample inputs for legacy GUI tests (production starts at zero)."""
SAMPLE = {'spin_male_cylinder_id_nom': 0.75, 'spin_male_cylinder_id_tol': 0.001, 'spin_male_direct_rod_od_nom': 0.748, 'spin_male_direct_rod_od_tol': 0.001, 'spin_male_rod_od_nom': 0.748, 'spin_male_rod_od_tol': 0.001, 'spin_female_direct_cylinder_id_nom': 0.577, 'spin_female_direct_cylinder_id_tol': 0.0005, 'spin_female_cylinder_id_nom': 0.577, 'spin_female_cylinder_id_tol': 0.0005, 'spin_female_rod_od_nom': 0.575, 'spin_female_rod_od_tol': 0.001, 'spin_shared_width_nom': 0.145, 'spin_shared_width_tol': 0.003, 'spin_shared_radius_nom': 0.0, 'spin_shared_radius_tol': 0.0, 'spin_shared_entrance_radius_nom': 0.0, 'spin_shared_entrance_radius_tol': 0.0, 'spin_shared_rect_angle_nom': 0.0, 'spin_shared_rect_angle_tol': 0.0, 'spin_shared_angle_nom': 24.0, 'spin_shared_angle_tol': 0.5, 'spin_male_gland_od_nom': 0.584, 'spin_male_gland_od_tol': 0.001, 'spin_male_groove_depth_nom': 0.082, 'spin_male_groove_depth_tol': 0.001, 'spin_female_gland_id_nom': 0.741, 'spin_female_gland_id_tol': 0.001, 'spin_female_groove_depth_nom': 0.082, 'spin_female_groove_depth_tol': 0.00025, 'spin_male_ring_id_nom': 0.565, 'spin_male_ring_id_tol': 0.005, 'spin_male_section_nom': 0.103, 'spin_male_section_tol': 0.003}


def seed_sample(window):
    """Populate the former v0.9.7 demo dimensions for tests expecting results."""
    for rows, group in ((window.rows, 'male'), (window.female_rows, 'female'),
                        (window.shared_rows, 'shared')):
        for key, row in rows.items():
            row.nominal.setValue(SAMPLE[f'spin_{group}_{key}_nom'])
            row.tolerance.setValue(SAMPLE[f'spin_{group}_{key}_tol'])
    window._recalculate()
