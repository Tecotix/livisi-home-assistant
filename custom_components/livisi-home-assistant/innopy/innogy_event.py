class InnogyEvent():

    def __init__(self, evt):
        self.desc = evt["desc"]
        self.timestamp = evt["timestamp"]
        self.type = evt["type"]


        if "Properties" in evt:
            prop_dict = {}
            for prop in evt["Properties"]:
                if "lastchanged" in prop:
                    prop_dict.update({prop["name"]:{"value":prop["value"], "lastchanged":prop["lastchanged"]}})
                else:
                    prop_dict.update({prop["name"]:{"value":prop["value"]}})

            self.properties_dict = prop_dict
        if "link" in evt:
            self.link_dict = evt["link"]