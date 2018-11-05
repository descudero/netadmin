class RoutePolicy(object):
    def __init__(self, name, parent):
        self.name = name
        self.sequences = []
        self.parent = parent

    def setSequence(self, condition, action):
        condition2 = condition.replace("(", "").replace(")", "").replace("destination in", "")
        conditions = condition2.split("and")
        prefixes = {}
        for condition in conditions:
            condition = condition.replace(" ", "")
            if condition in self.parent.prefix_sets:
                prefixes[condition] = self.parent.prefix_sets[condition]
        self.sequences.append({"condition": prefixes, "action": action})

    def listSequence(self):
        listado = "";

        for sequence in self.sequences:
            listado = listado + " CON " + sequence["condition"] + " ACT " + sequence["action"] + "\n"

        return listado

    def hasApply(self):
        flag = False;
        for sequence in self.sequences:
            if (sequence["action"].find("apply") != -1):
                return sequence["action"].replace("apply", "").replace(" ", "")
        return False

    def filterAction(self, listActions):
        returnSequences = []
        for sequence in self.sequences:
            for action in listActions:
                if (sequence["action"].find(action) != -1):
                    returnSequences.append(sequence)

        return returnSequences

    def ipInSequence(self, ip, filter=["pass"]):

        sequences = self.filterAction(filter)
        prefixsets = {}
        for sequence in sequences:
            # print(sequence)
            for prefix in sequence["condition"].items():

                if (prefix[1].ipInPrefixSet(ip)):
                    prefixsets[prefix[1].name] = prefix
        return prefixsets

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name
