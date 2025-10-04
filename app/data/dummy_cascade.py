dummy_cascade_data = [
    {
        "id": 1,
        "trigger": "Heavy rain at Whitefield underpass",
        "features": {
            "rain_mm": 45,
            "drain_blockage": 0.8,
            "traffic_flow": 0.6,
            "nearby_construction": 1
        },
        "historical_cascade": [
            {"t_min": 15, "impact": "Waterlogging at underpass", "prob": 0.9},
            {"t_min": 30, "impact": "ORR traffic slowdown", "prob": 0.75},
            {"t_min": 45, "impact": "Public transport delays", "prob": 0.6}
        ]
    },
    {
        "id": 2,
        "trigger": "Multi-vehicle accident at Silk Board",
        "features": {
            "accident_severity": 0.9,
            "lane_blocked": 2,
            "time_of_day_peak": 1,
            "nearby_hospital_capacity": 0.5
        },
        "historical_cascade": [
            {"t_min": 10, "impact": "Immediate lane blockage", "prob": 0.95},
            {"t_min": 25, "impact": "Feeder roads clogged", "prob": 0.85},
            {"t_min": 40, "impact": "Ambulance delay risk", "prob": 0.5}
        ]
    },
    {
        "id": 3,
        "trigger": "Industrial power outage in Electronic City",
        "features": {
            "outage_size": 0.7,
            "factory_dependency": 0.8,
            "public_transport_effect": 0.3
        },
        "historical_cascade": [
            {"t_min": 20, "impact": "Factory halts -> supply chain delay", "prob": 0.8},
            {"t_min": 40, "impact": "Traffic increase due to shift changes", "prob": 0.5}
        ]
    }
]
