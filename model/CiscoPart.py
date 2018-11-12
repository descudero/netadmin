from functools import cmp_to_key
from multireplace import  multi_replace_void

class CiscoPart(object):
    PART_DESIGN={"ASR-9010-DC-V2":{
        "color":"blue"
    },"ASR-9910":{
        "color":"#85adad"
    },"A9K-MOD160-TR":
        {"color":"red",
         "witdth":260,
        "height":40},
     "A9K-MPA-8X10GE":
    {"color": "magenta",
     "witdth": 120,
     "height": 30},
    "A9K-MPA-8X2GE":
        {"color": "cyan",
             "witdth": 120,
             "height": 30}
   }





    SLOT_COUNT_PART={
                        "ASR-9010-DC-V2":10,
                        "A9K-MPA-8X10GE":8,
                        "A9K-MOD160-TR":2,
                        "A9K-MOD200-TR":2
                     }
    SLOT_USAGE_PART={"A9K-MPA-8X10GE":(1,1),
                     "A9K-MOD160-TR": (1,1),
                     "A99-RSP-TR":(1,1),
                     "A9K-RSP440-TR":(1,1),
                     "A9K-RSP880-TR": (1,1),
                     "A9K-MOD200-TR": (1,1),
                     "A99-SFC-S":(1,0),
                     "A9K-MPA-1X100GE":(1,1),




    }

    WIDTH=204
    PADDING=4
    SLOT_HEIGHT=30

    def __init__(self, parent_device, name, serial_number, vid, pid, local_name):
        self.parent_device = parent_device
        self.name = name
        self.serial_number = serial_number
        self.vid = vid
        self.pid = pid
        self.local_name = local_name
        self.part_level = local_name.count("/")
        self.type="OTHER"
        self.side = 0
        if (self.local_name.find("fan") > -1 or self.local_name.find("power") > -1):
            self.part_level = 1
            self.side =1

        self.children = {}
        self.calculate_slots()



    def calculate_slots(self):
        self.slots=0
        self.slot_number=0
        if self.local_name.find("RSP") > -1:
            self.type = "RSP"
            self.slots = 0
            self.slot_number= int(multi_replace_void(self.local_name,["0/","RSP"]))+8
        if self.local_name.find("chassis")>-1:
            self.type = "CHASSIS"
            self.slots=int(multi_replace_void(self.pid,{"ASR","99","DC","V2","-","90"}))
            self.slot_number=0

        if(self.pid.find("SFP")>-1 or self.pid.find("XFP")>-1):
            self.slots=0
            self.type = "SFP"
            self.slot_number = int(self.local_name[-1])

        if(self.pid.find("MOD")>-1):
            self.slots = 2
            self.type = "MOD"
            self.slot_number = int(self.local_name[-1])
        if (self.pid.find("MPA") > -1):
            self.type = "MPA"
            self.slots=int(self.pid.split("X")[0].split("-")[-1])
            self.slot_number = int(self.local_name[-1])

    def print_children(self, recursive=True):
        for id, child in self.children.items():
            print("\t" * (self.part_level+1) + str(child))
            if recursive:
                child.print_children(recursive)

    def is_parent(self, part):

        if self.part_level == part.part_level - 1 and self.is_related(part):
            return True
        return False

    def add_child(self, part):
        if (self.is_parent(part)):
            part.parent = self
            self.children[part.local_name] = part
            part.parent = self
            return True
        else:
            return_value = False
            for name, child in self.children.items():

                if (child.is_related(part)):
                    return_value = child.add_child(part)

            return return_value

    def is_related(self, children):

        if(self.type=="CHASSIS"):
            return True
        else:
            if children.local_name.startswith(self.local_name):
                return True
            else:
                return False


    def get_slot_number(self):

        pass

    def get_children_number(self):
        return len(self.children)


    def set_dimension(self,x_parent=0,y_parent=0):

        if(self.type=="CHASSIS"):
            self.height= (CiscoPart.SLOT_HEIGHT + CiscoPart.PADDING*2)*self.slots
            self.width=(CiscoPart.WIDTH)
            self.initial_x = x_parent
            self.initial_y = y_parent


        if (self.type == "MOD" or self.type =="RSP"):
            self.height = (CiscoPart.SLOT_HEIGHT)
            self.width = int((CiscoPart.WIDTH-CiscoPart.PADDING*2))
            self.initial_x = self.parent.initial_x+CiscoPart.PADDING
            self.initial_y = self.parent.initial_y+CiscoPart.PADDING + (CiscoPart.PADDING*2+CiscoPart.SLOT_HEIGHT)*self.slot_number

        if (self.type == "MPA" or self.type == "SFP"):
            self.width=int(self.parent.width/self.parent.slots-CiscoPart.PADDING)
            self.height = (CiscoPart.SLOT_HEIGHT-(self.part_level-1)*CiscoPart.PADDING*2)
            self.initial_x = self.parent.initial_x +\
                             CiscoPart.PADDING+(self.width+CiscoPart.PADDING)*self.slot_number
            self.initial_y= self.parent.initial_y+CiscoPart.PADDING


        self.final_x = self.initial_x + self.width
        self.final_y = self.initial_y + self.height




    def get_color(self):
        if(self.pid.find("ER")>-1):
            return "#14e870"
        if (self.pid.find("LR") > -1):
            return "#0991e5"
        if (self.pid.find("ZR") > -1):
            return "#03b775"
        if (self.pid.find("MPA-8X10") > -1):
            return "#bc8b27"
        if (self.pid.find("MPA-2X10") > -1):
            return "#e53808"
        if (self.pid.find("440") > -1):
            return "#174084"
        if (self.pid.find("880") > -1):
            return "#351b47"
        if (self.pid.find("MOD160") > -1):
            return "#33471b"
        if (self.pid.find("MOD200") > -1):
            return "#879e2f"

        return "gray"
    def draw_in_canvas(self,canvas,x=0,y=0,side=0,recursive=True):
        if(self.side==side):
            self.set_dimension(x,y)
            canvas.create_rectangle(self.initial_x, self.initial_y, self.final_x, self.final_y, fill=self.get_color())
            if(recursive):
                for name,child in self.children.items():
                    child.draw_in_canvas(canvas,x=0,y=0,side=side,recursive=recursive)

    def get_slots_used(self,side=0):
        counter=0
        for id, child in self.children.items():
            if child.side==side:
                counter+=1
        return counter

    def get_slots_empty(self,side=0):
        return self.slots- self.get_slots_used(side=side)


    def get_slots_summary(self,side=0):

        output_string=str(self)+" SLOTS:"+str(self.slots)+" USED:"+str(self.get_slots_used(side))\
        +" EMPTY:"+str(self.get_slots_empty(side))+"\n"
        for id, child in self.children.items():
            if(child.side==side and child.slots>0):
                output_string+=child.get_slots_summary(side)
        return output_string

    @staticmethod
    def create_inventory_tree(device, inventory):
        parts = []
        for inventory_part in inventory:
            part = CiscoPart(
                parent_device=device,
                name=inventory_part["description"],
                serial_number=inventory_part["SN"],
                vid=inventory_part["VID"],
                pid=inventory_part["PID"],
                local_name=inventory_part["local_name"])
            if part.part_level == 0:
                device.chassis = part
            else:
                parts.append(part)
        parts.sort(key=lambda x: x.part_level, reverse=False)
        while len(parts) != 0:
            part = parts.pop()
            if not device.chassis.add_child(part):
                parts.insert(0, part)

    def __str__(self):
        return self.local_name + " " + self.pid + " S:"+str(self.slots) +  " N: "+str(self.slot_number)
