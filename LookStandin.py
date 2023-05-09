import os
import re
import pymel.core as pm
from abc import ABC, abstractmethod
from enum import Enum
from common.utils import *


class LookPresentState(Enum):
    NotPlugged = 0,
    AnteriorVersionPlugged = 1,
    AlreadyPlugged = 2


class LookStandin(ABC):
    @staticmethod
    def __get_free_operator_slot(standin):
        index = 0
        while True:
            if pm.getAttr(standin + ".operators[" + str(index) + "]") is None:
                return index
            index += 1

    def __init__(self, standin, standin_name, object_name):
        self.__object_name = object_name
        self._valid = False
        self._standin = standin
        self._standin_name = standin_name
        self._looks = {}

    # Getter of object name
    def get_object_name(self):
        return self.__object_name

    # Getter of standin name
    def get_standin_name(self):
        return self._standin_name

    # Getter ofthe  standin
    def get_standin(self):
        return self._standin

    # Getter of the looks
    def get_looks(self):
        return self._looks

    # Getter of whether the standin object is valid
    def is_valid(self):
        return self._valid

    # Add Looks to the operators
    def add_looks(self, filepath_looks):
        for look_filepath in filepath_looks:
            for look_name, look_data in self._looks.items():
                if look_data[0] == look_filepath:
                    if look_data[1] == LookPresentState.AlreadyPlugged:
                        continue
                    elif look_data[1] == LookPresentState.AnteriorVersionPlugged:
                        include_graph = look_data[2]
                        include_graph.filename.set(look_filepath)
                    else:
                        include_graph = pm.createNode("aiIncludeGraph", n="aiIncludeGraph_" +
                                                                          self.__object_name+"_"+look_name)
                        include_graph.filename.set(look_filepath)
                        include_graph.out >> self._standin.operators[
                            LookStandin.__get_free_operator_slot(self._standin)]
        pm.select(clear=True)

    # Update existent Looks to the operators
    def update_existent_looks(self):
        for look_name, look_data in self._looks.items():
            look_filepath = look_data[0]
            look_state = look_data[1]
            if look_state == LookPresentState.AnteriorVersionPlugged:
                include_graph = look_data[2]
                include_graph.filename.set(look_filepath)
        pm.select(clear=True)

    @abstractmethod
    def retrieve_looks(self, current_project_dir):
        pass

    def _retrieve_looks_aux(self, current_project_dir, folder_sublook, suffix_operator, check_for_override=False):
        # Looks
        looks = {}

        # Looks dir
        looks_main_dir = os.path.join(current_project_dir, "assets", self._standin_name, "publish")

        # Find default look
        look_default = ""
        for f in reversed(os.listdir(looks_main_dir)):
            filepath = os.path.join(looks_main_dir, f).replace("\\", "/")
            match = re.match(r"^" + self._standin_name + suffix_operator + r"\.v[0-9]{3}\.ass$", f)
            if os.path.isfile(filepath) and match:
                look_default = filepath
                break
        # If default is not found then stop the function (valid is False)
        if look_default is None:
            self._valid = False
            return

        # Find sublooks within the look folder
        sublooks_dir = os.path.join(looks_main_dir, folder_sublook)
        if os.path.isdir(sublooks_dir):
            for sublook_dir in os.listdir(sublooks_dir):
                sublook_dir_path = os.path.join(sublooks_dir, sublook_dir).replace("\\", "/")
                if not os.path.isdir(sublook_dir_path):
                    continue
                sublooks = []
                for sublook in os.listdir(sublook_dir_path):
                    if re.match(r"^" + self._standin_name + "_" + sublook_dir + suffix_operator + r"\.v[0-9]{3}\.ass$",
                                sublook):
                        sublooks.append(sublook)

                if len(sublooks) == 0:
                    continue
                sublook_path = os.path.join(sublook_dir_path, sublooks[-1]).replace("\\", "/")
                looks[sublook_dir] = [sublook_path, LookPresentState.NotPlugged, None]

        looks = dict(sorted(looks.items()))

        self._looks["default"] = [look_default, LookPresentState.NotPlugged, None]

        if check_for_override:
            # Find the Override Look
            for f in os.listdir(looks_main_dir):
                filepath = os.path.join(looks_main_dir, f).replace("\\", "/")
                match = re.match(r"^" + self._standin_name + suffix_operator + r"\.ass$", f)
                if os.path.isfile(filepath) and match:
                    self._looks["override"] = [filepath, LookPresentState.NotPlugged, None]
                    break

        for look_name, look_data in looks.items():
            self._looks[look_name] = look_data

        # Determine if the look is used, not used or if a precedent version is used
        plugged_looks = {include_graph.filename.get().replace("\\", "/"): include_graph
                         for include_graph in pm.listConnections(self._standin, type="aiIncludeGraph")}
        suffix_operator_or_override =\
            suffix_operator if not check_for_override else "(?:_override|"+suffix_operator+")"
        for plugged_look_path, plugged_look in plugged_looks.items():
            match = re.match(r"^(.+" + suffix_operator_or_override + r").+$", plugged_look_path)
            if not match: continue
            root_look_path = match.group(1)
            for look_name in self._looks.keys():
                if self._looks[look_name][0] == plugged_look_path:
                    self._looks[look_name][1] = LookPresentState.AlreadyPlugged
                elif self._looks[look_name][0].startswith(root_look_path) and \
                        self._looks[look_name][1] != LookPresentState.AlreadyPlugged:
                    self._looks[look_name][1] = LookPresentState.AnteriorVersionPlugged
                    self._looks[look_name][2] = plugged_look
        self._valid = True


class LookAsset(LookStandin):
    def retrieve_looks(self, current_project_dir):
        self._retrieve_looks_aux(current_project_dir, "look", "_operator", True)


class LookFur(LookStandin):
    def retrieve_looks(self, current_project_dir):
        self._retrieve_looks_aux(current_project_dir, "look_fur", "_fur", False)
