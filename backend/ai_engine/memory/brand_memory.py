class BrandMemory:

    def __init__(self, brand_name, tone):
        self.brand_name = brand_name
        self.tone = tone

    def get_brand_context(self):

        return f"""
        Brand: {self.brand_name}
        Tone: {self.tone}
        Respond consistently with this voice.
        """
