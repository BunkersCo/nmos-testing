# Copyright (C) 2019 Advanced Media Workflow Association
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from ...GenericTest import NMOSTestException
from ...IS05Utils import IMMEDIATE_ACTIVATION
from .calls import Call
from .testConfig import globalConfig
import re


class Activation:

    def __init__(self):
        self.test = globalConfig.test
        self.urlBase = globalConfig.apiUrl
        self.type = IMMEDIATE_ACTIVATION
        self.activationTimestamp = "0:0"
        self.actionList = []
        self.activationID = None
        self._callInstance = Call(self.urlBase + "map/activations")

    def addAction(self, action):
        self.actionList.append(action)

    def addActions(self, actions):
        for action in actions:
            self.addAction(action)

    def getActions(self):
        return self.actionList

    def _activationObject(self):
        activationObject = {
            "mode": self.type
        }
        if self.type != IMMEDIATE_ACTIVATION:
            activationObject['requested_time'] = self.activationTimestamp
        return activationObject

    def _actionObject(self):
        actionObject = {}
        for action in self.actionList:
            if action.outputID not in actionObject:
                actionObject[action.outputID] = action.channelJSON()
            else:
                actionObject[action.outputID].update(action.channelJSON())
        return actionObject

    def _buildPOSTObject(self):
        postObject = {
            'activation': self._activationObject(),
            'action': self._actionObject()
        }
        return postObject

    def _setExpectedResponseCode(self):
        if self.type == IMMEDIATE_ACTIVATION:
            self._callInstance.expectedCode = 200
        else:
            self._callInstance.expectedCode = 202

    def _getActivationIDFromActivationResponse(self, activationResponse):
        try:
            activationID = list(activationResponse)[0]
        except IndexError:
            res = self.test.FAIL("Could not find activation ID in activation response")
            raise NMOSTestException(res)
        self._checkActivationID(activationID)
        self.activationID = activationID

    def _checkActivationID(self, activationID):
        if re.match("^[a-zA-Z0-9\\-_]+$", activationID) is None:
            res = self.test.FAIL("Activation ID {} did not match "
                                 "required regex".format(activationID))
            raise NMOSTestException(res)

    def fireActivation(self):
        postObject = self._buildPOSTObject()
        self._setExpectedResponseCode()
        self._callInstance.responseSchema = globalConfig.testSuite.get_schema(
            globalConfig.apiKey, "POST", "/map/activations", 200
        )
        activationResponse = self._callInstance.post(postObject)
        self._getActivationIDFromActivationResponse(activationResponse)
        return self.activationID

    def delete(self):
        url = self.urlBase + "map/activations/{}".format(self.activationID)
        deleteCall = Call(url)
        deleteCall.expectedCode = 204
        deleteCall.delete()
        deleteCall.expectedCode = 404
        try:
            deleteCall.get()
        except NMOSTestException:
            msg = "Activation still present at {} after deletion".format(url)
            raise NMOSTestException(self.test.FAIL(msg))

    def checkLock(self):
        postObject = self._buildPOSTObject()
        self._callInstance.expectedCode = 423
        self._callInstance.post(postObject)

    def checkReject(self):
        postObject = self._buildPOSTObject()
        self._callInstance.expectedCode = 400
        self._callInstance.responseSchema = globalConfig.testSuite.get_schema(
            globalConfig.apiKey, "POST", "/map/activations", 400
        )
        self._callInstance.post(postObject)
