class AdaptiveRTO:
    def __init__(self, initial=1.0, min_rto=0.05, max_rto=10.0):
        """Initialize RTO parameters and estimators."""
        self.rto = initial
        self.min_rto = min_rto
        self.max_rto = max_rto
        self.srtt = None      # Smoothed Round Trip Time
        self.rttvar = None    # Round Trip Time Variation

    def sample(self, rtt: float) -> None:
     """Jacobson/Karels algorithm (RFC 6298): alpha = 1/8, beta = 1/4."""
     if self.srtt is None:
        # First RTT measurement baseline
        self.srtt = rtt
        self.rttvar = rtt / 2.0    