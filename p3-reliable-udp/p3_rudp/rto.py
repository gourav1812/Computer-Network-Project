class AdaptiveRTO:
    def __init__(self, initial=1.0, min_rto=0.05, max_rto=10.0):
        """Initialize RTO parameters and estimators."""
        self.rto = initial
        self.min_rto = min_rto
        self.max_rto = max_rto
        self.srtt = None      # Smoothed Round Trip Time
        self.rttvar = None    # Round Trip Time Variation