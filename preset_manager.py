import bpy
import json
import pathlib
import os 

path_presets = str(os.path.dirname(os.path.realpath(__file__))) + "\\ATS_PRESETS\\" + "PRESETS.json"
print(path_presets)

class PresetManager:
    def __init__(self):
#        self.DEFAULT_PRESETS = [
#            {
#                "name" : "Head",
#    
#                "X" : "Y",
#                "Xinverted" : False,
#                "Xlocked" : False,
#    
#                "Y" : "X",
#                "Yinverted" : False,
#                "Ylocked" : False,
#    
#                "Z" : "Z",
#                "Zinverted" : True,
#                "Zlocked" : False
#            }
#        ]
    
        self.PRESETS = []


    def load_user_presets(self):
        global path_presets
        ### Load User Saved Presets
        with open(path_presets) as json_presets:
            data = json.load(json_presets)
            for dict_preset in data:
                self.PRESETS.append(dict_preset)

        return self.PRESETS


    def remove_preset(self, name : str):
        ### Load User Saved Presets
        for dict_preset in self.PRESETS:
            if dict_preset['name'] == name:
                self.PRESETS.remove(dict_preset)

        self.save_presets()

        return self.PRESETS

    def add_preset(self, new_data : dict):
        ### Load User Saved Presets
        need_new = True
        for dict_preset in self.PRESETS:
            if dict_preset['name'] == new_data['name']:
                need_new = False
                dict_preset['X'] = new_data['X']
                dict_preset['Xinverted'] = new_data['Xinverted']
                dict_preset['Xlocked'] = new_data['Xlocked']

                dict_preset['Y'] = new_data['Y']
                dict_preset['Yinverted'] = new_data['Yinverted']
                dict_preset['Ylocked'] = new_data['Ylocked']

                dict_preset['Z'] = new_data['Z']
                dict_preset['Zinverted'] = new_data['Zinverted']
                dict_preset['Zlocked'] = new_data['Zlocked']

                break

        if need_new:
            self.PRESETS.append(dict_preset)

        self.save_presets()

        return self.PRESETS

    def save_presets(self):
        ### Load User Saved Presets
        with open(path_presets, 'w') as outfile:
            json.dump(self.PRESETS, outfile)


    def get_enums(self):
        enum = [("None", "None", "None")]

        for p in self.PRESETS:
            enum.append((p['name'], p['name'], p['name'] + " Preset"))

        return enum

    def get_preset_name(self, name : str):
        for p in self.PRESETS:
            if p['name'] == name:
                return p
            
        return None
